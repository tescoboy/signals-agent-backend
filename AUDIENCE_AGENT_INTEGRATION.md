# Audience Agent Integration

This document describes the new audience-agent integration endpoints added to your backend.

## Overview

Your backend now includes endpoints that proxy requests to the audience-agent service at `https://audience-agent.fly.dev`. This allows your frontend to access audience-agent signals without needing to handle the MCP protocol directly.

## New Endpoints

### 1. Get Signals from Audience Agent

**Endpoint**: `POST /audience-agent/signals`

**Description**: Retrieves signals from the audience-agent service using natural language queries.

**Request Body**:
```json
{
  "signal_spec": "luxury automotive targeting",
  "deliver_to": {
    "platforms": "all",
    "countries": ["US"]
  },
  "max_results": 5,
  "principal_id": "optional_principal_id"
}
```

**Response**:
```json
{
  "source": "audience-agent",
  "query": "luxury automotive targeting",
  "timestamp": "2025-08-19T15:30:00Z",
  "signals": [
    {
      "signals_agent_segment_id": "liveramp_...",
      "name": "Luxury Cars",
      "description": "People with interest in Luxury Cars...",
      "data_provider": "LiveRamp (Skydeo)",
      "coverage_percentage": 50.0,
      "pricing": {
        "cpm": 0.0,
        "revenue_share_percentage": 0.0,
        "currency": "USD"
      }
    }
  ],
  "custom_segments": [
    {
      "proposed_name": "Luxury Vehicle Ownership Intent",
      "description": "Targets content indicating...",
      "estimated_coverage_percentage": 1.8,
      "estimated_cpm": 7.0,
      "creation_rationale": "This segment is more precise...",
      "custom_segment_id": "custom_230_5931"
    }
  ],
  "message": "Found 5 signals for 'luxury automotive targeting'...",
  "context_id": "ctx_1755613955_nr7k62",
  "total_signals": 5,
  "total_custom_segments": 3
}
```

### 2. Activate Signal from Audience Agent

**Endpoint**: `POST /audience-agent/activate`

**Description**: Activates a signal from the audience-agent service on a specific platform.

**Request Body**:
```json
{
  "signal_id": "liveramp_scope3-buyerapi_v6yhet5s@01JMJSQJ4529K32T7TQMD1600R.v2.serviceaccounts.liveramp.com_1012272561",
  "platform": "liveramp",
  "account": "your_account_id",
  "context_id": "ctx_1755613955_nr7k62"
}
```

**Response**:
```json
{
  "source": "audience-agent",
  "signal_id": "liveramp_...",
  "platform": "liveramp",
  "status": "activating",
  "message": "Signal 'Luxury Cars' is being activated on liveramp...",
  "platform_segment_id": "liveramp_luxury_cars_your_account",
  "deployed_at": null,
  "activation_duration": 15,
  "timestamp": "2025-08-19T15:30:00Z"
}
```

## Frontend Integration

Your HarvinAds frontend can now call these endpoints to access audience-agent signals:

### Example Frontend Usage

```javascript
// Get signals from audience-agent
const getAudienceAgentSignals = async (query) => {
  const response = await fetch('/audience-agent/signals', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      signal_spec: query,
      deliver_to: {
        platforms: "all",
        countries: ["US"]
      },
      max_results: 5
    })
  });
  
  return await response.json();
};

// Activate a signal from audience-agent
const activateAudienceAgentSignal = async (signalId, platform, account) => {
  const response = await fetch('/audience-agent/activate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      signal_id: signalId,
      platform: platform,
      account: account
    })
  });
  
  return await response.json();
};
```

## Benefits

1. **No MCP Complexity**: Your frontend doesn't need to handle MCP protocol
2. **Unified Interface**: Same API structure as your existing endpoints
3. **Error Handling**: Backend handles connection issues and timeouts
4. **Response Formatting**: Consistent response format for your frontend
5. **Logging**: All requests are logged through your existing logging system

## Testing

Run the test script to verify the integration:

```bash
python test_audience_agent_integration.py
```

Make sure your backend server is running on `localhost:8000` before running the test.

## Error Handling

The endpoints include comprehensive error handling:

- **Connection Errors**: Returns 500 with descriptive error message
- **Invalid Requests**: Returns 400 with validation details
- **Timeout Handling**: 30-second timeout for audience-agent requests
- **Logging**: All errors are logged for debugging

## Deployment

No additional configuration is needed for deployment. The endpoints will work in production as long as:

1. Your backend can reach `https://audience-agent.fly.dev`
2. The `fastmcp` dependency is installed (already included in requirements.txt)

## Next Steps

1. Test the endpoints locally
2. Update your frontend to use the new endpoints
3. Deploy the updated backend
4. Monitor the integration in production
