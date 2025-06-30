# Version Control MCP Servers Guide

This guide covers the best **free version control MCP servers** available for your flash loan project.

## 🎯 Recommended MCP Servers

### 1. GitHub Official MCP Server ⭐
- **Repository**: [github/github-mcp-server](https://github.com/github/github-mcp-server)
- **Trust Score**: 8.2/10
- **Cost**: **FREE** 
- **Features**:
  - Complete GitHub API integration
  - Repository management
  - Issue tracking
  - Pull request operations
  - Code security scanning
  - Branch management
  - Commit operations

### 2. Enhanced GitHub MCP Server
- **Repository**: [cyanheads/github-mcp-server](https://github.com/cyanheads/github-mcp-server)
- **Trust Score**: 9.1/10
- **Cost**: **FREE**
- **Features**:
  - TypeScript-based
  - Enhanced AI assistant integration
  - Better error handling
  - Modular architecture

### 3. Filesystem MCP Server (Git Operations)
- **Repository**: [cyanheads/filesystem-mcp-server](https://github.com/cyanheads/filesystem-mcp-server)
- **Trust Score**: 9.1/10
- **Cost**: **FREE**
- **Features**:
  - Local file operations
  - Git command execution
  - Directory traversal
  - File search/replace

## 🚀 Quick Setup

### Prerequisites
- Docker installed
- GitHub Personal Access Token
- VS Code (optional, for integration)

### Setup Commands

```bash
# 1. Pull the GitHub MCP Server
docker pull ghcr.io/github/github-mcp-server

# 2. Run the setup script
python mcp_servers/setup_github_mcp.py

# 3. Test the server
export GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN \
  ghcr.io/github/github-mcp-server \
  --toolsets all
```

## 🔧 Configuration Options

### Available Toolsets
- `repos` - Repository management
- `issues` - Issue tracking  
- `pull_requests` - Pull request operations
- `code_security` - Security scanning
- `experiments` - Beta features
- `all` - All available features

### Example Configurations

#### Basic Configuration
```json
{
  "servers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```

#### Advanced Configuration with Specific Toolsets
```bash
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=your_token \
  -e GITHUB_TOOLSETS="repos,issues,pull_requests,code_security" \
  ghcr.io/github/github-mcp-server
```

#### GitHub Enterprise Configuration
```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token",
    "GITHUB_HOST": "https://your-github-enterprise.com"
  }
}
```

## 🎮 Usage Examples

### Repository Operations
```bash
# List repositories
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools list_repos

# Create a new repository
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools create_repo --name "my-new-repo" --description "My new repository"

# Get repository info
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools get_repo --owner username --repo repository-name
```

### Issue Management
```bash
# List issues
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools list_issues --owner username --repo repository-name

# Create an issue
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools create_issue --owner username --repo repository-name --title "Bug Report" --body "Description of the bug"

# Get specific issue
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools get_issue --owner username --repo repository-name --issue_number 1
```

### Pull Request Operations
```bash
# List pull requests
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools list_pull_requests --owner username --repo repository-name

# Create pull request
mcpcurl --stdio-server-cmd "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN mcp/github" tools create_pull_request --owner username --repo repository-name --title "Feature Update" --head "feature-branch" --base "main"
```

## 🛡️ Security Best Practices

### GitHub Token Management
1. **Create a Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with required scopes:
     - `repo` (for repository access)
     - `issues` (for issue management)
     - `pull_requests` (for PR operations)

2. **Store Token Securely**:
   ```bash
   # Use environment variables
   export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
   
   # Or use a .env file (don't commit this!)
   echo "GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here" > .env
   ```

3. **Token Permissions**:
   - Grant minimal required permissions
   - Regularly rotate tokens
   - Use different tokens for different environments

## 🔍 Troubleshooting

### Common Issues

#### Docker Not Found
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

#### Authentication Errors
```bash
# Verify token is set
echo $GITHUB_PERSONAL_ACCESS_TOKEN

# Test token with GitHub API
curl -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" https://api.github.com/user
```

#### Permission Errors
- Ensure token has required scopes
- Check repository permissions
- Verify organization settings

### Debug Mode
```bash
# Enable verbose logging
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN \
  -e DEBUG=1 \
  ghcr.io/github/github-mcp-server
```

## 🌟 Integration with Your Flash Loan Project

### Recommended Workflow
1. **Repository Management**: Use GitHub MCP for managing your flash loan codebase
2. **Issue Tracking**: Track bugs and feature requests
3. **Pull Requests**: Code review process for changes
4. **Security Scanning**: Monitor for vulnerabilities in dependencies
5. **Branch Management**: Feature branches for development

### Project-Specific Configuration
```json
{
  "flash-loan-github": {
    "command": "docker",
    "args": [
      "run", "-i", "--rm",
      "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
      "-e", "GITHUB_TOOLSETS=repos,issues,pull_requests,code_security",
      "ghcr.io/github/github-mcp-server"
    ],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
    }
  }
}
```

## 📚 Additional Resources

- [GitHub MCP Server Documentation](https://github.com/github/github-mcp-server)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [VS Code MCP Extension](https://marketplace.visualstudio.com/items?itemName=modelcontextprotocol.mcp)
- [GitHub API Documentation](https://docs.github.com/en/rest)

## 🤝 Contributing

To contribute improvements to this guide:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Note**: All mentioned MCP servers are completely free to use. GitHub API rate limits apply based on your token type (authenticated users get higher limits).