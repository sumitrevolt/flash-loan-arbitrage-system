# GitHub Copilot MCP Memory Server Setup Guide

## Overview
This guide explains how to set up the MCP Memory Server with GitHub Copilot in VS Code. The memory server allows GitHub Copilot to remember information across chat sessions.

## Configuration Files Created

### 1. VS Code Settings with MCP Memory Server
**File**: `config/settings.json` and `config/github_copilot_settings.json`

```json
{
  "mcp.servers": {
    "memory": {
      "command": "C:\\Program Files\\nodejs\\npx.cmd",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    }
  }
}
```

## Installation Steps

### 1. Copy Settings to VS Code
You need to copy the settings to your VS Code user settings:

**Windows Path**: `%APPDATA%\Code\User\settings.json`

Or use VS Code:
1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type "Preferences: Open Settings (JSON)"
4. Add the MCP configuration to your settings

### 2. Alternative: Workspace Settings
You can also add this to your workspace settings:
- Create `.vscode/settings.json` in your project root
- Copy the MCP configuration there

### 3. Reload VS Code
After adding the configuration:
1. Close VS Code completely
2. Reopen VS Code
3. Open your project

## VS Code Workspace Configuration

Let me create a proper VS Code workspace configuration for you:

**File**: `.vscode/settings.json`

```json
{
  "mcp.servers": {
    "memory": {
      "command": "C:\\Program Files\\nodejs\\npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

## Testing the Setup

### 1. Check MCP Server Status
In VS Code:
1. Open Command Palette (`Ctrl+Shift+P`)
2. Look for MCP-related commands
3. Check the Output panel for MCP logs

### 2. Test with GitHub Copilot Chat
1. Open GitHub Copilot Chat
2. Try asking: "Can you remember that I prefer TypeScript for new projects?"
3. Later ask: "What programming language do I prefer?"

## Memory Server Capabilities

The memory server provides these tools to GitHub Copilot:

### Tools Available:
- **add_memory**: Store information
- **get_memories**: Retrieve stored information  
- **search_memories**: Search through memories
- **delete_memory**: Remove specific memories

### Use Cases for Flash Loan Project:
1. **Trading Preferences**: Remember your preferred DEXs, tokens, etc.
2. **Configuration Settings**: Store frequently used parameters
3. **Successful Strategies**: Remember profitable arbitrage patterns
4. **Error Solutions**: Remember fixes for common issues
5. **Project Context**: Maintain context about your system architecture

## Troubleshooting

### If Memory Server Doesn't Start:
1. Check Node.js installation: `node --version`
2. Check npx availability: `"C:\Program Files\nodejs\npx.cmd" --version`
3. Test package: `"C:\Program Files\nodejs\npx.cmd" -y @modelcontextprotocol/server-memory --help`

### If GitHub Copilot Doesn't Recognize Memory:
1. Restart VS Code completely
2. Check VS Code Output panel for MCP errors
3. Verify settings.json syntax is valid JSON
4. Try workspace settings instead of user settings

### Common Issues:
1. **Path Issues**: Use full path to npx.cmd as shown
2. **JSON Syntax**: Ensure proper JSON formatting
3. **Permissions**: Run VS Code as administrator if needed
4. **Node.js Version**: Requires Node.js 16+ for MCP support

## Files Created:
- `config/settings.json` - Updated with MCP configuration
- `config/github_copilot_settings.json` - Complete GitHub Copilot settings
- `docs/github_copilot_mcp_guide.md` - This guide
- `test_memory_server.py` - Test script for validation

## Next Steps:
1. Copy the MCP configuration to your VS Code settings
2. Restart VS Code
3. Test the memory functionality with GitHub Copilot
4. Start using memory for your flash loan development context
