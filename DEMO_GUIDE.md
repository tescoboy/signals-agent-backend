# 🎯 Signals Agent Live Demo Guide

Welcome to the Signals Activation Protocol live demo! This guide will walk you through testing the AI-powered signal discovery system.

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

## 💻 Interactive Client Demo (Recommended)

The best way to experience the demo is through the interactive MCP client:

```bash
uv run python client.py
```

This opens a beautiful command-line interface where you can:

- Enter natural language signal queries
- See AI-ranked results in attractive tables
- View custom segment proposals with activation IDs  
- Test the full activation lifecycle

### Example Queries to Try:
- "Luxury automotive signals for BMW and Mercedes buyers"
- "High-income consumer signals for premium brands"
- "Technology enthusiast signals for expensive gadget buyers"
- "Parent shopping signals for children's products"

## 💻 Quick Search Mode

For one-off queries, use the prompt mode:

```bash
uv run python client.py --prompt "luxury automotive targeting"
```

This gives you instant results without the interactive menu.

### Interactive Commands

When you run `uv run python client.py`, you'll see a menu with these commands:

- **discover**: Search for signals with natural language
- **activate**: Activate a segment for a platform  
- **status**: Check deployment status
- **help**: Show command help
- **quit**: Exit the demo

## 🎯 What You'll See

### Real Data
- 56 authentic signal segments from various providers including Peer39
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

1. **Search** for any signal (e.g., "BMW luxury buyer signals")
2. **Note the Custom Segment IDs** in the proposals section (e.g., `custom_1_1234`)
3. **Activate** using that ID - this simulates creating the segment from scratch
4. **Check Status** - custom segments take 120 minutes vs 60 for existing ones

## 🛠️ Technical Details

This demo showcases:
- **MCP Protocol**: Full Model Context Protocol implementation via interactive client
- **FastMCP Framework**: Modern Python MCP server  
- **Pydantic Schemas**: Type-safe request/response validation
- **SQLite Database**: Real signal segment data
- **Google Gemini**: AI-powered ranking and proposals
- **Rich CLI**: Beautiful command-line tables and interface

## 📚 Learn More

- [Protocol Specification](https://github.com/adcontextprotocol/signals-agent/blob/main/README.md)
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
- Open an issue on [GitHub](https://github.com/adcontextprotocol/signals-agent/issues)
- The demo includes realistic sample data, so some queries may return fewer results