# HarvinAds Frontend Integration Guide

This document provides complete instructions for integrating the HarvinAds frontend with the existing Signals Agent backend.

## Overview

The Signals Agent backend is ready to run as-is and provides all the necessary endpoints for the HarvinAds frontend. No modifications to the existing Python code are required.

## Backend Status

✅ **Ready to Run**: All required files are present and validated  
✅ **API Endpoints**: `/health` and `/a2a/task` are implemented  
✅ **Database**: SQLite with 575 sample segments automatically seeded  
✅ **AI Support**: Optional Gemini integration for enhanced functionality  
✅ **CORS**: Configured for frontend access  

## Quick Setup

### 1. Backend Setup

```bash
# Navigate to signals-agent directory
cd signals-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment (optional)
cp env.example .env
# Edit .env to add your GEMINI_API_KEY if desired

# Start the server
python unified_server.py
```

### 2. Verify Backend

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test discovery endpoint
curl -X POST http://localhost:8000/a2a/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "discovery",
    "parameters": {
      "query": "sports enthusiasts"
    },
    "taskId": "test1"
  }'
```

## API Contract

### Discovery Request

```json
{
  "type": "discovery",
  "parameters": {
    "query": "brief text from user",
    "filters": {
      "max_cpm": 15,
      "min_coverage_percentage": 5,
      "provider": "liveramp"
    }
  },
  "taskId": "t1"
}
```

### Discovery Response

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
              "matched_segments": [
                {
                  "audienceID": 58765,
                  "segmentID": 200065,
                  "externalSegmentName": "Sports",
                  "providerID": 17,
                  "dataProvider": {"name": "Peer39", "id": 17}
                }
              ],
              "proposed_segments": [
                {
                  "id": "custom_1",
                  "name": "Premium Sports Enthusiasts",
                  "description": "AI-generated segment combining sports and luxury interests",
                  "estimated_cpm": 12.50,
                  "estimated_coverage": 2.3
                }
              ]
            }
          }
        }
      ],
      "role": "agent"
    }
  }
}
```

## Frontend Integration

### 1. API Client Setup

```javascript
// api.js
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function discoverSignals(query, filters = {}) {
  const response = await fetch(`${BACKEND_URL}/a2a/task`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type: 'discovery',
      parameters: {
        query,
        filters
      },
      taskId: `task_${Date.now()}`
    })
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${BACKEND_URL}/health`);
  return response.json();
}
```

### 2. React Component Example

```jsx
// DiscoveryForm.jsx
import { useState } from 'react';
import { discoverSignals } from './api';

export default function DiscoveryForm() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await discoverSignals(query);
      setResults(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="mb-3">
          <label htmlFor="query" className="form-label">
            Describe your target audience
          </label>
          <input
            type="text"
            className="form-control"
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., sports enthusiasts, luxury car buyers"
            required
          />
        </div>
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Discover Signals'}
        </button>
      </form>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {results && (
        <div className="results">
          <h3>Results</h3>
          {/* Display matched_segments and proposed_segments */}
        </div>
      )}
    </div>
  );
}
```

### 3. Environment Configuration

```bash
# .env.local (Next.js)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Production
NEXT_PUBLIC_BACKEND_URL=https://your-backend.onrender.com
```

## AI Functionality

### With Gemini (AI On)
- Set `GEMINI_API_KEY` environment variable
- Responses include both `matched_segments` and `proposed_segments`
- AI-powered ranking and intelligent segment suggestions

### Without Gemini (AI Off)
- No API key required
- Responses include only `matched_segments`
- Deterministic results with clear "AI off" labeling

## Deployment

### Backend (Render)
1. Follow instructions in `render.md`
2. Set environment variables in Render dashboard
3. Deploy and get the backend URL

### Frontend (Vercel)
1. Set `NEXT_PUBLIC_BACKEND_URL` environment variable
2. Deploy to Vercel
3. Update backend CORS with Vercel URL

## Testing

### Backend Tests
```bash
# Run the setup test
python3 test_setup.py

# Test endpoints manually
curl http://localhost:8000/health
curl -X POST http://localhost:8000/a2a/task -H "Content-Type: application/json" -d '{"type":"discovery","parameters":{"query":"test"},"taskId":"test"}'
```

### Frontend Tests
- Test with both AI on and off modes
- Verify CORS works in production
- Test error handling for network issues
- Validate response parsing

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure `ALLOWED_ORIGINS` includes your frontend URL
2. **AI Not Working**: Check `GEMINI_API_KEY` is set correctly
3. **Database Issues**: Database auto-recreates on startup
4. **Port Conflicts**: Use `lsof -i :8000` to check for conflicts

### Debug Mode

Enable detailed logging by setting `LOG_LEVEL=DEBUG` in environment variables.

## Support

- Backend logs are available in Render dashboard
- Frontend logs are available in Vercel dashboard
- Use the `/health` endpoint to verify backend status
- Check browser network tab for API request details

## Next Steps

1. ✅ Backend is ready and tested
2. 🔄 Deploy backend to Render
3. 🔄 Build and deploy frontend to Vercel
4. 🔄 Test end-to-end integration
5. 🔄 Monitor and optimize performance
