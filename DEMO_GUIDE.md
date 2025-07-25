# 🎯 Audience Agent Live Demo Guide

Welcome to the Audience Activation Protocol live demo! This guide will walk you through testing the AI-powered audience discovery system.

## 🚀 Quick Start (GitHub Codespaces)

1. **Launch Demo**: Click the green "Code" button → "Codespaces" → "Create codespace on main"
2. **Wait for Setup**: The environment will automatically install dependencies (~2 minutes)
3. **Add API Key**: Once ready, run:
   ```bash
   cp config.json.sample config.json
   ```
   Then edit `config.json` and replace `"your-gemini-api-key-here"` with a real Gemini API key from [ai.google.dev](https://ai.google.dev)

4. **Initialize Database**:
   ```bash
   uv run python database.py
   ```

## 🌐 Web Demo (Recommended)

Start the web interface for the easiest experience:

```bash
uv run python demo_web.py
```

Then click the "Ports" tab in VS Code and open the forwarded port 8000. You'll see a web form where you can:

- Enter natural language audience queries
- See AI-ranked results with explanations  
- View custom segment proposals with activation IDs
- Test one-click activation simulation

### Example Queries to Try:
- "Luxury automotive buyers interested in BMW and Mercedes"
- "High-income consumers interested in premium brands"
- "Technology enthusiasts who buy expensive gadgets"
- "Parents shopping for children's products"

## 💻 Command Line Demo

For developers who prefer the terminal:

```bash
uv run python client.py
```

This opens an interactive client where you can:

### 1. Discover Audiences
```
Command: discover
Query: "luxury automotive targeting"
```

### 2. Activate Segments
```
Command: activate  
Segment ID: [copy from discovery results or custom proposals]
Platform: index-exchange
```

### 3. Check Status
```
Command: status
Segment ID: [same ID you activated]
Platform: index-exchange
```

## 🎯 What You'll See

### Real Data
- 56 authentic Peer39 audience segments from Index Exchange
- Realistic CPM pricing ($0.50 - $8.50 based on segment specificity)
- 6 major SSP platforms (Index Exchange, The Trade Desk, OpenX, etc.)

### AI Features
- **Smart Ranking**: Gemini AI ranks segments by relevance to your query
- **Match Explanations**: Each result includes why it matches your request
- **Custom Proposals**: AI suggests new segments that could be created

### Full Lifecycle
- **Discovery**: Find existing segments across multiple platforms
- **Custom Creation**: AI proposes new segments with unique IDs
- **Activation**: Deploy segments to decisioning platforms (simulated)
- **Status Tracking**: Monitor deployment progress with realistic timing

## 🔧 Testing Custom Segments

The most interesting feature is custom segment creation:

1. **Search** for any audience (e.g., "BMW luxury buyers")
2. **Note the Custom Segment IDs** in the proposals section (e.g., `custom_1_1234`)
3. **Activate** using that ID - this simulates creating the segment from scratch
4. **Check Status** - custom segments take 120 minutes vs 60 for existing ones

## 🛠️ Technical Details

This demo showcases:
- **MCP Protocol**: Full Model Context Protocol implementation
- **FastMCP Framework**: Modern Python MCP server
- **Pydantic Schemas**: Type-safe request/response validation
- **SQLite Database**: Real audience segment data
- **Google Gemini**: AI-powered ranking and proposals
- **Rich CLI**: Beautiful command-line interface

## 📚 Learn More

- [Protocol Specification](https://github.com/adcontextprotocol/audience-agent/blob/main/README.md)
- [Ad Context Protocol](https://github.com/adcontextprotocol)
- [Model Context Protocol](https://modelcontextprotocol.io)

## 🆘 Troubleshooting

**No results found?** 
- Check your Gemini API key in `config.json`
- Try simpler queries like "automotive" or "technology"

**Codespace not starting?**
- Refresh the page and try again
- Check if you have Codespaces enabled on your GitHub account

**Need help?**
- Open an issue on [GitHub](https://github.com/adcontextprotocol/audience-agent/issues)
- The demo includes realistic sample data, so some queries may return fewer results