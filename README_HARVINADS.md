# Signals Agent Backend for HarvinAds Frontend

This is the existing Signals Agent backend that provides the API endpoints for the HarvinAds frontend. The backend is ready to run as-is without any modifications.

## Quick Start

### 1. Set up Python Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file (see `.env.example` for template):

```bash
# Optional: AI functionality (Gemini API)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Database path override
DATABASE_PATH=./signals.db

# Optional: CORS origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend-domain.vercel.app
```

### 3. Start the Server

```bash
python unified_server.py
```

The server will start on `http://localhost:8000` and automatically seed the database with sample data from `sample_data.json` on first run.

### 4. Verify Installation

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "protocols": ["mcp", "a2a"],
  "timestamp": "2025-01-XX..."
}
```

## API Endpoints

### Health Check
- **GET** `/health` - Returns server status and supported protocols

### A2A Task Endpoint
- **POST** `/a2a/task` - Main endpoint for discovery and activation tasks

### Discovery Request Example

```bash
curl -X POST http://localhost:8000/a2a/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "discovery",
    "parameters": {
      "query": "sports enthusiasts",
      "filters": {
        "max_cpm": 15,
        "min_coverage_percentage": 5,
        "provider": "liveramp"
      }
    },
    "taskId": "t1"
  }'
```

### Expected Response Format

The response will include matched segments and optionally proposed segments (when Gemini is enabled):

```json
{
  "id": "t1",
  "kind": "task",
  "status": {
    "state": "completed",
    "timestamp": "2025-01-XX...",
    "message": {
      "kind": "message",
      "message_id": "msg_...",
      "parts": [
        {
          "kind": "text",
          "text": "Found 15 matching segments..."
        },
        {
          "kind": "data",
          "data": {
            "contentType": "application/json",
            "content": {
              "matched_segments": [...],
              "proposed_segments": [...] // Only when Gemini is enabled
            }
          }
        }
      ],
      "role": "agent"
    }
  }
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | No | Enables AI-powered ranking and proposals. If not set, returns deterministic results. |
| `DATABASE_PATH` | No | SQLite database path (default: `./signals.db`) |
| `ALLOWED_ORIGINS` | No | CORS origins for frontend access |

## Database Seeding

The database is automatically created and seeded with 575 sample segments from `sample_data.json` on first startup. No manual intervention required.

## AI Functionality

- **With Gemini**: AI-powered ranking, proposals, and intelligent segment matching
- **Without Gemini**: Deterministic results with clear "AI off" labeling in responses

## CORS Configuration

The server allows all origins by default. For production, set `ALLOWED_ORIGINS` environment variable with comma-separated frontend URLs.

## Logging

The server logs one concise line per request with method, path, status, latency, and AI status (on/off).

## Troubleshooting

### Port 8000 Already in Use (macOS)
```bash
lsof -i :8000 | awk 'NR>1 {print $2}' | xargs kill -9
```

### Database Issues
The database is automatically recreated if corrupted. Delete `signals.db` to reset.

### AI Not Working
Ensure `GEMINI_API_KEY` is set correctly. The system gracefully falls back to deterministic mode if AI is unavailable.

## Frontend Integration

The HarvinAds frontend should:

1. Call `POST /a2a/task` with discovery requests
2. Handle both `matched_segments` and `proposed_segments` in responses
3. Display AI status (on/off) based on response content
4. Use the task schema as defined in the existing repository

## Deployment

See `render.md` for Render deployment instructions.
