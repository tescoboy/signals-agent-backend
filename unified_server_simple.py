#!/usr/bin/env python3
"""Simplified HTTP server supporting both MCP and A2A protocols."""

import asyncio
import logging
import uuid
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Simple logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_signals_simple(spec: str, max_results: int = 10):
    """Simple wrapper for the MCP get_signals function."""
    from schemas import DeliverySpecification
    
    # Create a simple delivery specification for "all" platforms
    deliver_to = DeliverySpecification(platforms="all")
    
    # Call the MCP function
    result = main.get_signals(
        signal_spec=spec,
        deliver_to=deliver_to,
        max_results=max_results
    )
    
    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting up Signals Agent server...")
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Signals Agent server...")


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "protocols": ["mcp", "a2a"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/signals")
async def get_signals(
    spec: str,
    max_results: int = 10,
    request: Request = None
):
    """Get signals based on specification."""
    try:
        logger.info(f"Received signal request: spec='{spec}', max_results={max_results}")
        
        # Call the simple wrapper function
        result = get_signals_simple(spec, max_results)
        
        logger.info(f"Signal request completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_signals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals")
async def get_signals_post(request: GetSignalsRequest):
    """Get signals based on specification (POST endpoint)."""
    try:
        logger.info(f"Received POST signal request: spec='{request.spec}', max_results={request.max_results}")
        
        # Call the simple wrapper function
        result = get_signals_simple(request.spec, request.max_results)
        
        logger.info(f"POST signal request completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_signals_post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/activate")
async def activate_signal(request: ActivateSignalRequest):
    """Activate a signal."""
    try:
        logger.info(f"Received activation request for signal: {request.signal_id}")
        
        # For now, return a mock response
        # TODO: Implement actual signal activation
        result = {
            "message": f"Signal {request.signal_id} activation initiated",
            "activation_id": str(uuid.uuid4()),
            "status": "pending",
            "estimated_completion": datetime.now().isoformat()
        }
        
        logger.info(f"Activation request completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in activate_signal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
