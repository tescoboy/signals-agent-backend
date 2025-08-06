#!/usr/bin/env python3
"""Unified HTTP server supporting both MCP and A2A protocols."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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
async def get_agent_card():
    """Return the A2A Agent Card."""
    return {
        "agentId": "signals-activation-agent",
        "name": "Signals Activation Agent", 
        "description": "AI agent for discovering and activating audience signals",
        "version": "1.0.0",
        "capabilities": {
            "discovery": {
                "description": "Discover audience signals using natural language",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "deliver_to": {"type": "object"},
                        "max_results": {"type": "integer"},
                        "principal_id": {"type": "string"}
                    },
                    "required": ["query"]
                }
            },
            "activation": {
                "description": "Activate a signal on a platform",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "signal_id": {"type": "string"},
                        "platform": {"type": "string"},
                        "account": {"type": "string"},
                        "context_id": {"type": "string"}
                    },
                    "required": ["signal_id", "platform"]
                }
            }
        },
        "protocols": ["a2a", "mcp"],
        "endpoints": {
            "a2a": "http://localhost:8000/a2a/task",
            "mcp": "http://localhost:8000/mcp"
        }
    }


@app.post("/a2a/task")
async def handle_a2a_task(request: Dict[str, Any]):
    """Handle A2A task requests."""
    task_id = request.get("taskId")
    task_type = request.get("type")
    params = request.get("parameters", {})
    
    try:
        if task_type == "discovery":
            # Convert to internal format
            internal_request = GetSignalsRequest(
                signal_spec=params.get("query", ""),
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
            
            # Convert to A2A format
            return {
                "taskId": task_id,
                "status": "completed",
                "completedAt": datetime.now().isoformat(),
                "parts": [{
                    "contentType": "application/json",
                    "content": response.model_dump()
                }],
                "artifact": {
                    "type": "discovery_results",
                    "context_id": response.context_id,
                    "signal_count": len(response.signals)
                }
            }
            
        elif task_type == "activation":
            # Convert to internal format
            internal_request = ActivateSignalRequest(
                signals_agent_segment_id=params.get("signal_id", ""),
                platform=params.get("platform", ""),
                account=params.get("account"),
                context_id=params.get("context_id")
            )
            
            # Call business logic
            response = main.activate_signal.fn(
                signals_agent_segment_id=internal_request.signals_agent_segment_id,
                platform=internal_request.platform,
                account=internal_request.account,
                context_id=internal_request.context_id
            )
            
            # Convert to A2A format
            status = "completed" if response.status == "deployed" else "in_progress"
            return {
                "taskId": task_id,
                "status": status,
                "completedAt": datetime.now().isoformat() if status == "completed" else None,
                "parts": [{
                    "contentType": "application/json",
                    "content": response.model_dump()
                }],
                "artifact": {
                    "type": "activation_result",
                    "context_id": response.context_id,
                    "status": response.status
                }
            }
            
        else:
            raise HTTPException(400, f"Unknown task type: {task_type}")
            
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return {
            "taskId": task_id,
            "status": "failed",
            "parts": [{
                "contentType": "text/plain",
                "content": str(e)
            }]
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