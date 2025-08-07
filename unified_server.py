#!/usr/bin/env python3
"""Unified HTTP server supporting both MCP and A2A protocols."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import A2A types for proper validation
try:
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities
    A2A_TYPES_AVAILABLE = True
except ImportError:
    A2A_TYPES_AVAILABLE = False

from schemas import (
    GetSignalsRequest, GetSignalsResponse,
    ActivateSignalRequest, ActivateSignalResponse
)
from database import init_db
from config_loader import load_config
from adapters.manager import AdapterManager

# Import the MCP tools
import main

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Signals Agent Unified Server",
    description="Supports both MCP and A2A protocols",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in production, adjust as needed
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# ===== Shared Business Logic =====

def get_business_logic():
    """Get initialized business logic components."""
    config = load_config()
    adapter_manager = AdapterManager(config)
    return config, adapter_manager


# ===== A2A Protocol Endpoints =====

@app.get("/agent-card")
async def get_agent_card(request: Request):
    """Return the A2A Agent Card compliant with the official spec."""
    # Build base URL dynamically
    base_url = str(request.base_url).rstrip('/')
    
    # Build the agent card following A2A spec
    agent_card = {
        # Note: 'agentId' is not in the official spec - the field is just 'name'
        "name": "Signals Activation Agent", 
        "description": "AI agent for discovering and activating audience signals",
        "version": "1.0.0",
        "url": base_url,  # Dynamic URL based on request
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "capabilities": {  # Required by spec
            "streaming": False,
            "batchProcessing": False,
            "concurrentTasks": True
        },
        "skills": [
            {
                "id": "discovery",
                "name": "Signal Discovery",
                "description": "Discover audience signals using natural language",
                "tags": ["search", "discovery", "audience", "signals"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query for signal discovery"
                        },
                        "deliver_to": {
                            "type": "object",
                            "description": "Delivery specification"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        },
                        "principal_id": {
                            "type": "string",
                            "description": "Principal identifier for access control"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "id": "activation",
                "name": "Signal Activation",
                "description": "Activate a signal on a platform",
                "tags": ["activation", "deployment", "platform", "signals"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "signal_id": {
                            "type": "string",
                            "description": "ID of the signal to activate"
                        },
                        "platform": {
                            "type": "string",
                            "description": "Target platform for activation"
                        },
                        "account": {
                            "type": "string",
                            "description": "Platform account identifier"
                        },
                        "context_id": {
                            "type": "string",
                            "description": "Context ID from discovery"
                        }
                    },
                    "required": ["signal_id", "platform"]
                }
            }
        ]
    }
    
    # Add optional fields that help with discovery
    agent_card["protocolVersion"] = "0.2"  # A2A protocol version
    agent_card["provider"] = {
        "name": "Signals Agent",
        "url": base_url
    }
    
    # If we have the official types, validate the card
    if A2A_TYPES_AVAILABLE:
        try:
            # Validate using official AgentCard type
            validated = AgentCard(**agent_card)
            return validated.model_dump(exclude_none=True)
        except Exception as e:
            logger.warning(f"Agent card validation failed: {e}")
            # Return unvalidated card if validation fails
    
    return agent_card


@app.post("/a2a/task")
async def handle_a2a_task(request: Dict[str, Any]):
    """Handle A2A task requests following the official spec."""
    # Extract task metadata
    task_id = request.get("taskId") or f"task_{datetime.now().timestamp()}"
    task_type = request.get("type")
    context_id = request.get("contextId")
    
    # Handle both standard A2A format (with parameters) and simplified format
    if "parameters" in request:
        params = request.get("parameters", {})
    else:
        # For simplified format, treat the whole request as parameters
        params = {k: v for k, v in request.items() if k not in ["taskId", "type", "contextId"]}
    
    try:
        if task_type == "discovery":
            # Convert to internal format
            # Support 'query' at root level or in parameters
            query = params.get("query", request.get("query", ""))
            
            internal_request = GetSignalsRequest(
                signal_spec=query,
                deliver_to=params.get("deliver_to", {"platforms": "all", "countries": ["US"]}),
                filters=params.get("filters"),
                max_results=params.get("max_results", 10),
                principal_id=params.get("principal_id")
            )
            
            # Call business logic
            response = main.get_signals.fn(
                signal_spec=internal_request.signal_spec,
                deliver_to=internal_request.deliver_to,
                filters=internal_request.filters,
                max_results=internal_request.max_results,
                principal_id=internal_request.principal_id
            )
            
            # Build A2A-compliant response
            task_response = {
                "id": task_id,  # Changed from taskId to id per spec
                "kind": "task",  # Added required field
                "status": "Completed",  # Capital C per spec enum
                "contextId": context_id or response.context_id,
                "completedAt": datetime.now().isoformat(),
                "output": {  # Changed from parts to output per spec
                    "parts": [{
                        "contentType": "application/json",
                        "content": response.model_dump()
                    }]
                }
            }
            
            # Add optional metadata
            if response.signals:
                task_response["metadata"] = {
                    "signal_count": len(response.signals),
                    "context_id": response.context_id
                }
            
            return task_response
            
        elif task_type == "activation":
            # Convert to internal format
            internal_request = ActivateSignalRequest(
                signals_agent_segment_id=params.get("signal_id", ""),
                platform=params.get("platform", ""),
                account=params.get("account"),
                context_id=params.get("context_id") or context_id
            )
            
            # Call business logic
            response = main.activate_signal.fn(
                signals_agent_segment_id=internal_request.signals_agent_segment_id,
                platform=internal_request.platform,
                account=internal_request.account,
                context_id=internal_request.context_id
            )
            
            # Build A2A-compliant response
            task_status = "Completed" if response.status == "deployed" else "InProgress"
            task_response = {
                "id": task_id,
                "kind": "task",
                "status": task_status,  # Using proper A2A status enum
                "contextId": context_id or response.context_id,
                "output": {
                    "parts": [{
                        "contentType": "application/json",
                        "content": response.model_dump()
                    }]
                }
            }
            
            if task_status == "Completed":
                task_response["completedAt"] = datetime.now().isoformat()
            
            # Add optional metadata
            task_response["metadata"] = {
                "activation_status": response.status,
                "platform": internal_request.platform
            }
            
            return task_response
            
        else:
            raise HTTPException(400, f"Unknown task type: {task_type}")
            
    except Exception as e:
        logger.error(f"Task failed: {e}")
        # Return A2A-compliant error response
        return {
            "id": task_id,
            "kind": "task",
            "status": "Failed",  # Proper A2A status
            "contextId": context_id,
            "error": {
                "code": "TASK_EXECUTION_ERROR",
                "message": str(e)
            },
            "output": {
                "parts": [{
                    "contentType": "text/plain",
                    "content": str(e)
                }]
            }
        }


# ===== MCP Protocol Endpoints =====

@app.get("/mcp")
@app.get("/mcp/")
async def mcp_discovery():
    """Return MCP server information for discovery."""
    return {
        "mcp_version": "1.0",
        "server_name": "audience-agent",
        "server_version": "1.0.0",
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        }
    }

@app.post("/mcp")
@app.post("/mcp/")
async def handle_mcp_request(request: Request):
    """Handle MCP JSON-RPC requests over HTTP."""
    try:
        # Get JSON-RPC request
        json_rpc = await request.json()
        
        method = json_rpc.get("method")
        params = json_rpc.get("params", {})
        request_id = json_rpc.get("id")
        
        # Route to appropriate handler
        if method == "initialize":
            # Handle MCP initialization
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "audience-agent",
                    "version": "1.0.0"
                }
            }
            
        elif method == "tools/list":
            # Return available tools
            result = {
                "tools": [
                    {
                        "name": "get_signals",
                        "description": "Discover relevant signals",
                        "inputSchema": main.get_signals.parameters
                    },
                    {
                        "name": "activate_signal", 
                        "description": "Activate a signal",
                        "inputSchema": main.activate_signal.parameters
                    }
                ]
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_params = params.get("arguments", {})
            
            if tool_name == "get_signals":
                # Convert deliver_to dict to proper object
                from schemas import DeliverySpecification
                if 'deliver_to' in tool_params and isinstance(tool_params['deliver_to'], dict):
                    tool_params['deliver_to'] = DeliverySpecification(**tool_params['deliver_to'])
                
                result = main.get_signals.fn(**tool_params)
            elif tool_name == "activate_signal":
                result = main.activate_signal.fn(**tool_params)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
            # Convert response to dict
            result = result.model_dump() if hasattr(result, 'model_dump') else result
            
        else:
            raise ValueError(f"Unknown method: {method}")
            
        # Return JSON-RPC response
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        })
        
    except Exception as e:
        logger.error(f"MCP request failed: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            },
            "id": request_id if 'request_id' in locals() else None
        })


@app.get("/mcp/sse")
async def mcp_sse_endpoint():
    """MCP Server-Sent Events endpoint for streaming."""
    async def event_generator():
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield f": keepalive\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ===== Health Check =====

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "protocols": ["mcp", "a2a"],
        "timestamp": datetime.now().isoformat()
    }


# ===== Main =====

def run_unified_server(host: str = "localhost", port: int = 8000):
    """Run the unified server supporting both protocols."""
    logger.info(f"Starting Unified Server on {host}:{port}")
    logger.info(f"- A2A Agent Card: http://{host}:{port}/agent-card")
    logger.info(f"- A2A Tasks: http://{host}:{port}/a2a/task")
    logger.info(f"- MCP Endpoint: http://{host}:{port}/mcp")
    logger.info(f"- MCP SSE: http://{host}:{port}/mcp/sse")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    run_unified_server()