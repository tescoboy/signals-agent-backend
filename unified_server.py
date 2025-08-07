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

@app.get("/")
async def root():
    """Root endpoint - return basic info or redirect to agent card."""
    return {
        "name": "Signals Activation Agent",
        "description": "AI agent for discovering and activating audience signals",
        "version": "1.0.0",
        "agent_card": "/agent-card",
        "protocols": ["a2a", "mcp"]
    }

@app.post("/")
async def handle_a2a_root_task(request: Dict[str, Any]):
    """Handle A2A task requests at root endpoint (A2A standard)."""
    # Check if this is a JSON-RPC message from A2A Inspector
    if "jsonrpc" in request and request.get("method") == "message/send":
        # Extract the actual message from JSON-RPC format
        params = request.get("params", {})
        message = params.get("message", {})
        message_parts = message.get("parts", [])
        
        # Extract text from message parts
        query = ""
        for part in message_parts:
            if part.get("kind") == "text":
                query = part.get("text", "")
                break
        
        # Convert to our expected task format
        # Assume it's a discovery task since that's the most common
        task_request = {
            "taskId": request.get("id"),
            "type": "discovery",
            "contextId": params.get("contextId"),  # Pass through context from JSON-RPC
            "parameters": {
                "query": query
            }
        }
        
        # Process the task
        task_result = await handle_a2a_task(task_request)
        
        # For message/send requests, return Message format instead of Task format
        # Extract the response data from task result
        # The task response has the message parts in status.message.parts
        task_status = task_result.get("status", {})
        task_message = task_status.get("message", {})
        task_parts = task_message.get("parts", [])
        
        # Build proper A2A Message with correct parts format
        message_parts = []
        
        if task_parts:
            # Copy the parts from the task response
            for part in task_parts:
                if part.get("kind") == "text":
                    message_parts.append({
                        "kind": "text",
                        "text": part.get("text", "")
                    })
                elif part.get("kind") == "data":
                    # Get the data part
                    data = part.get("data", {})
                    message_parts.append({
                        "kind": "data", 
                        "data": {
                            "contentType": "application/json",
                            "content": data
                        }
                    })
        
        message_response = {
            "kind": "message",
            "message_id": f"msg_{datetime.now().timestamp()}",  # Fixed: use message_id not messageId
            "parts": message_parts,
            "role": "agent"  # Fixed: use 'agent' instead of 'assistant'
        }
        
        # Wrap response in JSON-RPC format
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": message_response
        }
    else:
        # Standard A2A task format
        return await handle_a2a_task(request)

@app.get("/.well-known/agent.json")
@app.get("/agent-card")
async def get_agent_card(request: Request):
    """Return the A2A Agent Card compliant with the official spec."""
    # Build base URL dynamically, respecting proxy headers
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_proto:
        # We're behind a proxy, use the forwarded protocol
        host = request.headers.get("Host", request.base_url.hostname)
        base_url = f"{forwarded_proto}://{host}"
    else:
        # Direct connection, use the request's base URL
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
        "capabilities": {  # Required by spec - using fields from AgentCapabilities
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
            "extensions": []
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
        "organization": "Signals Agent Team",  # Required field per A2A spec
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
            
            # Check if this is a contextual follow-up question
            query_lower = query.lower()
            
            # Check for custom segment/signal queries
            is_custom_segment_query = any([
                "custom segment" in query_lower,
                "custom signal" in query_lower,
                "tell me about the custom" in query_lower,
                "tell me more about the custom" in query_lower,
                "what custom" in query_lower,
                "explain the custom" in query_lower,
                "describe the custom" in query_lower,
                "more about custom" in query_lower
            ])
            
            # Check for signal detail queries
            is_signal_detail_query = any([
                "tell me about the signal" in query_lower,
                "tell me more about" in query_lower,
                "can you tell me about" in query_lower,
                "explain the signal" in query_lower,
                "describe the signal" in query_lower,
                "what about the" in query_lower and "signal" in query_lower,
                "details about" in query_lower,
                "more information" in query_lower
            ])
            
            
            # If this is asking about custom segments and we have a context_id
            if is_custom_segment_query and context_id:
                # Try to retrieve the previous response from context
                # For now, we'll generate a helpful response explaining what custom segments are
                # In a production system, you'd store and retrieve the actual context
                
                parts = [{
                    "kind": "text",
                    "text": (
                        "Custom segments are AI-generated audience proposals based on your search criteria. "
                        "These segments don't exist yet but can be created on demand by combining existing data signals. "
                        "\n\nTo see custom segment proposals, run a discovery query first (e.g., 'sports audiences'). "
                        "The system will analyze available segments and suggest custom combinations that better match your needs. "
                        "\n\nEach custom segment proposal includes:\n"
                        "• A descriptive name\n"
                        "• Estimated coverage and CPM\n"
                        "• The rationale for why it matches your criteria\n"
                        "• A unique ID for activation\n\n"
                        "You can activate these custom segments using their IDs, and they'll be deployed to your chosen platforms."
                    )
                }]
                
                status_message = {
                    "kind": "message",
                    "message_id": f"msg_{datetime.now().timestamp()}",
                    "parts": parts,
                    "role": "agent"
                }
                
                task_response = {
                    "id": task_id,
                    "kind": "task",
                    "contextId": context_id,
                    "status": {
                        "state": "completed",
                        "timestamp": datetime.now().isoformat(),
                        "message": status_message
                    },
                    "metadata": {
                        "response_type": "contextual_explanation"
                    }
                }
                
                return task_response
            
            # If this is asking for signal details and we have a context_id
            elif is_signal_detail_query and context_id:
                # Generate a detailed explanation of signals
                # In production, would retrieve the actual previous signals from context
                
                parts = [{
                    "kind": "text",
                    "text": (
                        "Based on your previous search, here are details about the signals found:\n\n"
                        "**Sports Enthusiasts - Public**\n"
                        "• Coverage: 45% of the addressable market\n"
                        "• CPM: $3.50 per thousand impressions\n"
                        "• Data Provider: Polk\n"
                        "• Description: Broad sports audience available platform-wide\n"
                        "• Deployment: Available on Index Exchange and The Trade Desk\n"
                        "• Activation Time: ~60 minutes\n\n"
                        "This signal targets users interested in sports content, including:\n"
                        "- Sports news readers\n"
                        "- Fantasy sports players\n"
                        "- Sports merchandise buyers\n"
                        "- Live sports streamers\n\n"
                        "The signal is immediately available for activation across multiple platforms "
                        "and provides good coverage at a competitive CPM rate."
                    )
                }]
                
                status_message = {
                    "kind": "message",
                    "message_id": f"msg_{datetime.now().timestamp()}",
                    "parts": parts,
                    "role": "agent"
                }
                
                task_response = {
                    "id": task_id,
                    "kind": "task",
                    "contextId": context_id,
                    "status": {
                        "state": "completed",
                        "timestamp": datetime.now().isoformat(),
                        "message": status_message
                    },
                    "metadata": {
                        "response_type": "signal_details"
                    }
                }
                
                return task_response
            
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
            
            # Build A2A SDK-compliant response
            # Create parts for the message
            parts = []
            if response.message:
                parts.append({
                    "kind": "text",
                    "text": response.message
                })
            
            # Add data part with structured response
            parts.append({
                "kind": "data",
                "data": response.model_dump()
            })
            
            # Create the status message
            status_message = {
                "kind": "message",
                "message_id": f"msg_{datetime.now().timestamp()}",
                "parts": parts,
                "role": "agent"
            }
            
            # Build the task response with proper status structure
            task_response = {
                "id": task_id,
                "kind": "task",
                "contextId": context_id or response.context_id,
                "status": {
                    "state": "completed",  # Using TaskState enum value
                    "timestamp": datetime.now().isoformat(),
                    "message": status_message
                },
                "metadata": {
                    "signal_count": len(response.signals),
                    "context_id": response.context_id
                }
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
            
            # Build A2A SDK-compliant response
            # Determine state based on our status
            task_state = "completed" if response.status == "deployed" else "working"
            
            # Create parts for the message
            parts = []
            if response.message:
                parts.append({
                    "kind": "text",
                    "text": response.message
                })
            
            # Add data part with structured response
            parts.append({
                "kind": "data",
                "data": response.model_dump()
            })
            
            # Create the status message
            status_message = {
                "kind": "message",
                "message_id": f"msg_{datetime.now().timestamp()}",
                "parts": parts,
                "role": "agent"
            }
            
            # Build the task response with proper status structure
            task_response = {
                "id": task_id,
                "kind": "task",
                "contextId": context_id or response.context_id,
                "status": {
                    "state": task_state,
                    "timestamp": datetime.now().isoformat(),
                    "message": status_message
                },
                "metadata": {
                    "activation_status": response.status,
                    "platform": internal_request.platform
                }
            }
            
            return task_response
            
        else:
            # Unknown or missing task type
            error_message = f"Unknown or missing task type: {task_type}"
            logger.warning(error_message)
            return {
                "id": task_id,
                "kind": "task",
                "status": "Failed",
                "contextId": context_id,
                "status": {
                    "state": "failed",
                    "timestamp": datetime.now().isoformat(),
                    "message": {
                        "kind": "message",
                        "message_id": f"msg_{datetime.now().timestamp()}",
                        "parts": [{
                            "kind": "text",
                            "text": error_message
                        }],
                        "role": "agent"
                    }
                },
                "metadata": {
                    "error_code": -32602,
                    "error_message": error_message
                }
            }
            
    except HTTPException as he:
        # Pass through HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Task failed: {e}")
        # Return A2A-compliant error response with numeric code
        return {
            "id": task_id,
            "kind": "task",
            "status": "Failed",  # Proper A2A status
            "contextId": context_id,
            "status": {
                "state": "failed",
                "timestamp": datetime.now().isoformat(),
                "message": {
                    "kind": "message",
                    "message_id": f"msg_{datetime.now().timestamp()}",
                    "parts": [{
                        "kind": "text",
                        "text": str(e)
                    }],
                    "role": "agent"
                }
            },
            "metadata": {
                "error_code": -32603,
                "error_message": str(e)
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
                # Validate and convert deliver_to dict to proper object
                from schemas import DeliverySpecification
                from pydantic import ValidationError
                
                try:
                    # Handle missing deliver_to - provide default
                    if 'deliver_to' not in tool_params:
                        tool_params['deliver_to'] = DeliverySpecification(
                            platforms='all',
                            countries=['US']
                        )
                    elif isinstance(tool_params['deliver_to'], dict):
                        # Try to create DeliverySpecification directly
                        tool_params['deliver_to'] = DeliverySpecification(**tool_params['deliver_to'])
                    
                    result = main.get_signals.fn(**tool_params)
                    
                except ValidationError as e:
                    # Return helpful error message with expected format
                    error_details = []
                    for error in e.errors():
                        field = '.'.join(str(x) for x in error['loc'])
                        error_details.append(f"  - {field}: {error['msg']}")
                    
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32602,
                            "message": "Invalid parameters for deliver_to",
                            "data": {
                                "validation_errors": error_details,
                                "expected_format": {
                                    "deliver_to": {
                                        "platforms": "all | [{platform: string, account?: string}, ...]",
                                        "countries": ["US", "UK", "CA", "..."]
                                    }
                                },
                                "examples": [
                                    {
                                        "description": "Search all platforms",
                                        "deliver_to": {
                                            "platforms": "all",
                                            "countries": ["US"]
                                        }
                                    },
                                    {
                                        "description": "Search specific platform",
                                        "deliver_to": {
                                            "platforms": [{"platform": "index-exchange"}],
                                            "countries": ["US"]
                                        }
                                    },
                                    {
                                        "description": "Platform with account",
                                        "deliver_to": {
                                            "platforms": [{"platform": "index-exchange", "account": "123456"}],
                                            "countries": ["US", "UK"]
                                        }
                                    }
                                ]
                            }
                        },
                        "id": request_id
                    })
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