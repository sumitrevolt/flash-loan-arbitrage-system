
# Online MCP Integration Instructions

## Available Online MCP Servers

### 1. GitHub MCP Server
- **Server Name**: `github.com/modelcontextprotocol/servers/tree/main/src/github`
- **Purpose**: Code repository management, documentation, issue tracking
- **Key Tools**:
  - `search_repositories`: Find relevant repositories
  - `create_or_update_file`: Document opportunities and strategies
  - `create_issue`: Track problems or improvements
  - `create_pull_request`: Submit code changes
  - `get_file_contents`: Read existing documentation

### 2. Upstash Context7 MCP Server  
- **Server Name**: `@upstash/context7-mcp`
- **Purpose**: Library documentation and integration guidance
- **Key Tools**:
  - `resolve-library-id`: Find library documentation IDs
  - `get-library-docs`: Get detailed documentation for libraries

### 3. Context7 Clean MCP Server
- **Server Name**: `context7_clean`
- **Purpose**: Clean documentation search and library information
- **Key Tools**:
  - `search_docs`: Search documentation across libraries
  - `get_library_info`: Get information about specific libraries
  - `health`: Check server health

## Integration Workflow

1. **Discovery Phase**
   - Use GitHub MCP to find existing flash loan implementations
   - Use Context7 to understand DEX integration patterns

2. **Documentation Phase** 
   - Document opportunities using GitHub MCP file creation
   - Query Context7 for integration best practices

3. **Implementation Phase**
   - Use GitHub MCP to manage code changes
   - Use Context7 to verify implementation approaches

4. **Monitoring Phase**
   - Use GitHub MCP for issue tracking
   - Use Context7 for troubleshooting guidance

## Example Usage

```python
# Search for flash loan repositories
await use_mcp_tool(
    server_name="github.com/modelcontextprotocol/servers/tree/main/src/github",
    tool_name="search_repositories", 
    arguments={"query": "flash loan arbitrage", "perPage": 10}
)

# Get Web3.js documentation
await use_mcp_tool(
    server_name="@upstash/context7-mcp",
    tool_name="resolve-library-id",
    arguments={"libraryName": "web3.js"}
)

# Create opportunity documentation
await use_mcp_tool(
    server_name="github.com/modelcontextprotocol/servers/tree/main/src/github", 
    tool_name="create_or_update_file",
    arguments={
        "owner": "YOUR_USERNAME",
        "repo": "flash-loan-bot",
        "path": "opportunities/opportunity.md", 
        "content": "# New Opportunity\nDetails...",
        "message": "Document opportunity",
        "branch": "main"
    }
)
```

## Benefits

- **GitHub Integration**: Automatic documentation, version control, issue tracking
- **Context7 Integration**: Access to comprehensive library documentation
- **No Local Server Management**: Leverage reliable online services
- **Scalable**: Online servers handle the infrastructure
- **Always Updated**: Documentation and repositories are current

## Next Steps

1. Configure your GitHub credentials for write access
2. Test each MCP server connection
3. Implement the workflow in your arbitrage bot
4. Set up automated documentation and monitoring

