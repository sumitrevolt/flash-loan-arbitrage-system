import asyncio
import json
import logging
import os
import subprocess # For running py_compile and flake8
from pathlib import Path
from typing import Dict, List, Any, Optional

# Attempt to import MCP server components (with fallbacks for subtask validation)
try:
    from mcp.server import Server, InitializationOptions, NotificationOptions
    from mcp.types import Tool, TextContent
    MCP_FRAMEWORK_AVAILABLE = True
except ImportError:
    MCP_FRAMEWORK_AVAILABLE = False
    # Define dummy classes if MCP framework is not available
    _dummy_logger = logging.getLogger("DummyMCPForBasicTesting") # Separate logger for this context
    _dummy_logger.warning("MCP framework not found, using dummy classes for BasicFixTestingMCPServer.")
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
logger = logging.getLogger("BasicFixTestingMCPServer")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BasicFixTestingMCPServer:
    def __init__(self):
        self.server = Server("basic-fix-testing-mcp-server")
        if not MCP_FRAMEWORK_AVAILABLE:
            logger.warning("MCP framework not available. Server will have limited functionality (using dummies).")
        self._setup_handlers()

    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="run_basic_tests",
                    description="Runs basic tests (Python compilation and flake8 linting) on a target file within a sandboxed code root.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Name of the service being tested (for context)."},
                            "sandboxed_code_root": {"type": "string", "description": "Absolute path to the root of the sandboxed service code."},
                            "target_file_relative_path": {"type": "string", "description": "Relative path of the modified file within the sandboxed_code_root to be tested."}
                        },
                        "required": ["service_name", "sandboxed_code_root", "target_file_relative_path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "run_basic_tests":
                service_name = arguments.get("service_name")
                sandboxed_code_root_str = arguments.get("sandboxed_code_root")
                target_file_relative_str = arguments.get("target_file_relative_path")

                if not all([service_name, sandboxed_code_root_str, target_file_relative_str]):
                    return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": "Missing required arguments."}))]

                sandboxed_code_root = Path(sandboxed_code_root_str)
                target_file_relative = Path(target_file_relative_str.lstrip('/\\'))
                if ".." in target_file_relative.parts:
                    return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": "Invalid target_file_relative_path (contains '..')."}))]

                absolute_target_file = sandboxed_code_root / target_file_relative

                compilation_result: Dict[str, Any] = {"outcome": "not_run", "details": None}
                linting_result: Dict[str, Any] = {"outcome": "not_run", "issues_found": [], "details": None}

                try:
                    if not sandboxed_code_root.exists() or not sandboxed_code_root.is_dir():
                        msg = f"Sandboxed code root {sandboxed_code_root} does not exist or is not a directory."
                        logger.error(msg)
                        return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": msg}))]

                    if not absolute_target_file.exists() or not absolute_target_file.is_file():
                        msg = f"Target file {absolute_target_file} does not exist or is not a file in the sandbox."
                        logger.error(msg)
                        return [TextContent(type="application/json", text=json.dumps({"status": "error", "message": msg}))]

                    # 1. Python Syntax Check (Compilation)
                    logger.info(f"Running py_compile on {absolute_target_file}")
                    try:
                        compile_process = subprocess.run(
                            ["python3", "-m", "py_compile", str(absolute_target_file)],
                            capture_output=True, text=True, timeout=30, check=False # check=False to handle non-zero exits manually
                        )
                        if compile_process.returncode == 0:
                            compilation_result["outcome"] = "passed"
                            logger.info(f"py_compile passed for {absolute_target_file}")
                        else:
                            compilation_result["outcome"] = "failed"
                            compilation_result["details"] = (compile_process.stderr or compile_process.stdout).strip()
                            logger.warning(f"py_compile failed for {absolute_target_file}: {compilation_result['details']}")
                    except subprocess.TimeoutExpired:
                        logger.error(f"py_compile timed out for {absolute_target_file}")
                        compilation_result["outcome"] = "error_running_test"
                        compilation_result["details"] = "py_compile process timed out."
                    except FileNotFoundError:
                        logger.error("'python3' command not found for py_compile.")
                        compilation_result["outcome"] = "error_running_test"
                        compilation_result["details"] = "'python3' command not found."
                    except Exception as e_compile:
                        logger.error(f"Exception during py_compile for {absolute_target_file}: {e_compile}", exc_info=True)
                        compilation_result["outcome"] = "error_running_test"
                        compilation_result["details"] = f"Exception: {str(e_compile)}"

                    # 2. Linting with Flake8
                    # Flake8 can run even if there's a syntax error caught by py_compile, as it has its own parser.
                    logger.info(f"Running flake8 on {absolute_target_file}")
                    try:
                        flake8_process = subprocess.run(
                            ["flake8", "--isolated", "--show-source", str(absolute_target_file)], # --show-source for context
                            capture_output=True, text=True, timeout=30, check=False
                        )
                        linting_issues_raw = flake8_process.stdout.strip().splitlines()
                        # Remove sandboxed path prefix for cleaner, relative paths in output
                        linting_issues = [
                            line.replace(str(absolute_target_file) + ":", str(target_file_relative) + ":", 1)
                            for line in linting_issues_raw
                        ]

                        if not linting_issues: # No output implies no issues found by flake8
                            if flake8_process.returncode == 0: # Normal "no issues" exit
                                linting_result["outcome"] = "passed"
                                logger.info(f"flake8 found no issues for {absolute_target_file}")
                            else: # Non-zero exit but no stdout, implies flake8 error or config issue
                                linting_result["outcome"] = "error_running_test"
                                linting_result["details"] = (flake8_process.stderr or "flake8 exited non-zero without specific issues on stdout.").strip()
                                logger.error(f"flake8 error for {absolute_target_file} (no stdout): {linting_result['details']}")
                        else: # Issues were found and printed to stdout
                            linting_result["outcome"] = "failed"
                            linting_result["issues_found"] = linting_issues
                            logger.warning(f"flake8 found {len(linting_issues)} issues for {absolute_target_file}")
                            # Details field can store a summary or if stderr had something
                            if flake8_process.stderr:
                                linting_result["details"] = flake8_process.stderr.strip()

                    except subprocess.TimeoutExpired:
                        logger.error(f"flake8 timed out for {absolute_target_file}")
                        linting_result["outcome"] = "error_running_test"
                        linting_result["details"] = "flake8 process timed out."
                    except FileNotFoundError:
                        logger.error("'flake8' command not found for linting.")
                        linting_result["outcome"] = "error_running_test"
                        linting_result["details"] = "'flake8' command not found."
                    except Exception as e_flake8:
                        logger.error(f"Exception during flake8 for {absolute_target_file}: {e_flake8}", exc_info=True)
                        linting_result["outcome"] = "error_running_test"
                        linting_result["details"] = f"Exception: {str(e_flake8)}"

                except Exception as e_outer: # Catch issues like sandboxed_code_root not existing
                    logger.error(f"Outer exception in run_basic_tests for {service_name}: {e_outer}", exc_info=True)
                    return [TextContent(type="application/json", text=json.dumps({
                        "status": "error",
                        "message": f"Failed to prepare for tests: {str(e_outer)}",
                        "compilation_check": compilation_result, # Include partial results if any
                        "linting_check": linting_result,
                        "overall_outcome": "failed"
                    }))]

                # Determine overall outcome
                overall_outcome = "failed" # Default
                if compilation_result["outcome"] == "passed" and linting_result["outcome"] == "passed":
                    overall_outcome = "passed"

                response_payload = {
                    "status": "success",
                    "compilation_check": compilation_result,
                    "linting_check": linting_result,
                    "overall_outcome": overall_outcome
                }
                return [TextContent(type="application/json", text=json.dumps(response_payload))]

            else:
                logger.error(f"Call to unknown tool: {name}")
                raise ValueError(f"Unknown tool: {name}")

async def main():
    if not MCP_FRAMEWORK_AVAILABLE:
        logger.error("MCP framework is not available. Cannot start BasicFixTestingMCPServer properly.")
        try:
            _ = BasicFixTestingMCPServer() # For basic validation by subtask runner
        except Exception as e:
            logger.error(f"Failed to instantiate BasicFixTestingMCPServer even with dummies: {e}")
        return

    server_instance = BasicFixTestingMCPServer()
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
