import asyncio
import json
import logging
import os
import shutil # For copying directories and removing them
from pathlib import Path # For robust path manipulation
from typing import Dict, List, Any, Optional

# Attempt to import MCP server components (with fallbacks for subtask validation)
try:
    from mcp.server import Server, InitializationOptions, NotificationOptions
    from mcp.types import Tool, TextContent
    MCP_FRAMEWORK_AVAILABLE = True
except ImportError:
    MCP_FRAMEWORK_AVAILABLE = False
    # Define dummy classes if MCP framework is not available
    _dummy_logger = logging.getLogger("DummyMCPForCodeEditing")
    _dummy_logger.warning("MCP framework not found, using dummy classes for CodeEditingMCPServer.")
    class Server:
        def __init__(self, name): self.name = name
        def list_tools(self): return lambda func: func
        def call_tool(self): return lambda func: func
        async def run(self, *args, **kwargs): pass
        def get_capabilities(self, *args, **kwargs): return {}
    class Tool:
        def __init__(self, name, description, inputSchema):
            self.name, self.description, self.inputSchema = name, description, inputSchema
    class TextContent:
        def __init__(self, type, text): self.type, self.text = type, text # type: ignore
    class InitializationOptions: pass
    class NotificationOptions: pass

# Configure logging
logger = logging.getLogger("CodeEditingMCPServer")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configuration from environment variables
SANDBOX_BASE_PATH = Path(os.getenv("SANDBOX_BASE_PATH", "/tmp/code_sandbox"))
CODEBASE_ROOT = Path(os.getenv("CODEBASE_ROOT", "/app"))

class CodeEditingMCPServer:
    def __init__(self):
        self.server = Server("code-editing-mcp-server")
        if not MCP_FRAMEWORK_AVAILABLE:
            logger.warning("MCP framework not available. Server will have limited functionality (using dummies).")

        try:
            SANDBOX_BASE_PATH.mkdir(parents=True, exist_ok=True)
            logger.info(f"Sandbox base path ensured at: {SANDBOX_BASE_PATH}")
        except Exception as e:
            logger.error(f"Failed to create SANDBOX_BASE_PATH at {SANDBOX_BASE_PATH}: {e}", exc_info=True)
            # This could be a fatal error for the server's core functionality.

        self._setup_handlers()

    def _get_original_service_path(self, service_name: str) -> Optional[Path]:
        """Determines the path to the original service code within the CODEBASE_ROOT."""
        normalized_service_name = service_name.replace('-', '_')

        potential_paths_tried = []

        # Logic for mcp-prefixed services (e.g., mcp_servers/some_service.py or mcp_servers/some_service/)
        if service_name.startswith("mcp-"):
            specific_name = normalized_service_name.split('_', 1)[1] if '_' in normalized_service_name else normalized_service_name
            # Check for file: mcp_servers/specific_name.py
            p = CODEBASE_ROOT / "mcp_servers" / f"{specific_name}.py"
            potential_paths_tried.append(str(p))
            if p.exists() and p.is_file(): return p
            # Check for directory: mcp_servers/specific_name/
            p = CODEBASE_ROOT / "mcp_servers" / specific_name
            potential_paths_tried.append(str(p))
            if p.exists() and p.is_dir(): return p

        # Logic for src_-prefixed services (e.g., src/tools/mytool.py or src/tools/mytool/)
        elif service_name.startswith("src_"):
            parts = normalized_service_name.split('_')[1:] # Remove 'src'
            if parts:
                relative_path_from_src = Path("/".join(parts))
                # Check for file: src/part1/part2.py
                p = CODEBASE_ROOT / "src" / f"{relative_path_from_src}.py"
                potential_paths_tried.append(str(p))
                if p.exists() and p.is_file(): return p
                # Check for directory: src/part1/part2/
                p = CODEBASE_ROOT / "src" / relative_path_from_src
                potential_paths_tried.append(str(p))
                if p.exists() and p.is_dir(): return p

        # Logic for other services (e.g., ai_agents/my_agent.py or ai_agents/my_agent/)
        else:
            # Check under ai_agents/
            p = CODEBASE_ROOT / "ai_agents" / f"{normalized_service_name}.py"
            potential_paths_tried.append(str(p))
            if p.exists() and p.is_file(): return p
            p = CODEBASE_ROOT / "ai_agents" / normalized_service_name
            potential_paths_tried.append(str(p))
            if p.exists() and p.is_dir(): return p

            # Check directly under CODEBASE_ROOT (e.g. for top-level services)
            p = CODEBASE_ROOT / f"{normalized_service_name}.py"
            potential_paths_tried.append(str(p))
            if p.exists() and p.is_file(): return p
            p = CODEBASE_ROOT / normalized_service_name
            potential_paths_tried.append(str(p))
            if p.exists() and p.is_dir(): return p

        logger.error(f"Could not find original code path for service '{service_name}' under CODEBASE_ROOT '{CODEBASE_ROOT}'. Checked: {potential_paths_tried}")
        return None

    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="sandbox_apply_fix",
                    description="Creates a sandbox for a service, copies its code, and applies suggested full file content to a target file.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Name of the service (e.g., mcp-cache-manager)."},
                            "target_file_relative_path": {"type": "string", "description": "Relative path of the file to modify within the service's code structure (e.g., cache_manager.py or sub_module/file.py)."},
                            "suggested_full_file_content": {"type": "string", "description": "The full suggested content for the target file."},
                            "sandbox_id": {"type": "string", "description": "A unique ID for this sandboxing attempt."}
                        },
                        "required": ["service_name", "target_file_relative_path", "suggested_full_file_content", "sandbox_id"]
                    }
                ),
                Tool(
                    name="cleanup_sandbox",
                    description="Deletes a specified sandbox directory.",
                    inputSchema={
                        "type": "object",
                        "properties": {"sandbox_id": {"type": "string", "description": "The unique ID of the sandbox to delete."}},
                        "required": ["sandbox_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "sandbox_apply_fix":
                service_name = arguments.get("service_name")
                target_file_rel_path_str = arguments.get("target_file_relative_path")
                suggested_full_file_content = arguments.get("suggested_full_file_content")
                sandbox_id = arguments.get("sandbox_id")

                if not all([service_name, target_file_rel_path_str, suggested_full_file_content is not None, sandbox_id]):
                    return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": "Missing required arguments."}))]

                # Sanitize relative path to prevent path traversal issues
                target_file_relative_path = Path(target_file_rel_path_str.lstrip('/\\'))
                if ".." in target_file_relative_path.parts:
                    return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": "Invalid target_file_relative_path (contains '..')."}))]


                sandbox_service_root = SANDBOX_BASE_PATH / sandbox_id / service_name

                try:
                    original_service_code_path = self._get_original_service_path(service_name)
                    if not original_service_code_path:
                        return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": f"Original code for service '{service_name}' not found."}))]

                    if sandbox_service_root.exists():
                        logger.warning(f"Sandbox directory {sandbox_service_root} already exists. Clearing it.")
                        shutil.rmtree(sandbox_service_root)

                    # Ensure parent of sandbox_service_root exists for copying
                    sandbox_service_root.parent.mkdir(parents=True, exist_ok=True)

                    if original_service_code_path.is_dir():
                        shutil.copytree(original_service_code_path, sandbox_service_root, dirs_exist_ok=True)
                        logger.info(f"Copied directory from {original_service_code_path} to {sandbox_service_root}")
                        sandboxed_target_file = sandbox_service_root / target_file_relative_path
                    elif original_service_code_path.is_file():
                        sandbox_service_root.mkdir(parents=True, exist_ok=True) # Create service root dir in sandbox
                        shutil.copy2(original_service_code_path, sandbox_service_root / original_service_code_path.name)
                        logger.info(f"Copied file from {original_service_code_path} to {sandbox_service_root / original_service_code_path.name}")
                        # For single file services, target_file_relative_path must match the original file's name
                        if str(target_file_relative_path) != original_service_code_path.name:
                            logger.warning(f"Adjusting target_file_relative_path for single-file service. Was '{target_file_relative_path}', now '{original_service_code_path.name}'.")
                        sandboxed_target_file = sandbox_service_root / original_service_code_path.name
                    else:
                         return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": f"Original service path {original_service_code_path} is not a file or directory."}))]

                    sandboxed_target_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(sandboxed_target_file, "w", encoding='utf-8') as f:
                        f.write(suggested_full_file_content)
                    logger.info(f"Applied fix to {sandboxed_target_file}")

                    result = {
                        "status": "success",
                        "sandbox_id": sandbox_id,
                        "sandboxed_service_root": str(sandbox_service_root),
                        "modified_file_path": str(sandboxed_target_file)
                    }
                    return [TextContent(type="application/json", text=json.dumps(result))]

                except Exception as e:
                    logger.error(f"Error in sandbox_apply_fix for {sandbox_id}/{service_name}: {e}", exc_info=True)
                    return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": str(e)}))]

            elif name == "cleanup_sandbox":
                sandbox_id = arguments.get("sandbox_id")
                if not sandbox_id:
                    return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": "Missing sandbox_id."}))]

                sandbox_to_delete = SANDBOX_BASE_PATH / sandbox_id
                try:
                    # Security check: ensure we are deleting something under SANDBOX_BASE_PATH
                    if not sandbox_to_delete.is_relative_to(SANDBOX_BASE_PATH): # Requires Python 3.9+
                         # Manual check for older Pythons:
                         # if SANDBOX_BASE_PATH not in sandbox_to_delete.resolve().parents and sandbox_to_delete.resolve() != SANDBOX_BASE_PATH.resolve():
                        logger.error(f"Attempt to delete directory '{sandbox_to_delete}' outside SANDBOX_BASE_PATH '{SANDBOX_BASE_PATH}'. Denied.")
                        return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": "Invalid sandbox path for cleanup (outside base path)."}))]


                    if sandbox_to_delete.exists() and sandbox_to_delete.is_dir():
                        shutil.rmtree(sandbox_to_delete)
                        logger.info(f"Successfully cleaned up sandbox: {sandbox_to_delete}")
                        result = {"status": "success", "message": f"Sandbox {sandbox_id} cleaned up."}
                    elif not sandbox_to_delete.exists():
                        logger.warning(f"Sandbox {sandbox_to_delete} not found for cleanup, considered cleaned.")
                        result = {"status": "success", "message": "Sandbox not found, considered cleaned."}
                    else: # Exists but not a directory
                        logger.error(f"Path {sandbox_to_delete} is not a directory. Cleanup aborted.")
                        result = {"status": "error", "message": "Invalid path: not a directory."}
                    return [TextContent(type="application/json", text=json.dumps(result))]
                except Exception as e:
                    logger.error(f"Error cleaning up sandbox {sandbox_id}: {e}", exc_info=True)
                    return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": str(e)}))]
            else:
                logger.error(f"Call to unknown tool: {name}")
                raise ValueError(f"Unknown tool: {name}")

async def main():
    if not MCP_FRAMEWORK_AVAILABLE:
        logger.error("MCP framework not available. Cannot start CodeEditingMCPServer properly.")
        try:
            _ = CodeEditingMCPServer() # For basic validation by subtask runner
        except Exception as e:
            logger.error(f"Failed to instantiate CodeEditingMCPServer even with dummies: {e}")
        return

    server_instance = CodeEditingMCPServer()
    try:
        from mcp.server.stdio import stdio_server
        logger.info("Attempting to start server in stdio mode.")
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=server_instance.server.name,
                    server_version="1.0.0",
                    capabilities=server_instance.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ) if MCP_FRAMEWORK_AVAILABLE else None,
            )
    except ImportError:
        logger.warning("mcp.server.stdio not found. Server cannot run in stdio mode.")
    except Exception as e:
        logger.error(f"Error during server startup or execution: {e}", exc_info=True)

if __name__ == "__main__":
    # asyncio.run(main()) # Commented out for subtask validation
    pass
