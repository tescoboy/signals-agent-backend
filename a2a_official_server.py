#!/usr/bin/env python3
"""Official A2A SDK implementation for Signals Agent."""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

# Note: This requires installing the official A2A SDK
# Install with: uv add a2a-sdk or pip install a2a-sdk
try:
    from a2a import Agent, Task, TaskStatus, Message, MessagePart
    from a2a.server import A2AServer
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    print("Warning: a2a-sdk not installed. Install with: uv add a2a-sdk")

from schemas import (
    GetSignalsRequest, GetSignalsResponse,
    ActivateSignalRequest, ActivateSignalResponse
)


class SignalsAgent(Agent if A2A_AVAILABLE else object):
    """Official A2A Agent implementation for Signals."""
    
    def __init__(self, core_logic):
        if A2A_AVAILABLE:
            super().__init__(
                agent_id="signals-activation-agent",
                name="Signals Activation Agent",
                description="AI agent for discovering and activating audience signals",
                version="1.0.0"
            )
        self.core_logic = core_logic
    
    async def handle_task(self, task: 'Task') -> 'Task':
        """Handle incoming A2A tasks."""
        task_type = task.metadata.get('type', '')
        
        if task_type == 'discovery':
            return await self._handle_discovery(task)
        elif task_type == 'activation':
            return await self._handle_activation(task)
        else:
            task.status = TaskStatus.FAILED
            task.error = f"Unknown task type: {task_type}"
            return task
    
    async def _handle_discovery(self, task: 'Task') -> 'Task':
        """Handle discovery task using official A2A format."""
        try:
            # Extract parameters from task
            params = task.input_data or {}
            
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
            
            # Create response message
            message = Message()
            message.add_part(MessagePart(
                content_type="application/json",
                content=response.model_dump()
            ))
            
            # Update task
            task.output = message
            task.status = TaskStatus.COMPLETED
            task.metadata['context_id'] = response.context_id
            task.metadata['signal_count'] = len(response.signals)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
        
        return task
    
    async def _handle_activation(self, task: 'Task') -> 'Task':
        """Handle activation task using official A2A format."""
        try:
            # Extract parameters from task
            params = task.input_data or {}
            
            # Create internal request
            request = ActivateSignalRequest(
                signals_agent_segment_id=params.get('signal_id', ''),
                platform=params.get('platform', ''),
                account=params.get('account'),
                context_id=params.get('context_id')
            )
            
            # Execute activation
            response = await self.core_logic.activate_signal(request)
            
            # Create response message
            message = Message()
            message.add_part(MessagePart(
                content_type="application/json",
                content=response.model_dump()
            ))
            
            # Update task
            task.output = message
            task.status = TaskStatus.IN_PROGRESS if response.status == "activating" else TaskStatus.COMPLETED
            task.metadata['activation_status'] = response.status
            task.metadata['context_id'] = response.context_id
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
        
        return task
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities in A2A format."""
        return {
            "discovery": {
                "description": "Discover audience signals using natural language",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language audience description"},
                        "deliver_to": {"type": "object", "description": "Platform targeting specification"},
                        "filters": {"type": "object", "description": "Optional filters"},
                        "max_results": {"type": "integer", "description": "Maximum results to return"},
                        "principal_id": {"type": "string", "description": "Principal ID for access control"}
                    },
                    "required": ["query"]
                }
            },
            "activation": {
                "description": "Activate a signal on a specific platform",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "signal_id": {"type": "string", "description": "Signal to activate"},
                        "platform": {"type": "string", "description": "Target platform"},
                        "account": {"type": "string", "description": "Optional account ID"},
                        "context_id": {"type": "string", "description": "Optional discovery context"}
                    },
                    "required": ["signal_id", "platform"]
                }
            }
        }


def create_a2a_server(core_logic, host: str = "localhost", port: int = 8080):
    """Create official A2A server instance."""
    if not A2A_AVAILABLE:
        raise ImportError("a2a-sdk not installed. Install with: uv add a2a-sdk")
    
    # Create agent
    agent = SignalsAgent(core_logic)
    
    # Create server
    server = A2AServer(agent, host=host, port=port)
    
    return server


# Example usage for testing
if __name__ == "__main__":
    if not A2A_AVAILABLE:
        print("Error: a2a-sdk not installed. Install with: uv add a2a-sdk")
        exit(1)
    
    # Mock core logic for testing
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
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    core = MockCore()
    server = create_a2a_server(core)
    
    print(f"Starting official A2A server on {server.host}:{server.port}")
    server.run()