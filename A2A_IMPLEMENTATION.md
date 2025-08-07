# A2A Protocol Implementation

## Overview

This implementation supports the A2A (Agent-to-Agent) protocol alongside the existing MCP protocol, enabling the Signals Agent to communicate with other AI agents using Google's A2A standard.

## Implementation Approach

We provide **two implementations** of A2A support:

### 1. Custom Implementation (`a2a_server.py`)
- Pure Python HTTP server without external dependencies
- Implements A2A protocol concepts directly
- Good for understanding the protocol and quick testing
- May not be 100% protocol-compliant

### 2. Official SDK Implementation (`a2a_official_server.py`)
- Uses the official `a2a-sdk` library
- Ensures full protocol compliance
- Recommended for production use
- Requires: `uv add a2a-sdk` or `pip install a2a-sdk`

## Protocol Compatibility

To ensure full A2A protocol compatibility:

1. **Use the Official SDK**: The `a2a_official_server.py` implementation uses the official A2A SDK, ensuring we follow the protocol specification exactly.

2. **Test with Official Client**: The `test_a2a_official_client.py` uses the official A2A client SDK to validate our implementation.

3. **Agent Card Compliance**: Both implementations provide proper Agent Cards that describe capabilities in the A2A-specified format.

## Running the A2A Server

### With Official SDK (Recommended)
```bash
# Install the official SDK
uv add a2a-sdk

# Run the multi-protocol server
./multi_protocol_server.py --protocols all
```

### Testing with Official Client
```bash
# Test discovery
./test_a2a_official_client.py --query "luxury car buyers"

# Test with custom parameters
./test_a2a_official_client.py \
  --agent-url http://localhost:8080 \
  --query "sports fans" \
  --signal sports_enthusiasts_public \
  --platform the-trade-desk
```

## Key Design Decisions

1. **Protocol Abstraction**: Created a clean abstraction layer that separates protocol handling from business logic.

2. **Context Mapping**: Our context IDs map directly to A2A task IDs, maintaining continuity.

3. **Dual Implementation**: Providing both custom and official SDK implementations allows flexibility.

## A2A Protocol Concepts

### Agent Card
Describes the agent's capabilities, including:
- Agent ID and metadata
- Available capabilities (discovery, activation)
- Input/output schemas for each capability
- Supported protocols and endpoints

### Tasks
The fundamental unit of work in A2A:
- Have unique task IDs
- Progress through states: submitted → in_progress → completed/failed
- Contain input data and produce output messages
- Include metadata for additional context

### Messages
Structured communication format:
- Contain one or more "parts"
- Each part has a content type and content
- Support multiple modalities (JSON, text, media)

## Protocol Differences

| Feature | MCP | A2A |
|---------|-----|-----|
| Transport | STDIO/Socket | HTTP/HTTPS |
| Communication | Synchronous RPC | Task-based async |
| Discovery | Tool listing | Agent Cards |
| State | Stateless | Task lifecycle |
| Format | JSON-RPC | HTTP + JSON |

## Future Enhancements

1. **Dynamic Skill Negotiation**: A2A supports agents negotiating capabilities during runtime.

2. **Multi-Agent Workflows**: Enable complex workflows involving multiple agents.

3. **Security**: Add authentication and authorization per A2A spec.

4. **Streaming**: Implement Server-Sent Events for long-running tasks.

## Validation

To ensure your implementation is A2A-compliant:

1. Use the official A2A SDK
2. Test with the official client library
3. Validate with the A2A Inspector tool
4. Follow the protocol specification at https://github.com/a2aproject/A2A

## References

- [A2A Protocol Specification](https://github.com/a2aproject/A2A)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- [A2A Samples](https://github.com/a2aproject/a2a-samples)