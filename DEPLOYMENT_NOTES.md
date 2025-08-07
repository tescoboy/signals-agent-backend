# Deployment Notes - Unified MCP/A2A Server

## Deployment Summary

Successfully deployed the unified server supporting both MCP and A2A protocols to Fly.io.

### Deployment Details

- **App Name**: audience-agent
- **URL**: https://audience-agent.fly.dev
- **Region**: fra (Frankfurt)
- **Deployment Date**: 2025-08-05
- **Docker Image Size**: 185 MB

### Available Endpoints

1. **Health Check**: https://audience-agent.fly.dev/health
   - Returns: `{"status":"healthy","protocols":["mcp","a2a"],"timestamp":"..."}`

2. **A2A Agent Card**: https://audience-agent.fly.dev/agent-card
   - Returns agent capabilities and supported protocols

3. **A2A Task Execution**: https://audience-agent.fly.dev/a2a/task
   - POST endpoint for A2A task requests

4. **MCP JSON-RPC**: https://audience-agent.fly.dev/mcp
   - POST endpoint for MCP protocol requests

### Testing the Deployment

Test A2A Discovery:
```bash
curl -X POST https://audience-agent.fly.dev/a2a/task \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "test_123",
    "type": "discovery",
    "parameters": {
      "query": "luxury car buyers",
      "max_results": 3
    }
  }'
```

Test MCP Tools List:
```bash
curl -X POST https://audience-agent.fly.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

### Configuration

The deployed server uses environment variables for configuration:
- Set `GEMINI_API_KEY` via `fly secrets set`
- Platform credentials can be configured via environment variables
- See `config_loader.py` for all supported environment variables

### Monitoring

- View logs: `fly logs`
- Check status: `fly status`
- SSH into container: `fly ssh console`
- Monitor at: https://fly.io/apps/audience-agent/monitoring

### Next Steps

1. Set production API keys:
   ```bash
   fly secrets set GEMINI_API_KEY="your-production-key"
   ```

2. Configure platform credentials if needed:
   ```bash
   fly secrets set IX_USERNAME="your-username"
   fly secrets set IX_PASSWORD="your-password"
   ```

3. Scale if needed:
   ```bash
   fly scale count 2  # Run 2 instances
   fly scale memory 2048  # Increase to 2GB RAM
   ```

### Architecture Notes

The unified server:
- Runs on a single port (8000)
- Supports both MCP (JSON-RPC) and A2A (REST) protocols
- Uses FastAPI with uvicorn for production performance
- Shares context IDs between protocols
- Uses SQLite database (ephemeral - consider Fly Volumes for persistence)