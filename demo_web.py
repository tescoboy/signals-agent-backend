#!/usr/bin/env python3
"""
Web demo interface for the Audience Activation Protocol.
Provides a simple HTML interface for testing the audience discovery functionality.
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from main import get_audiences, activate_audience, check_audience_status
from schemas import DeliverySpecification, AudienceFilters

app = FastAPI(title="Audience Agent Demo", description="Interactive demo of the Audience Activation Protocol")

# HTML template for the demo
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Audience Agent Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; margin-bottom: 10px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        .results { margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 4px; }
        .audience-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 4px; background: white; }
        .custom-proposal { border: 1px solid #ffa500; margin: 10px 0; padding: 15px; border-radius: 4px; background: #fff8e1; }
        .error { color: red; padding: 10px; background: #ffebee; border-radius: 4px; }
        .success { color: green; padding: 10px; background: #e8f5e8; border-radius: 4px; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin: 30px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Audience Activation Protocol Demo</h1>
        <p>AI-powered audience discovery with real Peer39 data from Index Exchange</p>
    </div>

    <div class="section">
        <h2>Discover Audiences</h2>
        <form method="post" action="/search">
            <div class="form-group">
                <label for="audience_spec">Describe your target audience:</label>
                <textarea name="audience_spec" id="audience_spec" rows="3" placeholder="e.g., Luxury automotive buyers interested in BMW and Mercedes">{{ audience_spec or '' }}</textarea>
            </div>
            
            <div class="form-group">
                <label for="max_results">Number of results (1-20):</label>
                <input type="number" name="max_results" id="max_results" min="1" max="20" value="{{ max_results or 5 }}">
            </div>
            
            <div class="form-group">
                <label for="max_cpm">Maximum CPM (optional):</label>
                <input type="number" name="max_cpm" id="max_cpm" step="0.01" placeholder="e.g., 5.00">
            </div>
            
            <button type="submit">🔍 Search Audiences</button>
        </form>
    </div>

    {% if error %}
    <div class="error">
        <strong>Error:</strong> {{ error }}
    </div>
    {% endif %}

    {% if results %}
    <div class="results">
        <h2>🎯 Found {{ results.audiences|length }} Audiences</h2>
        
        {% for audience in results.audiences %}
        <div class="audience-item">
            <h3>{{ audience.name }}</h3>
            <p><strong>Provider:</strong> {{ audience.data_provider }}</p>
            <p><strong>Coverage:</strong> {{ "%.1f"|format(audience.coverage_percentage) }}%</p>
            <p><strong>Type:</strong> {{ audience.audience_type }}</p>
            <p><strong>CPM:</strong> ${{ "%.2f"|format(audience.pricing.cpm) if audience.pricing.cpm else "N/A" }}</p>
            <p><strong>Description:</strong> {{ audience.description }}</p>
            
            {% if audience.match_reason %}
            <p style="font-style: italic; color: #666;"><strong>AI Match:</strong> {{ audience.match_reason }}</p>
            {% endif %}
            
            <p><strong>Platforms:</strong></p>
            <ul>
            {% for deployment in audience.deployments %}
                <li>{{ deployment.platform }}: 
                    {% if deployment.is_live %}
                        🟢 Live
                    {% else %}
                        🟡 Needs Activation
                    {% endif %}
                </li>
            {% endfor %}
            </ul>
            
            <form method="post" action="/activate" style="display: inline;">
                <input type="hidden" name="segment_id" value="{{ audience.audience_agent_segment_id }}">
                <button type="submit">🚀 Activate</button>
            </form>
        </div>
        {% endfor %}
        
        {% if results.custom_segment_proposals %}
        <h2>💡 Custom Segment Proposals</h2>
        <p style="color: #666;">AI-suggested segments that could be created for better targeting:</p>
        
        {% for proposal in results.custom_segment_proposals %}
        <div class="custom-proposal">
            <h3>{{ proposal.proposed_name }}</h3>
            <p><strong>ID:</strong> <code>{{ proposal.custom_segment_id }}</code></p>
            <p><strong>Target:</strong> {{ proposal.target_audience }}</p>
            <p><strong>Coverage:</strong> {{ "%.1f"|format(proposal.estimated_coverage_percentage) }}%</p>
            <p><strong>Est. CPM:</strong> ${{ "%.2f"|format(proposal.estimated_cpm) }}</p>
            <p style="font-style: italic;">{{ proposal.creation_rationale }}</p>
            
            <form method="post" action="/activate" style="display: inline;">
                <input type="hidden" name="segment_id" value="{{ proposal.custom_segment_id }}">
                <button type="submit">🛠️ Create & Activate</button>
            </form>
        </div>
        {% endfor %}
        {% endif %}
    </div>
    {% endif %}

    <div class="section">
        <h2>About This Demo</h2>
        <p>This demo showcases the <a href="https://github.com/adcontextprotocol/audience-agent">Audience Activation Protocol</a> reference implementation:</p>
        <ul>
            <li>🤖 <strong>AI-Powered Discovery:</strong> Uses Google Gemini to intelligently rank audience segments</li>
            <li>📊 <strong>Real Data:</strong> Contains actual Peer39 segments from Index Exchange</li>
            <li>🎯 <strong>Smart Matching:</strong> Natural language queries with relevance explanations</li>
            <li>💡 <strong>Custom Segments:</strong> AI proposes new segments for better targeting</li>
            <li>🚀 <strong>Live Activation:</strong> Simulate audience deployment to DSPs</li>
        </ul>
        <p><em>Note: This is a demonstration system. Activations are simulated and no real ad serving occurs.</em></p>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main demo page."""
    from jinja2 import Template
    template = Template(HTML_TEMPLATE)
    return template.render()

@app.post("/search", response_class=HTMLResponse)
async def search_audiences(
    request: Request,
    audience_spec: str = Form(...),
    max_results: int = Form(5),
    max_cpm: Optional[float] = Form(None)
):
    """Handle audience search requests."""
    from jinja2 import Template
    template = Template(HTML_TEMPLATE)
    
    try:
        # Build filters
        filters = None
        if max_cpm:
            filters = AudienceFilters(max_cpm=max_cpm)
        
        # Build delivery specification
        delivery_spec = DeliverySpecification(
            platforms="all",
            countries=["US"]
        )
        
        # Call the search function
        results = get_audiences(
            audience_spec=audience_spec,
            deliver_to=delivery_spec,
            filters=filters,
            max_results=max_results
        )
        
        # Convert to dict for template
        results_dict = results.model_dump() if hasattr(results, 'model_dump') else results
        
        return template.render(
            audience_spec=audience_spec,
            max_results=max_results,
            results=results_dict
        )
        
    except Exception as e:
        return template.render(
            audience_spec=audience_spec,
            max_results=max_results,
            error=str(e)
        )

@app.post("/activate", response_class=HTMLResponse)
async def activate_segment(
    request: Request,
    segment_id: str = Form(...)
):
    """Handle activation requests."""
    from jinja2 import Template
    template = Template(HTML_TEMPLATE)
    
    try:
        # Activate on Index Exchange as example
        result = activate_audience(
            audience_agent_segment_id=segment_id,
            platform="index-exchange"
        )
        
        success_msg = f"✅ Activation initiated! Platform Segment ID: {result.decisioning_platform_segment_id}"
        success_msg += f" (Est. {result.estimated_activation_duration_minutes} minutes)"
        
        return template.render(success=success_msg)
        
    except Exception as e:
        return template.render(error=f"Activation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🎯 Starting Audience Agent Web Demo")
    print("📍 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)