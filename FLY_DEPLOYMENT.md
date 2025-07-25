# Fly.io Deployment Guide

This guide explains how to deploy the Audience Agent to Fly.io with proper configuration and secrets management.

## Prerequisites

1. Install the Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Sign up/login to Fly.io:
```bash
fly auth login
```

## Initial Setup

The fly.toml file has already been created. Review the configuration:
- App name: `audience-agent`
- Region: `fra` (Frankfurt)
- Memory: 1GB
- Auto-stop enabled to save costs

## Configuration and Secrets

### Option 1: Using Fly Secrets (Recommended for Production)

1. Set your Gemini API key as a secret:
```bash
fly secrets set GEMINI_API_KEY="your-gemini-api-key-here"
```

2. Set Index Exchange credentials (if using):
```bash
fly secrets set IX_USERNAME="your-ix-username"
fly secrets set IX_PASSWORD="your-ix-password"
```

3. Update the application to read from environment variables. Create a file `config_loader.py`:
```python
import os
import json

def load_config():
    """Load config with environment variable overrides."""
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Override with environment variables if present
    if gemini_key := os.environ.get('GEMINI_API_KEY'):
        config['gemini_api_key'] = gemini_key
    
    if ix_username := os.environ.get('IX_USERNAME'):
        config['platforms']['index-exchange']['username'] = ix_username
    
    if ix_password := os.environ.get('IX_PASSWORD'):
        config['platforms']['index-exchange']['password'] = ix_password
    
    return config
```

### Option 2: Build-time Configuration

1. Create a production config file locally:
```bash
cp config.json.sample config.prod.json
# Edit config.prod.json with your actual credentials
```

2. Update Dockerfile to use production config:
```dockerfile
# Replace the config copy line with:
COPY config.prod.json config.json
```

3. **Important**: Add `config.prod.json` to `.gitignore` to avoid committing secrets:
```bash
echo "config.prod.json" >> .gitignore
```

## Deployment Steps

1. Deploy the application:
```bash
fly deploy
```

2. Check deployment status:
```bash
fly status
```

3. View logs:
```bash
fly logs
```

4. SSH into the running container (for debugging):
```bash
fly ssh console
```

## Web Interface Setup

Since this is an MCP server, you'll need to set up a web interface for Fly.io. Options:

### Option 1: Add a Simple Web Server

Create `web_server.py`:
```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return JSONResponse({
        "name": "Audience Agent",
        "type": "MCP Server",
        "status": "running",
        "docs": "https://github.com/adcontextprotocol/audience-agent"
    })

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Update Dockerfile CMD:
```dockerfile
CMD ["uv", "run", "python", "web_server.py"]
```

### Option 2: Run MCP Server with HTTP Transport

Update fly.toml to use a different port since MCP doesn't use HTTP by default:
```toml
[processes]
mcp = "uv run python main.py"

[http_service]
  processes = ["mcp"]
  internal_port = 5173  # MCP default port
```

## Managing Multiple Environments

### Development
```bash
# Use config.json locally
cp config.json.sample config.json
# Edit with test credentials
```

### Staging
```bash
fly deploy --app audience-agent-staging
fly secrets set GEMINI_API_KEY="staging-key" --app audience-agent-staging
```

### Production
```bash
fly deploy --app audience-agent
fly secrets set GEMINI_API_KEY="production-key" --app audience-agent
```

## Security Best Practices

1. **Never commit secrets to git**
   - Use environment variables via `fly secrets`
   - Add sensitive files to `.gitignore`

2. **Rotate credentials regularly**
   ```bash
   fly secrets set GEMINI_API_KEY="new-key-value"
   ```

3. **Use different credentials per environment**
   - Development: Test credentials
   - Staging: Separate staging credentials
   - Production: Production-only credentials

4. **Monitor access**
   ```bash
   fly logs | grep "authentication"
   ```

## Updating Configuration

To update configuration without redeploying:

1. For secrets:
```bash
fly secrets set KEY="new-value"
# This will restart the app automatically
```

2. For non-secret config changes:
```bash
# SSH into the container
fly ssh console

# Edit config file
vi config.json

# Restart the app
fly apps restart
```

## Troubleshooting

1. **App won't start**: Check logs for missing config
```bash
fly logs
```

2. **Authentication failures**: Verify secrets are set
```bash
fly secrets list
```

3. **Database issues**: The SQLite database is ephemeral. For production, consider:
   - Using Fly Volumes for persistence
   - Migrating to PostgreSQL

## Cost Optimization

The current configuration uses:
- Auto-stop machines (stops when idle)
- Minimal resources (1GB RAM, shared CPU)
- Single region deployment

To further optimize:
```toml
[http_service]
  min_machines_running = 0  # Scale to zero when idle
  auto_stop_machines = 'stop'
  auto_start_machines = true
```

## Next Steps

1. Set up monitoring:
```bash
fly logs --tail
```

2. Configure alerts:
   - Set up Fly.io monitoring
   - Add health check endpoints

3. Scale as needed:
```bash
fly scale count 2  # Run 2 instances
fly scale memory 2048  # Increase to 2GB RAM
```