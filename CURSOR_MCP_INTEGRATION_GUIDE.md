# Cursor MCP Integration Guide

This guide explains how to integrate the Context7 MCP server with Cursor IDE.

## Overview

The Context7 MCP server provides enhanced documentation lookup, context management, and AI-powered code assistance directly within Cursor IDE.

## Prerequisites

1. **Cursor IDE**: Latest version installed
2. **Python**: 3.8 or higher
3. **Dependencies**: 
   ```bash
   pip install requests asyncio
   ```

## Configuration Files

### 1. Main MCP Configuration (`.kilocode/mcp.json`)

The Context7 MCP server is already configured in your `.kilocode/mcp.json` file:

```json
{
  "context7-mcp-server": {
    "command": "python",
    "args": ["mcp_servers/context7_mcp_server.py"],
    "disabled": false,
    "autoApprove": [],
    "alwaysAllow": [
      "search_docs",
      "get_library_info",
      "get_context_suggestions",
      "analyze_code_context",
      "health_check",
      "register_with_coordinator"
    ]
  }
}
```

### 2. Cursor-Specific Configuration (`cursor_mcp_config.json`)

A dedicated Cursor configuration file is available with optimized settings:

```json
{
  "mcpServers": {
    "context7-mcp-server": {
      "command": "python",
      "args": ["mcp_servers/context7_mcp_server.py"],
      "disabled": false,
      "autoApprove": [
        "search_docs",
        "get_library_info",
        "get_context_suggestions",
        "analyze_code_context",
        "health_check"
      ],
      "alwaysAllow": [
        "search_docs",
        "get_library_info",
        "get_context_suggestions",
        "analyze_code_context",
        "health_check",
        "register_with_coordinator"
      ]
    }
  }
}
```

## Installation Steps

### Step 1: Start the Context7 MCP Server

#### Windows
```cmd
cursor_start_context7_mcp.bat
```

#### Linux/Mac
```bash
chmod +x cursor_start_context7_mcp.sh
./cursor_start_context7_mcp.sh
```

### Step 2: Configure Cursor IDE

1. **Open Cursor IDE**
2. **Go to Settings** (Ctrl/Cmd + ,)
3. **Search for "MCP"** in the settings
4. **Add MCP Configuration**:
   - Click "Add MCP Server"
   - Name: `context7-mcp-server`
   - Command: `python`
   - Arguments: `["mcp_servers/context7_mcp_server.py"]`
   - Working Directory: Your project root

### Step 3: Verify Integration

1. **Restart Cursor IDE**
2. **Open Command Palette** (Ctrl/Cmd + Shift + P)
3. **Type "MCP"** to see available MCP commands
4. **Test the integration** by using the Context7 tools

## Available Tools in Cursor

### 1. Documentation Search
- **Tool**: `search_docs`
- **Usage**: Search for library/framework documentation
- **Example**: Search for "asyncio" in Python documentation

### 2. Library Information
- **Tool**: `get_library_info`
- **Usage**: Get comprehensive library details
- **Example**: Get information about "requests" library

### 3. Context Suggestions
- **Tool**: `get_context_suggestions`
- **Usage**: Get AI-powered code suggestions
- **Example**: Get suggestions for async code patterns

### 4. Code Analysis
- **Tool**: `analyze_code_context`
- **Usage**: Analyze code structure and provide insights
- **Example**: Analyze current file for imports and functions

### 5. Health Check
- **Tool**: `health_check`
- **Usage**: Check server status
- **Example**: Verify MCP server is running

## Using Context7 MCP in Cursor

### Method 1: Command Palette
1. Press `Ctrl/Cmd + Shift + P`
2. Type the tool name (e.g., "search_docs")
3. Select the tool and provide parameters

### Method 2: Chat Interface
1. Open Cursor's chat interface
2. Ask questions like:
   - "Search documentation for asyncio"
   - "Get information about the requests library"
   - "Analyze this code and provide suggestions"

### Method 3: Direct Tool Calls
Use the MCP tools directly in your workflow:
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {
      "library": "python",
      "query": "asyncio"
    }
  }
}
```

## Integration Features

### 1. Documentation Integration
- **Real-time Documentation**: Get instant access to library documentation
- **Context-Aware Search**: Search based on your current code context
- **Version-Specific Info**: Get documentation for specific library versions

### 2. Code Analysis
- **Import Analysis**: Analyze imports and dependencies
- **Function Discovery**: Find relevant functions and classes
- **Code Metrics**: Get complexity and maintainability insights

### 3. AI-Powered Suggestions
- **Best Practices**: Get coding best practices for your language
- **Code Examples**: Receive relevant code examples
- **Troubleshooting**: Get help with common issues

### 4. Flash Loan System Integration
- **DeFi Documentation**: Access DeFi library documentation
- **Smart Contract Analysis**: Analyze Solidity code
- **Blockchain Libraries**: Get info about Web3 libraries

## Troubleshooting

### Common Issues

1. **Server Won't Start**
   - Check Python version: `python --version`
   - Verify dependencies: `pip list | grep requests`
   - Check file permissions

2. **Cursor Can't Connect**
   - Verify server is running on port 8007
   - Check firewall settings
   - Restart Cursor IDE

3. **Tools Not Available**
   - Check MCP configuration in Cursor settings
   - Verify server registration
   - Check server logs in `logs/context7_mcp_server.log`

### Debug Mode

Enable debug logging by modifying the server:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Logs

Check server logs at:
- Console output
- `logs/context7_mcp_server.log`

## Advanced Configuration

### Custom Port
Change the default port by setting environment variable:
```bash
export MCP_PORT=8008
```

### Custom Coordinator
Set custom coordinator URL:
```bash
export MCP_COORDINATOR_URL=http://localhost:9001
```

### Auto-Approval
Configure auto-approval for specific tools in `cursor_mcp_config.json`:
```json
"autoApprove": [
  "search_docs",
  "get_library_info"
]
```

## Performance Optimization

### Caching
The server includes built-in caching for:
- Documentation search results
- Library information
- Code analysis results

### Connection Pooling
The server maintains connection pools for:
- Coordinator communication
- External API calls

## Security Considerations

### Permissions
- Tools are configured with appropriate permissions
- Sensitive operations require explicit approval
- File system access is restricted to project directory

### Network Security
- Server only accepts local connections by default
- Coordinator communication uses HTTPS
- No sensitive data is logged

## Updates and Maintenance

### Updating the Server
1. Stop the current server
2. Update the Python files
3. Restart the server
4. Verify functionality

### Monitoring
- Check server health regularly
- Monitor log files for errors
- Verify coordinator connectivity

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs
3. Test with the provided test script
4. Check the main README for additional information

## Conclusion

The Context7 MCP server provides powerful documentation and context management capabilities directly within Cursor IDE. With proper configuration and regular maintenance, it will significantly enhance your development workflow. 