#!/usr/bin/env python3
"""Multi-protocol server for Signals Agent supporting both MCP and A2A."""

import sys
import os
import asyncio
import logging
import argparse
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from database import init_db
from config_loader import load_config
from adapters.manager import AdapterManager
from protocol_abstraction import CoreBusinessLogic
try:
    from a2a_fastapi_server import create_a2a_server
    A2A_AVAILABLE = True
except ImportError as e:
    A2A_AVAILABLE = False
    logger.warning(f"A2A dependencies not available: {e}")


def setup_core_logic():
    """Initialize core business logic components."""
    # Initialize database
    init_db()
    
    # Load configuration
    config = load_config()
    
    # Initialize adapter manager
    adapter_manager = AdapterManager(config)
    
    # Create core business logic instance
    # Note: In a real implementation, we'd refactor main.py to use CoreBusinessLogic
    # For now, we'll use a simplified version
    class SimplifiedCore:
        def __init__(self, config, adapter_manager):
            self.config = config
            self.adapter_manager = adapter_manager
        
        async def discover_signals(self, request):
            # Import the actual functions from FastMCP FunctionTool
            import main
            # FastMCP wraps functions in FunctionTool, access the actual function via .fn
            return main.get_signals.fn(
                signal_spec=request.signal_spec,
                deliver_to=request.deliver_to,
                filters=request.filters,
                max_results=request.max_results,
                principal_id=request.principal_id
            )
        
        async def activate_signal(self, request):
            # Import the actual functions from FastMCP FunctionTool
            import main
            # FastMCP wraps functions in FunctionTool, access the actual function via .fn
            return main.activate_signal.fn(
                signals_agent_segment_id=request.signals_agent_segment_id,
                platform=request.platform,
                account=request.account,
                principal_id=getattr(request, 'principal_id', None),
                context_id=request.context_id
            )
    
    return SimplifiedCore(config, adapter_manager)


def run_mcp_server():
    """Run the MCP server."""
    logger.info("Starting MCP server...")
    
    # Import and run the existing MCP server
    import main
    main.mcp.run()


def run_a2a_server(core_logic, host: str = "localhost", port: int = 8080):
    """Run the A2A server using FastAPI."""
    if not A2A_AVAILABLE:
        logger.error("Cannot start A2A server: dependencies not available")
        return None
    
    logger.info(f"Starting A2A server on {host}:{port}...")
    
    server = create_a2a_server(core_logic, host, port)
    
    # Run server in background thread
    import threading
    server_thread = threading.Thread(
        target=server.run, 
        args=(host, port),
        daemon=True
    )
    server_thread.start()
    
    return server


def main():
    """Main entry point for multi-protocol server."""
    parser = argparse.ArgumentParser(description="Multi-protocol Signals Agent Server")
    parser.add_argument(
        '--protocols',
        nargs='+',
        choices=['mcp', 'a2a', 'all'],
        default=['all'],
        help='Protocols to enable (default: all)'
    )
    parser.add_argument(
        '--a2a-host',
        default='localhost',
        help='A2A server host (default: localhost)'
    )
    parser.add_argument(
        '--a2a-port',
        type=int,
        default=8080,
        help='A2A server port (default: 8080)'
    )
    parser.add_argument(
        '--mcp-only',
        action='store_true',
        help='Run only MCP server (same as --protocols mcp)'
    )
    
    args = parser.parse_args()
    
    # Handle legacy --mcp-only flag
    if args.mcp_only:
        args.protocols = ['mcp']
    
    # Normalize protocols
    if 'all' in args.protocols:
        protocols = ['mcp', 'a2a']
    else:
        protocols = args.protocols
    
    logger.info(f"Starting Signals Agent with protocols: {protocols}")
    
    # Initialize core logic
    core_logic = setup_core_logic()
    
    # Start servers based on selected protocols
    a2a_server = None
    
    try:
        if 'a2a' in protocols:
            # Start A2A server in background
            a2a_server = run_a2a_server(core_logic, args.a2a_host, args.a2a_port)
            
            # Give A2A server time to start
            import time
            time.sleep(1)
        
        if 'mcp' in protocols:
            # Run MCP server (this will block)
            run_mcp_server()
        elif 'a2a' in protocols:
            # If only A2A, keep the server running
            logger.info("A2A server is running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
    
    finally:
        # Clean up A2A server
        if a2a_server:
            logger.info("A2A server stopped")


if __name__ == "__main__":
    main()