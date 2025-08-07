"""A2A Protocol server implementation for Signals Agent."""

import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

from protocol_abstraction import CoreBusinessLogic, A2AAdapter

logger = logging.getLogger(__name__)


class A2AAgentCard:
    """Agent Card for A2A protocol discovery."""
    
    @staticmethod
    def generate() -> Dict[str, Any]:
        """Generate the Agent Card for this signals agent."""
        return {
            "agentId": "signals-activation-agent",
            "name": "Signals Activation Agent",
            "description": "AI agent for discovering and activating audience signals across advertising platforms",
            "version": "1.0.0",
            "capabilities": {
                "discovery": {
                    "description": "Discover audience signals using natural language",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Natural language audience description"},
                            "deliver_to": {"type": "object", "description": "Platform targeting specification"},
                            "filters": {"type": "object", "description": "Optional filters"},
                            "max_results": {"type": "integer", "description": "Maximum results to return"},
                            "principal_id": {"type": "string", "description": "Principal ID for access control"}
                        },
                        "required": ["query"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "context_id": {"type": "string"},
                            "signals": {"type": "array"},
                            "custom_segment_proposals": {"type": "array"},
                            "clarification_needed": {"type": "string"}
                        }
                    }
                },
                "activation": {
                    "description": "Activate a signal on a specific platform",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "signal_id": {"type": "string", "description": "Signal to activate"},
                            "platform": {"type": "string", "description": "Target platform"},
                            "account": {"type": "string", "description": "Optional account ID"},
                            "context_id": {"type": "string", "description": "Optional discovery context"}
                        },
                        "required": ["signal_id", "platform"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "decisioning_platform_segment_id": {"type": "string"},
                            "status": {"type": "string", "enum": ["deployed", "activating", "failed"]},
                            "context_id": {"type": "string"}
                        }
                    }
                }
            },
            "protocols": ["a2a"],
            "endpoint": "http://localhost:8080/a2a",
            "authRequired": False
        }


class A2ARequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for A2A protocol."""
    
    def __init__(self, adapter: A2AAdapter, *args, **kwargs):
        self.adapter = adapter
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle POST requests for A2A tasks."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data.decode('utf-8'))
            
            # Route based on task type
            task_type = request.get('type', '')
            
            if task_type == 'discovery':
                response = asyncio.run(self.adapter.handle_discovery(request))
            elif task_type == 'activation':
                response = asyncio.run(self.adapter.handle_activation(request))
            elif self.path == '/agent-card':
                response = A2AAgentCard.generate()
            else:
                self.send_error(400, f"Unknown task type: {task_type}")
                return
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error handling A2A request: {e}")
            self.send_error(500, str(e))
    
    def do_GET(self):
        """Handle GET requests for agent card."""
        if self.path == '/agent-card':
            response = A2AAgentCard.generate()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404, "Not found")
    
    def log_message(self, format, *args):
        """Override to use proper logging."""
        logger.info(f"A2A: {format % args}")


class A2AServer:
    """A2A Protocol server."""
    
    def __init__(self, core_logic: CoreBusinessLogic, host: str = "localhost", port: int = 8080):
        self.core_logic = core_logic
        self.adapter = A2AAdapter(core_logic)
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the A2A server in a background thread."""
        def handler_factory(*args, **kwargs):
            return A2ARequestHandler(self.adapter, *args, **kwargs)
        
        self.server = HTTPServer((self.host, self.port), handler_factory)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"A2A server started on http://{self.host}:{self.port}")
        logger.info(f"Agent Card available at http://{self.host}:{self.port}/agent-card")
    
    def stop(self):
        """Stop the A2A server."""
        if self.server:
            self.server.shutdown()
            self.server_thread.join()
            logger.info("A2A server stopped")


# Example A2A task format for reference
EXAMPLE_DISCOVERY_TASK = {
    "taskId": "task_123456",
    "type": "discovery",
    "parameters": {
        "query": "luxury car buyers",
        "deliver_to": {
            "platforms": "all",
            "countries": ["US"]
        },
        "max_results": 10,
        "principal_id": "acme_corp"
    }
}

EXAMPLE_ACTIVATION_TASK = {
    "taskId": "task_789012",
    "type": "activation",
    "parameters": {
        "signal_id": "luxury_auto_intenders",
        "platform": "the-trade-desk",
        "account": "acct_12345",
        "context_id": "ctx_1234567890_abcdef"
    }
}


if __name__ == "__main__":
    # This would be used for standalone testing
    logging.basicConfig(level=logging.INFO)
    
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
    
    core = type('obj', (object,), {
        'discover_signals': MockCore().discover_signals,
        'activate_signal': MockCore().activate_signal
    })()
    
    server = A2AServer(core)
    server.start()
    
    try:
        input("A2A server running. Press Enter to stop...\n")
    finally:
        server.stop()