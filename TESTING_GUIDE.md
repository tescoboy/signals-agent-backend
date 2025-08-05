# Testing Guide for Unified MCP/A2A Server

## Quick Start

### 1. Run Automated Tests
```bash
# Run the comprehensive test suite
uv run python test_unified_server.py

# If server is already running
uv run python test_unified_server.py --no-start
```

### 2. Start the Server Manually
```bash
# Start unified server (both protocols)
uv run python unified_server.py

# Or use the multi-protocol server
uv run python multi_protocol_server.py --protocols all
```

## Manual Testing

### Test A2A Protocol

#### 1. Get Agent Card
```bash
curl http://localhost:8000/agent-card | python -m json.tool
```

#### 2. A2A Discovery
```bash
curl -X POST http://localhost:8000/a2a/task \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "manual_test_123",
    "type": "discovery",
    "parameters": {
      "query": "luxury car buyers",
      "max_results": 3
    }
  }' | python -m json.tool
```

#### 3. A2A Activation
```bash
curl -X POST http://localhost:8000/a2a/task \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "manual_activation_456",
    "type": "activation",
    "parameters": {
      "signal_id": "sports_enthusiasts_public",
      "platform": "the-trade-desk",
      "context_id": "ctx_123_abc"  # Optional: use context from discovery
    }
  }' | python -m json.tool
```

### Test MCP Protocol

#### 1. List Available Tools
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }' | python -m json.tool
```

#### 2. MCP Discovery
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_signals",
      "arguments": {
        "signal_spec": "sports fans",
        "deliver_to": {"platforms": "all"},
        "max_results": 5
      }
    },
    "id": 2
  }' | python -m json.tool
```

#### 3. MCP Activation
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "activate_signal",
      "arguments": {
        "signals_agent_segment_id": "luxury_auto_intenders",
        "platform": "index-exchange",
        "context_id": "ctx_123_abc"  # Optional
      }
    },
    "id": 3
  }' | python -m json.tool
```

### Test Cross-Protocol Features

#### 1. Discovery with A2A, Activate with MCP
```bash
# Step 1: Discover with A2A
CONTEXT_ID=$(curl -s -X POST http://localhost:8000/a2a/task \
  -H "Content-Type: application/json" \
  -d '{"taskId": "discovery_1", "type": "discovery", "parameters": {"query": "luxury buyers"}}' \
  | jq -r '.parts[0].content.context_id')

echo "Context ID: $CONTEXT_ID"

# Step 2: Activate with MCP using the A2A context
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"activate_signal\",
      \"arguments\": {
        \"signals_agent_segment_id\": \"luxury_auto_intenders\",
        \"platform\": \"the-trade-desk\",
        \"context_id\": \"$CONTEXT_ID\"
      }
    },
    \"id\": 4
  }" | python -m json.tool
```

#### 2. Check Server Health
```bash
curl http://localhost:8000/health | python -m json.tool
```

## What to Look For

### ✅ Success Indicators:
1. **Agent Card**: Should show both MCP and A2A in protocols
2. **Context IDs**: Format like `ctx_1234567890_abc123`
3. **Cross-Protocol**: Context from one protocol works in the other
4. **No Errors**: Both protocols return valid responses
5. **Shared State**: Same signals returned by both protocols

### ❌ Potential Issues:
1. **Port 8000 in use**: Change port or kill existing process
2. **Module not found**: Run from the project directory
3. **Database locked**: SQLite concurrency issue (rare)
4. **Context not found**: Context IDs expire after 7 days

## Performance Testing

### Concurrent Requests
```bash
# Test both protocols simultaneously
(curl -X POST http://localhost:8000/a2a/task -H "Content-Type: application/json" -d '{"taskId": "perf_1", "type": "discovery", "parameters": {"query": "test"}}' &) && \
(curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' &) && \
wait
```

## Debugging

### Enable Debug Logging
```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
uv run python unified_server.py
```

### Check Database
```bash
# View contexts table
sqlite3 signals_agent.db "SELECT * FROM contexts ORDER BY created_at DESC LIMIT 5;"
```

### Monitor Server Logs
```bash
# Run server with verbose output
uv run python unified_server.py 2>&1 | tee server.log
```

## Integration with Claude Desktop

To use with Claude Desktop, update your MCP settings to point to the unified server:
```json
{
  "mcpServers": {
    "signals-agent": {
      "command": "uv",
      "args": ["run", "python", "unified_server.py"],
      "env": {}
    }
  }
}
```

Note: The unified server defaults to HTTP mode, perfect for Claude Desktop.