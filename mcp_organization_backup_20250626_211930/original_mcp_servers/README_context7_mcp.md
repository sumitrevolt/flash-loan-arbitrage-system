# Context7 MCP Server

A comprehensive Model Context Protocol (MCP) server for documentation lookup, context management, and AI-powered code assistance.

## Features

- **Documentation Search**: Search documentation for libraries and frameworks
- **Library Information**: Get comprehensive information about libraries
- **Context Suggestions**: AI-powered suggestions for code and documentation
- **Code Analysis**: Analyze code and provide contextual information
- **Health Monitoring**: Server health checks and status monitoring
- **Coordinator Integration**: Automatic registration with MCP coordinator

## Tools Available

### 1. search_docs
Search documentation for a library or framework.

**Parameters:**
- `library` (string, required): Library or framework name to search
- `query` (string, required): Search query for documentation
- `version` (string, optional): Optional version specification

**Example:**
```json
{
  "library": "python",
  "query": "asyncio",
  "version": "3.11"
}
```

### 2. get_library_info
Get comprehensive information about a library or framework.

**Parameters:**
- `library` (string, required): Library or framework name
- `include_examples` (boolean, optional): Include code examples in response

**Example:**
```json
{
  "library": "requests",
  "include_examples": true
}
```

### 3. get_context_suggestions
Get AI-powered context suggestions for code or documentation.

**Parameters:**
- `code_snippet` (string, required): Code snippet to analyze
- `language` (string, required): Programming language
- `context_type` (string, optional): Type of context to provide (documentation, examples, best_practices, troubleshooting)

**Example:**
```json
{
  "code_snippet": "import asyncio\n\nasync def main():\n    await asyncio.sleep(1)",
  "language": "python",
  "context_type": "best_practices"
}
```

### 4. analyze_code_context
Analyze code and provide contextual information.

**Parameters:**
- `file_path` (string, required): Path to the file to analyze
- `line_number` (integer, optional): Specific line number to focus on
- `analysis_type` (string, optional): Type of analysis to perform (imports, functions, classes, dependencies)

**Example:**
```json
{
  "file_path": "src/main.py",
  "line_number": 42,
  "analysis_type": "functions"
}
```

### 5. health_check
Check server health and status.

**Parameters:** None

### 6. register_with_coordinator
Register this server with the MCP coordinator.

**Parameters:**
- `coordinator_url` (string, optional): URL of the coordinator
- `capabilities` (array, optional): Server capabilities

## Installation

1. Ensure you have Python 3.8+ installed
2. Install required dependencies:
   ```bash
   pip install requests asyncio
   ```

## Usage

### Starting the Server

#### Windows
```cmd
mcp_servers\start_context7_mcp.bat
```

#### Linux/Mac
```bash
chmod +x mcp_servers/start_context7_mcp.sh
./mcp_servers/start_context7_mcp.sh
```

#### Manual Start
```bash
export MCP_PORT=8007
export MCP_COORDINATOR_URL=http://localhost:9000
python mcp_servers/context7_mcp_server.py
```

### Testing the Server

Run the test script to verify functionality:
```bash
python mcp_servers/test_context7_mcp.py
```

## Configuration

### Environment Variables

- `MCP_PORT`: Port for the MCP server (default: 8007)
- `MCP_COORDINATOR_URL`: URL of the MCP coordinator (default: http://localhost:9000)

### MCP Configuration

The server is configured in `.kilocode/mcp.json`:

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

## Architecture

The Context7 MCP Server follows the standard MCP protocol and includes:

- **Message Handler**: Processes incoming MCP messages
- **Tool Registry**: Manages available tools and their schemas
- **Documentation Cache**: Caches search results for performance
- **Coordinator Integration**: Automatic registration and heartbeat
- **Error Handling**: Comprehensive error handling and logging

## Logging

Logs are written to:
- Console (stderr)
- File: `logs/context7_mcp_server.log`

## Integration with Flash Loan System

The Context7 MCP Server integrates with the flash loan system by:

1. **Documentation Support**: Providing documentation for DeFi libraries and frameworks
2. **Code Analysis**: Analyzing smart contracts and DeFi code
3. **Context Suggestions**: Offering suggestions for DeFi development patterns
4. **Library Information**: Providing information about blockchain and DeFi libraries

## Development

### Adding New Tools

To add a new tool:

1. Add tool definition to `_setup_tools()` method
2. Add tool handler method (e.g., `_new_tool_name()`)
3. Add tool call in `call_tool()` method
4. Update capabilities list in `_get_default_capabilities()`

### Extending Functionality

The server is designed to be easily extensible:

- Add new documentation sources
- Integrate with external APIs
- Add more sophisticated code analysis
- Implement caching strategies

## Troubleshooting

### Common Issues

1. **Server won't start**: Check Python version and dependencies
2. **Connection refused**: Verify coordinator URL and port
3. **Tool not found**: Check tool name and parameters
4. **JSON parse errors**: Verify message format

### Debug Mode

Enable debug logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is part of the Flash Loan System and follows the same license terms. 