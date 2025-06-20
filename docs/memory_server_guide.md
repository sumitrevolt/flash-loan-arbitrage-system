# MCP Memory Server Configuration Guide

## Overview
The MCP Memory Server provides persistent memory capabilities for AI assistants, allowing them to remember information across conversations and sessions.

## Configuration Added

The memory server has been integrated into your Claude MCP configuration:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    }
  }
}
```

## What This Server Provides

### Tools Available:
1. **add_memory** - Store new information in memory
2. **get_memories** - Retrieve stored memories
3. **search_memories** - Search through stored memories
4. **delete_memory** - Remove specific memories

### Resources Available:
- Memory storage and retrieval
- Persistent data across sessions
- Search capabilities

## Usage Examples

### Adding Memory
```
Can you remember that I prefer using TypeScript for new projects?
```

### Retrieving Memory
```
What programming languages do I prefer?
```

### Searching Memory
```
Show me what you remember about my project preferences
```

## Integration with Your Flash Loan System

The memory server can be particularly useful for:

1. **Trading Preferences**: Remember your preferred trading pairs, risk tolerance, etc.
2. **System Configuration**: Store frequently used configuration parameters
3. **Historical Data**: Keep track of successful arbitrage strategies
4. **User Preferences**: Remember UI preferences, notification settings, etc.
5. **Learning from Experience**: Store insights from previous trading sessions

## Installation Requirements

The memory server uses the official MCP memory server package:
- Requires Node.js and npm/npx
- Package: `@modelcontextprotocol/server-memory`
- Uses the `-y` flag to automatically install if not present

## File Locations

- **Main Configuration**: `config/claude_mcp_config.json`
- **Standalone Configuration**: `config/memory_mcp_config.json`
- **This Guide**: `docs/memory_server_guide.md`

## Next Steps

1. Restart Claude Desktop to load the new configuration
2. Test the memory functionality by asking Claude to remember something
3. Integrate memory capabilities into your flash loan and arbitrage systems
4. Consider adding memory persistence to your AI agents

## Technical Notes

- The server runs using npx with automatic package installation
- Memory is persistent across Claude Desktop sessions
- The server integrates with your existing MCP infrastructure
- No additional environment variables required for basic functionality
