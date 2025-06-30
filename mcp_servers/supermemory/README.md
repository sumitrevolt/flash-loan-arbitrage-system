# Supermemory MCP Server Integration

## Overview

The Supermemory MCP Server provides universal memory capabilities across Language Learning Models (LLMs). It enables AI agents to store, retrieve, and manage persistent memories that can be accessed across different sessions and LLM providers.

## Features

- **Universal Memory**: Store and retrieve memories across different LLM sessions
- **Semantic Search**: Find relevant memories using natural language queries
- **Demo Mode**: Works without API key for testing and development
- **Full API Integration**: Complete functionality when connected to Supermemory API

## Installation

### Prerequisites

```bash
pip install mcp httpx
```

### Configuration

The server is configured in `config/unified_mcp_config.json`:

```json
{
  "servers": {
    "github.com/supermemoryai/supermemory-mcp": {
      "name": "github.com/supermemoryai/supermemory-mcp",
      "type": "python",
      "path": "mcp_servers/supermemory/supermemory_mcp_server.py",
      "port": 3021,
      "enabled": true,
      "auto_restart": true,
      "environment_variables": {
        "MCP_SERVER_NAME": "github.com/supermemoryai/supermemory-mcp",
        "PORT": "3021",
        "SUPERMEMORY_API_KEY": "${SUPERMEMORY_API_KEY}"
      }
    }
  }
}
```

## Environment Variables

- `SUPERMEMORY_API_KEY`: Your Supermemory API key (optional for demo mode)

## Available Tools

### 1. add_memory
Store a new memory in the system.

**Parameters:**
- `content` (required): The content to store as a memory
- `title` (optional): Title for the memory
- `tags` (optional): Array of tags for categorization

**Example:**
```json
{
  "content": "Flash loans are uncollateralized loans that must be repaid within the same transaction block.",
  "title": "Flash Loan Definition",
  "tags": ["defi", "ethereum", "arbitrage"]
}
```

### 2. search_memories
Search through stored memories using semantic search.

**Parameters:**
- `query` (required): Search query to find relevant memories
- `limit` (optional): Maximum number of results to return (default: 10)

**Example:**
```json
{
  "query": "flash loan arbitrage",
  "limit": 5
}
```

### 3. get_memory
Retrieve a specific memory by ID.

**Parameters:**
- `memory_id` (required): The ID of the memory to retrieve

### 4. list_memories
List all stored memories with pagination.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Number of results per page (default: 20)

### 5. delete_memory
Delete a specific memory by ID.

**Parameters:**
- `memory_id` (required): The ID of the memory to delete

## Usage Examples

### Basic Memory Storage
```python
# Add a memory
result = await mcp_client.call_tool("add_memory", {
    "content": "Uniswap V3 uses concentrated liquidity to improve capital efficiency",
    "title": "Uniswap V3 Concentrated Liquidity",
    "tags": ["uniswap", "defi", "liquidity"]
})
```

### Memory Search
```python
# Search for relevant memories
result = await mcp_client.call_tool("search_memories", {
    "query": "liquidity mining rewards",
    "limit": 3
})
```

### Memory Management
```python
# List all memories
memories = await mcp_client.call_tool("list_memories", {
    "page": 1,
    "limit": 10
})

# Get specific memory
memory = await mcp_client.call_tool("get_memory", {
    "memory_id": "mem_12345"
})

# Delete memory
result = await mcp_client.call_tool("delete_memory", {
    "memory_id": "mem_12345"
})
```

## Demo Mode

When no API key is provided, the server operates in demo mode:

- Returns simulated responses for all operations
- Useful for testing and development
- No actual data is stored or retrieved
- All tools remain functional with mock data

## Full API Mode

With a valid `SUPERMEMORY_API_KEY`:

- Connects to Supermemory cloud service
- Persistent memory storage
- Advanced semantic search capabilities
- Cross-session memory retrieval
- Professional-grade scalability

## Getting an API Key

1. Visit [Supermemory Console](https://console.supermemory.ai)
2. Create an account or sign in
3. Generate an API key
4. Set the `SUPERMEMORY_API_KEY` environment variable

## Integration with Flash Loan System

The Supermemory MCP server is particularly useful for:

- **Strategy Memory**: Store successful arbitrage strategies
- **Market Insights**: Remember market conditions and patterns
- **Error Learning**: Keep track of failed transactions and lessons learned
- **Configuration History**: Store working configurations and parameters

### Example: Storing Arbitrage Strategy
```python
strategy_memory = {
    "content": """
    Successful arbitrage between Uniswap V2 and Sushiswap:
    - Token: WETH/USDC
    - Price difference: 0.5%
    - Gas cost: 0.02 ETH
    - Profit: 0.1 ETH
    - Block: 18500000
    """,
    "title": "WETH/USDC Arbitrage Strategy",
    "tags": ["arbitrage", "uniswap", "sushiswap", "profitable"]
}
```

## Error Handling

The server includes comprehensive error handling:

- Network connection issues
- API authentication errors
- Invalid parameter validation
- Graceful fallback to demo mode

## Testing

Run the test suite:

```bash
cd mcp_servers/supermemory
python test_supermemory.py
```

## Monitoring

The server provides:
- Health check endpoints
- Detailed logging
- Performance metrics
- Error tracking

## Security

- API keys are handled securely
- No sensitive data logged
- HTTPS connections for API calls
- Input validation on all parameters

## Development

### File Structure
```
mcp_servers/supermemory/
├── supermemory_mcp_server.py    # Main server implementation
├── requirements.txt             # Python dependencies
├── test_supermemory.py         # Test suite
└── README.md                   # This documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

- [Supermemory Documentation](https://docs.supermemory.ai)
- [GitHub Issues](https://github.com/supermemoryai/supermemory-mcp/issues)
- [Community Discord](https://discord.gg/supermemory)

## License

This implementation is part of the Flash Loan Arbitrage System and follows the project's licensing terms.