# Production Deployment Guide

This guide covers the production hardening features implemented for the Signals Agent Backend.

## 🛡️ Production Hardening Features

### 1. Rate Limiting
- **100 requests per minute** per IP address
- Sliding window implementation
- Automatic rate limit headers in responses

### 2. Security Validation
- Input sanitization and validation
- Protection against common attack patterns:
  - XSS (Cross-Site Scripting)
  - SQL Injection
  - Path Traversal
  - Code Injection
- Maximum input length: 1000 characters

### 3. Structured Logging
- JSON-formatted logs with timestamps
- Request tracking with unique IDs
- Performance metrics logging
- Error tracking and reporting

### 4. Monitoring & Metrics
- **Prometheus metrics** on port 8001
- Request count, duration, and error rates
- AI request tracking
- System resource monitoring (CPU, memory)
- Queue size monitoring

### 5. Background Warming
- **Automatic health checks** every 5 minutes
- **Pre-warming** of popular queries
- Keeps Render instance alive to prevent cold starts

### 6. Request Queuing
- Handles traffic spikes gracefully
- Maximum queue size: 100 requests
- Automatic request rejection when overloaded

## 📊 Monitoring Endpoints

### Health Check
```bash
GET /api/monitoring/health
```
Returns system health status with metrics.

### Prometheus Metrics
```bash
GET /api/monitoring/metrics
```
Returns Prometheus-formatted metrics.

### System Statistics
```bash
GET /api/monitoring/stats
```
Returns detailed system statistics.

### Manual Warmup
```bash
GET /api/monitoring/warmup
```
Triggers immediate warmup to keep instance alive.

## 🚀 Deployment Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
PORT=8000

# Optional (for production hardening)
BASE_URL=https://your-app.onrender.com
RENDER_URL=https://your-app.onrender.com
KEEP_ALIVE_INTERVAL=300
```

### Render Configuration

Add these environment variables in your Render dashboard:

1. **GEMINI_API_KEY**: Your Google Gemini API key
2. **BASE_URL**: Your Render app URL
3. **RENDER_URL**: Your Render app URL (for keep-alive script)

### Dependencies

The following packages are automatically installed:

```txt
slowapi>=0.1.9          # Rate limiting
redis>=5.0.0            # Caching (future use)
celery>=5.3.0           # Background tasks (future use)
structlog>=23.2.0       # Structured logging
prometheus-client>=0.19.0  # Metrics
python-multipart>=0.0.6 # File uploads
```

## 🔧 Keep-Alive Script

To prevent Render cold starts, run the keep-alive script:

```bash
# Run locally to keep your Render instance warm
python keep_alive.py https://your-app.onrender.com 300

# Or set environment variables
export RENDER_URL=https://your-app.onrender.com
export KEEP_ALIVE_INTERVAL=300
python keep_alive.py
```

### Automated Keep-Alive

You can run this script on:
- **Your local machine** (when developing)
- **A VPS or server** (for production)
- **GitHub Actions** (automated)
- **Cron job** (scheduled)

## 📈 Performance Monitoring

### Key Metrics to Monitor

1. **Response Times**
   - Target: < 10 seconds for AI requests
   - Target: < 1 second for cached requests

2. **Error Rates**
   - Target: < 5% error rate
   - Monitor: 500 errors, timeouts, rate limit hits

3. **System Resources**
   - Memory usage: < 80%
   - CPU usage: < 70%
   - Queue size: < 50 requests

4. **AI Performance**
   - AI request success rate: > 95%
   - AI response time: < 30 seconds
   - Fallback to text matching: < 10%

### Alerting

Set up alerts for:
- High error rates (> 10%)
- Long response times (> 30 seconds)
- High memory usage (> 90%)
- Queue overflow (> 80 requests)

## 🔒 Security Considerations

### Rate Limiting
- 100 requests per minute per IP
- Automatic blocking of abusive IPs
- Graceful degradation under load

### Input Validation
- All inputs are sanitized
- Maximum length limits enforced
- Suspicious patterns blocked

### Error Handling
- No sensitive information in error messages
- Structured error logging
- Graceful fallbacks

## 🚨 Troubleshooting

### Common Issues

1. **Cold Start Delays**
   - Solution: Use keep-alive script
   - Monitor: `/api/monitoring/warmup` endpoint

2. **Rate Limit Errors**
   - Check: Request frequency
   - Solution: Implement client-side retry logic

3. **AI Timeouts**
   - Monitor: `/api/monitoring/stats`
   - Solution: Check Gemini API status

4. **High Memory Usage**
   - Monitor: System metrics
   - Solution: Restart instance if needed

### Debug Endpoints

```bash
# Basic health check
GET /health

# Detailed system info
GET /api/debug

# Production metrics
GET /api/monitoring/stats

# Prometheus metrics
GET /api/monitoring/metrics
```

## 📝 Log Analysis

### Log Format
All logs are in JSON format for easy parsing:

```json
{
  "timestamp": "2025-08-12T20:30:00.123Z",
  "level": "info",
  "request_id": "abc12345",
  "endpoint": "/api/signals",
  "method": "GET",
  "duration": 8.5,
  "spec": "cars",
  "max_results": 10
}
```

### Key Log Fields
- `request_id`: Unique request identifier
- `endpoint`: API endpoint called
- `method`: HTTP method
- `duration`: Request duration in seconds
- `error`: Error details (if any)

## 🔄 Updates and Maintenance

### Regular Tasks
1. **Monitor metrics** daily
2. **Check logs** for errors
3. **Update dependencies** monthly
4. **Review rate limits** based on usage
5. **Test warmup script** weekly

### Scaling Considerations
- Current setup handles ~100 requests/minute
- For higher traffic, consider:
  - Upgrading Render plan
  - Implementing caching
  - Adding load balancing
  - Using multiple instances

## 📞 Support

For issues with production hardening:
1. Check the monitoring endpoints
2. Review structured logs
3. Monitor Prometheus metrics
4. Test with keep-alive script
5. Contact development team with logs and metrics
