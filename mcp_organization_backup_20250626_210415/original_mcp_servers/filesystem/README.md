# Filesystem MCP Server

This directory contains the configuration for the Model Context Protocol (MCP) filesystem server from the official MCP servers repository.

## Server Details

- **Server Name**: `github.com/modelcontextprotocol/servers/tree/main/src/filesystem`
- **Repository**: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- **Installation Method**: NPX (Node.js package)
- **Package**: `@modelcontextprotocol/server-filesystem`

## Configuration

The server is configured to provide filesystem operations with access to:
- Current workspace directory: `c:/Users/Ratanshila/Documents/flash loan`

## Available Tools

- **read_file**: Read complete contents of a file
- **read_multiple_files**: Read multiple files simultaneously
- **write_file**: Create new file or overwrite existing
- **edit_file**: Make selective edits using pattern matching
- **create_directory**: Create new directory or ensure it exists
- **list_directory**: List directory contents with [FILE]/[DIR] prefixes
- **move_file**: Move or rename files and directories
- **search_files**: Recursively search for files/directories
- **get_file_info**: Get detailed file/directory metadata
- **list_allowed_directories**: List all accessible directories

## Security

The filesystem server operates within a sandboxed environment and can only access directories explicitly specified in the configuration. This ensures secure file operations within the allowed workspace.

## Installation Status

✅ Configured in `mcp_settings.json`
✅ Configured in `.kilocode/mcp.json`
✅ Directory structure created