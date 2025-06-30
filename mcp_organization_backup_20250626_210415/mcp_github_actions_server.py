# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
import json
import logging
import os

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import ()
import aiohttp
import requests
"""
GitHub Actions MCP Server
Manages CI/CD pipelines and automated workflows
"""


    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel


# Configure logging

# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("github-actions-mcp")

class GitHubActionsMCPServer:
    def __init__(self):
        self.server = Server("github-actions-mcp")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER", "")
        self.repo_name = os.getenv("GITHUB_REPO_NAME", "")
        self.session = None
        self.base_url = "https://api.github.com"
        
        # Register handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available GitHub Actions resources."""
            return []
                Resource()
                    uri="github://actions/workflows",
                    name="GitHub Actions Workflows",
                    description="List and manage GitHub Actions workflows",
                    mimeType="application/json"
                ),
                Resource()
                    uri="github://actions/runs",
                    name="Workflow Runs",
                    description="Monitor workflow run status and logs",
                    mimeType="application/json"
                ),
                Resource()
                    uri="github://actions/secrets",
                    name="Repository Secrets",
                    description="Manage repository secrets for workflows",
                    mimeType="application/json"
                ),
                Resource()
                    uri="github://actions/artifacts",
                    name="Build Artifacts",
                    description="Access build artifacts from workflow runs",
                    mimeType="application/json"
                
            
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read GitHub Actions resource content."""
            if uri == "github://actions/workflows":
                return await self.get_workflows()
            elif uri == "github://actions/runs":
                return await self.get_workflow_runs()
            elif uri == "github://actions/secrets":
                return await self.get_repository_secrets()
            elif uri == "github://actions/artifacts":
                return await self.get_artifacts()
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available GitHub Actions tools."""
            return []
                Tool()
                    name="trigger_workflow",
                    description="Trigger a GitHub Actions workflow",
                    inputSchema={}
                        "type": "object",
                        "properties": {}
                            "workflow_id": {"type": "string", "description": "Workflow ID or filename"},
                            "ref": {"type": "string", "description": "Git reference (branch, tag, or SHA)"},
                            "inputs": {"type": "object", "description": "Input parameters for the workflow"}
                        },
                        "required": ["workflow_id", "ref"]
                    
                ),
                Tool()
                    name="get_workflow_status",
                    description="Get the status of a specific workflow run",
                    inputSchema={}
                        "type": "object",
                        "properties": {}
                            "run_id": {"type": "integer", "description": "Workflow run ID"}
                        },
                        "required": ["run_id"]
                    
                ),
                Tool()
                    name="cancel_workflow_run",
                    description="Cancel a running workflow",
                    inputSchema={}
                        "type": "object",
                        "properties": {}
                            "run_id": {"type": "integer", "description": "Workflow run ID to cancel"}
                        },
                        "required": ["run_id"]
                    
                ),
                Tool()
                    name="get_workflow_logs",
                    description="Get logs from a workflow run",
                    inputSchema={}
                        "type": "object",
                        "properties": {}
                            "run_id": {"type": "integer", "description": "Workflow run ID"},
                            "job_id": {"type": "integer", "description": "Specific job ID (optional)"}
                        },
                        "required": ["run_id"]
                    
                ),
                Tool()
                    name="create_workflow_dispatch",
                    description="Create a manual workflow dispatch event",
                    inputSchema={}
                        "type": "object",
                        "properties": {}
                            "workflow_id": {"type": "string", "description": "Workflow ID"},
                            "ref": {"type": "string", "description": "Git reference"},
                            "inputs": {"type": "object", "description": "Workflow inputs"}
                        },
                        "required": ["workflow_id", "ref"]
                    
                ),
                Tool()
                    name="update_repository_secret",
                    description="Update a repository secret",
                    inputSchema={}
                        "type": "object",
                        "properties": {}
                            "secret_name": {"type": "string", "description": "Secret name"},
                            "secret_value": {"type": "string", "description": "Secret value"}
                        },
                        "required": ["secret_name", "secret_value"]
                    
                
            
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls for GitHub Actions functionality."""
            try:
                if name == "trigger_workflow":
                    result = await self.trigger_workflow_tool(arguments)
                elif name == "get_workflow_status":
                    result = await self.get_workflow_status_tool(arguments)
                elif name == "cancel_workflow_run":
                    result = await self.cancel_workflow_run_tool(arguments)
                elif name == "get_workflow_logs":
                    result = await self.get_workflow_logs_tool(arguments)
                elif name == "create_workflow_dispatch":
                    result = await self.create_workflow_dispatch_tool(arguments)
                elif name == "update_repository_secret":
                    result = await self.update_repository_secret_tool(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=True, default=str))]
            except Exception as e:
                logger.error(str(f"Error in tool {name}: {str(e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_workflows(self) -> str:
        """Get list of repository workflows."""
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/workflows"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return json.dumps(data, indent=2, ensure_ascii=True, default=str)
                else:
                    return json.dumps({"error": f"Failed to fetch workflows: {response.status}"}, ensure_ascii=True, default=str)
        except Exception as e:
            logger.error(str(f"Error getting workflows: {str(e}")
            return json.dumps({"error": str(e, ensure_ascii=True, default=str)})
    
    async def get_workflow_runs(self) -> str:
        """Get recent workflow runs."""
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return json.dumps(data, indent=2, ensure_ascii=True, default=str)
                else:
                    return json.dumps({"error": f"Failed to fetch workflow runs: {response.status}"}, ensure_ascii=True, default=str)
        except Exception as e:
            logger.error(str(f"Error getting workflow runs: {str(e}")
            return json.dumps({"error": str(e, ensure_ascii=True, default=str)})
    
    async def get_repository_secrets(self) -> str:
        """Get repository secrets (names only for security)."""
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/secrets"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Only return secret names for security
                    secrets = [{"name": secret["name"], "created_at": secret["created_at"]} ]
                              for secret in data.get("secrets", [])
                    return json.dumps({"secrets": secrets}, indent=2, ensure_ascii=True, default=str)
                else:
                    return json.dumps({"error": f"Failed to fetch secrets: {response.status}"}, ensure_ascii=True, default=str)
        except Exception as e:
            logger.error(str(f"Error getting repository secrets: {str(e}")
            return json.dumps({"error": str(e, ensure_ascii=True, default=str)})
    
    async def get_artifacts(self) -> str:
        """Get build artifacts from recent workflow runs."""
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/artifacts"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return json.dumps(data, indent=2, ensure_ascii=True, default=str)
                else:
                    return json.dumps({"error": f"Failed to fetch artifacts: {response.status}"}, ensure_ascii=True, default=str)
        except Exception as e:
            logger.error(str(f"Error getting artifacts: {str(e}")
            return json.dumps({"error": str(e, ensure_ascii=True, default=str)})
    
    async def trigger_workflow_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for triggering workflows."""
        workflow_id = arguments.get("workflow_id")
        ref = arguments.get("ref")
        inputs = arguments.get("inputs", {})
        
        try:
            headers = {}
                "Authorization": f"token {self.github_token}",
                "Content-Type": "application/json"
            
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{workflow_id}/dispatches"
            
            data = {}
                "ref": ref,
                "inputs": inputs
            
            
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 204:
                    return {}
                        "success": True,
                        "message": f"Workflow {workflow_id} triggered successfully",
                        "ref": ref,
                        "inputs": inputs,
                        "timestamp": datetime.now().isoformat()
                    
                else:
                    return {}
                        "success": False,
                        "error": f"Failed to trigger workflow: {response.status}",
                        "timestamp": datetime.now().isoformat()
                    
        except Exception as e:
            logger.error(str(f"Error triggering workflow: {str(e}")
            return {"success": False, "error": str(e)}
    
    async def get_workflow_status_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for getting workflow status."""
        run_id = arguments.get("run_id")
        
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {}
                        "run_id": run_id,
                        "status": data.get("status"),
                        "conclusion": data.get("conclusion"),
                        "workflow_name": data.get("name"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "html_url": data.get("html_url")
                    
                else:
                    return {"error": f"Failed to get workflow status: {response.status}"}
        except Exception as e:
            logger.error(str(f"Error getting workflow status: {str(e}")
            return {"error": str(e)}
    
    async def cancel_workflow_run_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for cancelling workflow runs."""
        run_id = arguments.get("run_id")
        
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/cancel"
            
            async with self.session.post(url, headers=headers) as response:
                if response.status == 202:
                    return {}
                        "success": True,
                        "message": f"Workflow run {run_id} cancelled successfully",
                        "timestamp": datetime.now().isoformat()
                    
                else:
                    return {}
                        "success": False,
                        "error": f"Failed to cancel workflow: {response.status}"
                    
        except Exception as e:
            logger.error(str(f"Error cancelling workflow: {str(e}")
            return {"success": False, "error": str(e)}
    
    async def get_workflow_logs_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for getting workflow logs."""
        run_id = arguments.get("run_id")
        job_id = arguments.get("job_id")
        
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            
            if job_id:
                url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/jobs/{job_id}/logs"
            else:
                url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/logs"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    logs = await response.text()
                    return {}
                        "run_id": run_id,
                        "job_id": job_id,
                        "logs": logs[:5000] + "..." if len(logs) > 5000 else logs,  # Limit log size
                        "full_logs_url": url,
                        "timestamp": datetime.now().isoformat()
                    
                else:
                    return {"error": f"Failed to get workflow logs: {response.status}"}
        except Exception as e:
            logger.error(str(f"Error getting workflow logs: {str(e}")
            return {"error": str(e)}
    
    async def create_workflow_dispatch_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for creating workflow dispatch events."""
        return await self.trigger_workflow_tool(arguments)  # Same implementation
    
    async def update_repository_secret_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for updating repository secrets."""
        secret_name = arguments.get("secret_name")
        secret_value = arguments.get("secret_value")
        
        try:
            # Note: This is a simplified implementation
            # In practice, you'd need to encrypt the secret value using the repository's public key
            headers = {}
                "Authorization": f"token {self.github_token}",
                "Content-Type": "application/json"
            
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/secrets/{secret_name}"
            
            # This is a mock response since actual secret updating requires encryption
            return {}
                "success": True,
                "message": f"Secret {secret_name} would be updated (mock implementation)",
                "secret_name": secret_name,
                "timestamp": datetime.now().isoformat(),
                "note": "Actual implementation requires proper encryption with repository public key"
            
        except Exception as e:
            logger.error(str(f"Error updating repository secret: {str(e}")
            return {"success": False, "error": str(e)}
    
    async def initialize_session(self):
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()

async def main():
    """Main entry point for the GitHub Actions MCP server."""
    server_instance = GitHubActionsMCPServer()
    
    try:
        await server_instance.initialize_session()
        
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run()
                read_stream,
                write_stream,
                InitializationOptions()
                    server_name="github-actions-mcp",
                    server_version="1.0.0",
                    capabilities=server_instance.server.get_capabilities()
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            
    finally:
        await server_instance.cleanup()

if __name__ == "__main__":
    asyncio.run(main())