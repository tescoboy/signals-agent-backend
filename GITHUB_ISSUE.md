# Supporting Both MCP and A2A Protocols: Implementation Guide

## Overview
We successfully implemented support for both MCP (Model Context Protocol) and A2A (Agent-to-Agent) protocols in a single unified server. This allows the agent to be accessible from both Claude Desktop (via MCP) and web-based tools like A2A Inspector.

## Key Implementation Challenges & Solutions

### 1. Protocol Detection and Routing
**Challenge**: Different protocols expect different request/response formats at potentially overlapping endpoints.

**Solution**: 
- Use FastAPI's ability to handle multiple routes
- Root endpoint (`POST /`) detects JSON-RPC `message/send` for A2A
- Dedicated endpoints for each protocol (`/mcp` for MCP, `/a2a/task` for A2A tasks)

### 2. Agent Card Compliance
**Challenge**: A2A Inspector has strict validation requirements for agent cards.

**Required Fields**:
```python
{
    "name": str,
    "description": str, 
    "version": str,
    "capabilities": {
        "streaming": bool,
        "pushNotifications": bool,
        "stateTransitionHistory": bool,
        "extensions": []
    },
    "skills": [
        {
            "id": str,
            "name": str,
            "description": str,
            "tags": [str],
            "inputSchema": {}
        }
    ],
    "provider": {
        "organization": str,
        "url": str
    }
}
```

**Solution**: Ensure all required fields are present and properly typed. The `skills` array can duplicate your capabilities/tools.

### 3. JSON-RPC Message Format
**Challenge**: A2A uses JSON-RPC 2.0 for `message/send` which expects a specific response format.

**Solution**:
```python
# Detect JSON-RPC message/send
if "jsonrpc" in request and request.get("method") == "message/send":
    # Extract query from message.parts
    # Process the query
    # Return Message object (not Task object)
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "kind": "message",
            "message_id": f"msg_{timestamp}",  # Note: underscore, not camelCase
            "parts": [...],
            "role": "agent"  # Not "assistant"
        }
    }
```

### 4. Task Response Structure
**Challenge**: A2A expects specific nested structures for task responses.

**Correct Structure**:
```python
{
    "id": task_id,
    "kind": "task",
    "contextId": context_id,
    "status": {
        "state": "completed",  # or "working", "failed"
        "timestamp": iso_timestamp,
        "message": {
            "kind": "message",
            "message_id": msg_id,
            "parts": [
                {"kind": "text", "text": "Human readable"},
                {"kind": "data", "data": {...}}
            ],
            "role": "agent"
        }
    },
    "metadata": {...}
}
```

### 5. CORS Headers
**Challenge**: Web-based tools need CORS headers to access the API.

**Solution**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

### 6. HTTPS URL Generation
**Challenge**: Deployed agents behind proxies need to generate correct HTTPS URLs in agent cards.

**Solution**:
```python
# Detect proxy and use correct protocol
forwarded_proto = request.headers.get("X-Forwarded-Proto")
if forwarded_proto:
    base_url = f"{forwarded_proto}://{request.headers.get('Host', 'localhost')}"
else:
    base_url = f"{request.url.scheme}://{request.url.netloc}"
```

### 7. Error Handling
**Challenge**: A2A expects JSON-RPC numeric error codes, not string codes.

**Solution**:
```python
# Use standard JSON-RPC error codes
error_response = {
    "id": task_id,
    "kind": "task",
    "status": {
        "state": "failed",
        "message": {...},
        "error": {
            "code": -32602,  # Invalid params
            "message": "Unknown task type"
        }
    }
}
```

### 8. Well-Known Endpoint
**Challenge**: A2A specification recommends agent card at `/.well-known/agent.json`.

**Solution**:
```python
@app.get("/.well-known/agent.json")
@app.get("/agent-card")
async def get_agent_card(request: Request):
    # Return same agent card for both endpoints
```

## Testing Recommendations

### 1. Protocol Compliance Test
Create a comprehensive test suite that validates both protocols:
```python
def test_a2a_protocol():
    # Test agent card format
    # Test JSON-RPC message/send
    # Test task endpoints
    # Test error handling
    # Test CORS headers

def test_mcp_protocol():
    # Test tool discovery
    # Test function calling
    # Test SSE streaming
```

### 2. Use Official SDKs
- For A2A: `pip install a2a-sdk`
- For MCP: `pip install fastmcp`

### 3. Test with Official Tools
- A2A Inspector: https://a2a-inspector.vercel.app/
- MCP Explorer: Via Claude Desktop

## Common Pitfalls to Avoid

1. **Field Naming**: Use `message_id` not `messageId`, use `Role.agent` not `Role.assistant`
2. **Response Types**: Return `Message` for message/send, `Task` for task endpoints
3. **Database Duplicates**: Check if data exists before inserting during initialization
4. **Deployment Counting**: Count unique platforms, not individual deployment records
5. **Context Handling**: Maintain conversation context for follow-up queries

## Benefits of Dual Protocol Support

1. **Wider Reach**: Accessible from both desktop (MCP) and web (A2A) environments
2. **Tool Compatibility**: Works with multiple AI agent tools and platforms
3. **Future-Proof**: Ready for either protocol to become dominant
4. **Shared Logic**: Business logic remains in one place, only request/response transformation differs

## Example Implementation

Our full implementation is available at: [TODO: Add repository link]

Key files:
- `unified_server.py`: FastAPI server handling both protocols
- `main.py`: Shared business logic
- `test_a2a_protocol.py`: Comprehensive A2A compliance tests

## Conclusion

Supporting both protocols requires careful attention to request/response formats and validation requirements, but the unified approach minimizes code duplication and maximizes compatibility. The key is understanding each protocol's specific requirements and handling the transformations appropriately.