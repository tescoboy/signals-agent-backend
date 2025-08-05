#!/usr/bin/env python3
"""A2A Server implementation using FastAPI and the official a2a-sdk."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from schemas import (
    GetSignalsRequest, GetSignalsResponse,
    ActivateSignalRequest, ActivateSignalResponse
)

# Note: We're using FastAPI directly rather than a2a-sdk internals
# The a2a-sdk is more focused on database models and doesn't provide
# a simple server implementation, so we implement the A2A protocol directly

logger = logging.getLogger(__name__)


class A2ATaskRequest(BaseModel):
    """A2A Task request format."""
    taskId: str
    type: str
    parameters: Dict[str, Any]


class A2ATaskResponse(BaseModel):
    """A2A Task response format."""
    taskId: str
    status: str
    completedAt: Optional[str] = None
    parts: list
    artifact: Optional[Dict[str, Any]] = None


class SignalsA2AServer:
    """A2A server implementation for Signals Agent."""
    
    def __init__(self, core_logic):
        self.core_logic = core_logic
        self.app = FastAPI(title="Signals A2A Agent")
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up FastAPI routes for A2A protocol."""
        
        @self.app.get("/agent-card")
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
                "protocols": ["a2a"],
                "endpoint": "http://localhost:8080/a2a/task"
            }
        
        @self.app.post("/a2a/task")
        async def handle_task(task_request: A2ATaskRequest):
            """Handle A2A task requests."""
            try:
                if task_request.type == "discovery":
                    return await self._handle_discovery(task_request)
                elif task_request.type == "activation":
                    return await self._handle_activation(task_request)
                else:
                    raise HTTPException(400, f"Unknown task type: {task_request.type}")
            
            except Exception as e:
                logger.error(f"Task failed: {e}")
                return A2ATaskResponse(
                    taskId=task_request.taskId,
                    status="failed",
                    parts=[{
                        "contentType": "text/plain",
                        "content": str(e)
                    }]
                )
    
    async def _handle_discovery(self, task: A2ATaskRequest) -> A2ATaskResponse:
        """Handle discovery task."""
        params = task.parameters
        
        # Create internal request
        request = GetSignalsRequest(
            signal_spec=params.get('query', ''),
            deliver_to=params.get('deliver_to', {'platforms': 'all', 'countries': ['US']}),
            filters=params.get('filters'),
            max_results=params.get('max_results', 10),
            principal_id=params.get('principal_id')
        )
        
        # Execute discovery
        response = await self.core_logic.discover_signals(request)
        
        # Return A2A response
        return A2ATaskResponse(
            taskId=task.taskId,
            status="completed",
            completedAt=datetime.now().isoformat(),
            parts=[{
                "contentType": "application/json",
                "content": response.model_dump()
            }],
            artifact={
                "type": "discovery_results",
                "context_id": response.context_id,
                "signal_count": len(response.signals)
            }
        )
    
    async def _handle_activation(self, task: A2ATaskRequest) -> A2ATaskResponse:
        """Handle activation task."""
        params = task.parameters
        
        # Create internal request
        request = ActivateSignalRequest(
            signals_agent_segment_id=params.get('signal_id', ''),
            platform=params.get('platform', ''),
            account=params.get('account'),
            context_id=params.get('context_id')
        )
        
        # Execute activation
        response = await self.core_logic.activate_signal(request)
        
        # Determine A2A status
        a2a_status = "completed" if response.status == "deployed" else "in_progress"
        
        # Return A2A response
        return A2ATaskResponse(
            taskId=task.taskId,
            status=a2a_status,
            completedAt=datetime.now().isoformat() if a2a_status == "completed" else None,
            parts=[{
                "contentType": "application/json",
                "content": response.model_dump()
            }],
            artifact={
                "type": "activation_result",
                "context_id": response.context_id,
                "status": response.status
            }
        )
    
    def run(self, host: str = "localhost", port: int = 8080):
        """Run the FastAPI server."""
        uvicorn.run(self.app, host=host, port=port)


def create_a2a_server(core_logic, host: str = "localhost", port: int = 8080):
    """Create and return an A2A server instance."""
    server = SignalsA2AServer(core_logic)
    return server


# For testing
if __name__ == "__main__":
    # Mock core logic
    class MockCore:
        async def discover_signals(self, request):
            from schemas import GetSignalsResponse, SignalResponse, PlatformDeployment, PricingModel
            return GetSignalsResponse(
                message="Found 1 test signal",
                context_id="ctx_test_123",
                signals=[
                    SignalResponse(
                        signals_agent_segment_id="test_signal",
                        name="Test Signal",
                        description="Test description",
                        signal_type="audience",
                        data_provider="Test Provider",
                        coverage_percentage=50.0,
                        deployments=[
                            PlatformDeployment(
                                platform="test-platform",
                                is_live=True,
                                scope="platform-wide"
                            )
                        ],
                        pricing=PricingModel(cpm=5.0)
                    )
                ]
            )
        
        async def activate_signal(self, request):
            from schemas import ActivateSignalResponse
            return ActivateSignalResponse(
                message="Test activation successful",
                decisioning_platform_segment_id="test_platform_123",
                estimated_activation_duration_minutes=60,
                status="activating",
                context_id="ctx_activation_456"
            )
    
    logging.basicConfig(level=logging.INFO)
    core = MockCore()
    server = create_a2a_server(core)
    server.run()