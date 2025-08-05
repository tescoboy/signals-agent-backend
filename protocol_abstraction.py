"""Protocol abstraction layer for supporting multiple protocols (MCP, A2A, REST)."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from schemas import (
    GetSignalsRequest, GetSignalsResponse,
    ActivateSignalRequest, ActivateSignalResponse
)


class ProtocolAdapter(ABC):
    """Abstract base class for protocol adapters."""
    
    @abstractmethod
    async def handle_discovery(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle signal discovery request."""
        pass
    
    @abstractmethod
    async def handle_activation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle signal activation request."""
        pass
    
    @abstractmethod
    def get_protocol_name(self) -> str:
        """Return the protocol name."""
        pass


class CoreBusinessLogic:
    """Shared business logic for all protocols."""
    
    def __init__(self, db_connection, adapter_manager, config):
        self.db = db_connection
        self.adapter_manager = adapter_manager
        self.config = config
    
    async def discover_signals(self, request: GetSignalsRequest) -> GetSignalsResponse:
        """Core signal discovery logic extracted from main.py."""
        # This would contain the actual implementation from get_signals()
        # For now, returning a placeholder
        from main import get_signals
        return await get_signals(
            signal_spec=request.signal_spec,
            deliver_to=request.deliver_to,
            filters=request.filters,
            max_results=request.max_results,
            principal_id=request.principal_id
        )
    
    async def activate_signal(self, request: ActivateSignalRequest) -> ActivateSignalResponse:
        """Core signal activation logic extracted from main.py."""
        # This would contain the actual implementation from activate_signal()
        from main import activate_signal
        return await activate_signal(
            signals_agent_segment_id=request.signals_agent_segment_id,
            platform=request.platform,
            account=request.account,
            principal_id=getattr(request, 'principal_id', None),
            context_id=request.context_id
        )


class MCPAdapter(ProtocolAdapter):
    """Adapter for MCP protocol."""
    
    def __init__(self, core_logic: CoreBusinessLogic):
        self.core = core_logic
    
    async def handle_discovery(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP request to core format and back."""
        # MCP already uses our schemas directly
        req = GetSignalsRequest(**request)
        response = await self.core.discover_signals(req)
        return response.model_dump()
    
    async def handle_activation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP request to core format and back."""
        req = ActivateSignalRequest(**request)
        response = await self.core.activate_signal(req)
        return response.model_dump()
    
    def get_protocol_name(self) -> str:
        return "MCP"


class A2AAdapter(ProtocolAdapter):
    """Adapter for A2A protocol."""
    
    def __init__(self, core_logic: CoreBusinessLogic):
        self.core = core_logic
    
    async def handle_discovery(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert A2A task to core format and back."""
        # Extract parameters from A2A task format
        task_id = request.get('taskId')
        params = request.get('parameters', {})
        
        # Map A2A parameters to our schema
        core_request = GetSignalsRequest(
            signal_spec=params.get('query', params.get('signal_spec', '')),
            deliver_to=params.get('deliver_to', {'platforms': 'all', 'countries': ['US']}),
            filters=params.get('filters'),
            max_results=params.get('max_results', 10),
            principal_id=params.get('principal_id')
        )
        
        # Execute core logic
        response = await self.core.discover_signals(core_request)
        
        # Convert to A2A task response format
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
    
    async def handle_activation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert A2A task to core format and back."""
        task_id = request.get('taskId')
        params = request.get('parameters', {})
        
        # Map A2A parameters to our schema
        core_request = ActivateSignalRequest(
            signals_agent_segment_id=params.get('signal_id', params.get('signals_agent_segment_id', '')),
            platform=params.get('platform', ''),
            account=params.get('account'),
            context_id=params.get('context_id')
        )
        
        # Execute core logic
        response = await self.core.activate_signal(core_request)
        
        # Convert to A2A task response format
        return {
            "taskId": task_id,
            "status": "completed" if response.status == "deployed" else "in_progress",
            "completedAt": datetime.now().isoformat() if response.status == "deployed" else None,
            "parts": [{
                "contentType": "application/json",
                "content": response.model_dump()
            }],
            "artifact": {
                "type": "activation_result",
                "context_id": response.context_id,
                "platform_segment_id": response.decisioning_platform_segment_id,
                "status": response.status
            }
        }
    
    def get_protocol_name(self) -> str:
        return "A2A"


class ProtocolManager:
    """Manages multiple protocol adapters."""
    
    def __init__(self, core_logic: CoreBusinessLogic):
        self.core = core_logic
        self.adapters = {
            'mcp': MCPAdapter(core_logic),
            'a2a': A2AAdapter(core_logic)
        }
    
    def get_adapter(self, protocol: str) -> Optional[ProtocolAdapter]:
        """Get adapter for specified protocol."""
        return self.adapters.get(protocol.lower())
    
    def list_protocols(self) -> List[str]:
        """List supported protocols."""
        return list(self.adapters.keys())