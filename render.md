# Render Deployment for Signals Agent Backend

This guide explains how to deploy the Signals Agent backend to Render for the HarvinAds frontend.

## Render Web Service Configuration

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python unified_server.py
```

### Environment Variables

Set these in your Render dashboard:

| Variable | Value | Description |
|----------|-------|-------------|
| `GEMINI_API_KEY` | `your_actual_gemini_key` | Optional: Enables AI functionality |
| `ALLOWED_ORIGINS` | `https://your-frontend-domain.vercel.app` | Required: Frontend CORS origin |
| `DATABASE_PATH` | `/opt/render/project/src/signals.db` | Optional: Database path for Render |

### Port Configuration

The application runs on port 8000 by default. Render will automatically assign the `PORT` environment variable, which the application will use.

### Health Check

Render will use the `/health` endpoint for health checks:
- **URL**: `/health`
- **Expected Response**: `{"status": "healthy", ...}`

## Deployment Steps

1. **Connect Repository**
   - Link your GitHub repository to Render
   - Select the `signals-agent` directory as the root

2. **Configure Service**
   - **Name**: `harvinads-backend` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python unified_server.py`

3. **Set Environment Variables**
   - Add the environment variables listed above
   - Ensure `ALLOWED_ORIGINS` includes your Vercel frontend URL

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

## Post-Deployment

### Get Your Backend URL

After deployment, Render will provide a URL like:
```
https://your-service-name.onrender.com
```

### Update Frontend Configuration

Update your HarvinAds frontend to use the Render backend URL:

```javascript
const BACKEND_URL = 'https://your-service-name.onrender.com';
```

### Test the Deployment

```bash
# Test health endpoint
curl https://your-service-name.onrender.com/health

# Test discovery endpoint
curl -X POST https://your-service-name.onrender.com/a2a/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "discovery",
    "parameters": {
      "query": "sports enthusiasts"
    },
    "taskId": "test1"
  }'
```

## Important Notes

### Database Persistence

- The SQLite database will be recreated on each deployment
- Sample data is automatically loaded from `sample_data.json`
- For production, consider using a managed database service

### CORS Configuration

- Set `ALLOWED_ORIGINS` to your exact Vercel frontend URL
- Include both development and production URLs if needed
- Example: `https://harvinads.vercel.app,http://localhost:3000`

### AI Functionality

- Set `GEMINI_API_KEY` only if you want AI-powered features
- The system works without it (deterministic mode)
- Test both modes to ensure frontend handles both responses

### Monitoring

- Use Render's built-in logs to monitor the application
- Check the `/health` endpoint for service status
- Monitor request logs for API usage

## Troubleshooting

### Build Failures
- Ensure all dependencies are in `requirements.txt`
- Check Python version compatibility (3.10+)

### Runtime Errors
- Check Render logs for detailed error messages
- Verify environment variables are set correctly
- Ensure the application starts without errors locally first

### CORS Issues
- Verify `ALLOWED_ORIGINS` includes your frontend URL exactly
- Check that the frontend is making requests to the correct backend URL

### Database Issues
- The database is automatically created and seeded
- Check logs for any database initialization errors
- Verify `sample_data.json` is present in the repository
