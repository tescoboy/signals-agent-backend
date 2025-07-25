# Audience Agent Reference Implementation

This project is a Python-based reference implementation of an Audience Activation Protocol agent as defined in the [Ad Context Protocol](../adcontextprotocol/docs/audience/specification.md). It demonstrates how to build an audience platform that integrates with AI assistants through the Model Context Protocol (MCP).

## 🚀 Try the Live Demo

**Quick Start**: Click the green **"Code"** button above → **"Codespaces"** → **"Create codespace on main"**

The demo will automatically set up with real Peer39 data and AI-powered audience discovery. See [DEMO_GUIDE.md](DEMO_GUIDE.md) for complete instructions.

## Overview

The Audience Agent provides:

- **AI-Powered Discovery**: Uses Google Gemini to intelligently rank audience segments based on natural language queries
- **Smart Match Explanations**: Each result includes AI-generated explanations of why the segment matches your targeting goals
- **Custom Segment Proposals**: AI suggests new custom segments that could be created for better targeting
- **Multi-Platform Support**: Discover audiences across multiple SSPs (Index Exchange, The Trade Desk, OpenX, etc.)
- **Real-Time Activation**: On-demand audience deployment to decisioning platforms
- **Transparent Pricing**: CPM and revenue share models with realistic market pricing

## Agent Types Supported

This reference implementation supports all three audience agent types:

### 1. Private Audience Agent
- Owned by the principal with exclusive access
- No audience costs (workflow orchestration only)
- Only visible to the owning principal

### 2. Marketplace Audience Agent - Public Catalog
- Available to any orchestrator without principal registration
- Standard marketplace pricing
- Platform-wide segments only

### 3. Marketplace Audience Agent - Personalized Catalog
- Requires principal account with the audience agent
- Account-specific segments plus platform-wide segments
- Mixed pricing: negotiated rates and standard rates

## Getting Started

### Option 1: GitHub Codespaces (Recommended)

The fastest way to try the demo:

1. Click **"Code"** → **"Codespaces"** → **"Create codespace on main"**
2. Wait for automatic setup (dependencies install automatically)
3. Get a free Gemini API key at [ai.google.dev](https://ai.google.dev)
4. Configure your API key:
   ```bash
   cp config.json.sample config.json
   # Edit config.json to add your API key
   ```
5. Initialize the database:
   ```bash
   uv run python database.py
   ```
6. Start the web demo:
   ```bash
   uv run python demo_web.py
   # Open the forwarded port 8000 in your browser
   ```

### Option 2: Local Installation

For local development:

```bash
# Install dependencies
pip install uv
uv sync

# Configure API key
cp config.json.sample config.json
# Edit config.json with your Gemini API key from ai.google.dev

# Initialize database
uv run python database.py

# Start MCP server
uv run python main.py
```

## Protocol Implementation

This agent implements the following tools from the Audience Activation Protocol:

- `get_audiences`: Discover audiences based on marketing specifications
- `activate_audience`: Activate audiences for specific platforms/accounts  
- `check_audience_status`: Check deployment status of audiences

## Live Demo

Try the live demo at: **[Live Demo URL - TBD]**

Or run locally:

```bash
# Start web demo
uv run python demo_web.py
# Open http://localhost:8000
```

## Testing

Test the client interactively:

```bash
uv run python client.py
```

Quick search with prompt:

```bash
uv run python client.py --prompt "BMW luxury automotive targeting"
```

Limit results (default is 5):

```bash
uv run python client.py --prompt --limit 10 "BMW luxury automotive targeting"
```

Run the test suite to validate functionality:

```bash
uv run python -m unittest test_main.py
```

## Full Lifecycle Demo

The system now supports the complete audience lifecycle:

1. **Discovery**: Search for audiences with natural language
2. **AI Proposals**: Get custom segment suggestions with unique IDs
3. **Activation**: Activate both existing and custom segments
4. **Status Tracking**: Check deployment progress

Try activating a custom segment:
```bash
uv run python client.py
# Use 'discover' to get custom segment IDs
# Use 'activate' with the custom segment ID
# Use 'status' to check deployment progress
```

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   AI Assistant      │    │   Audience Agent     │    │  Decisioning        │
│   (Orchestrator)    │───▶│   (This Project)     │───▶│  Platform (DSP)     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
        │                            │                            │
        │                            │                            │
        └────────────── Direct Integration Model ──────────────────┘
```

The agent operates within the broader Ad Tech Ecosystem Architecture, enabling direct integration with decisioning platforms while eliminating intermediary reporting complexity.

## License

This project is licensed under the MIT License - see the LICENSE file for details.