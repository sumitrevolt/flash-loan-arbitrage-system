import json
import logging
import subprocess
import os
import aiohttp # For making HTTP requests to FileSystemMCPServer
import asyncio # Added for main test stub

# Configure logging
logger = logging.getLogger("CodeAnalyzerAgent")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configuration for FileSystemMCPServer
FILESYSTEM_MCP_URL = os.getenv("FILESYSTEM_MCP_URL", "http://localhost:8001/call_tool")

class CodeAnalyzerAgent:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    def _get_service_file_path(self, service_name: str, error_report: dict) -> str:
        """
        Determines the conventional file path for a given service.
        Uses 'file_path' from error report details if available and seems reasonable.
        Otherwise, assumes a convention based on service name.
        """
        # Prioritize file_path from error_details if it seems plausible
        # The key from orchestrator is 'file_path', not 'file_path_guess'
        guessed_path = error_report.get("error_details", {}).get("file_path")
        normalized_service_name = service_name.replace('-', '_')

        if guessed_path and guessed_path.endswith(".py"):
            # Check if the guessed path contains a semblance of the service name
            # This is a basic sanity check. e.g., service 'mcp-foo' and path 'mcp_servers/foo.py'
            if normalized_service_name in guessed_path.replace('-', '_').replace('/', '_'):
                # Check if it's a relative path from a known root like 'mcp_servers/', 'ai_agents/', 'src/'
                if guessed_path.startswith(("mcp_servers/", "ai_agents/", "src/")):
                    logger.info(f"Using file path from error report: {guessed_path}")
                    return guessed_path
                # If it's just a filename, prepend a conventional directory
                elif "/" not in guessed_path:  # e.g., "some_server.py"
                    if service_name.startswith("mcp-"):
                        logger.info(f"Using conventional directory for filename from report: mcp_servers/{guessed_path}")
                        return f"mcp_servers/{guessed_path}"
                    elif service_name.startswith("src_"):
                        # This case is tricky if only filename is guessed, assume it's in a subdirectory of src
                        # Defaulting to a flat structure under src/ for a simple guess might be too naive
                        # For now, let's prefer the full path guess for src_ or use convention
                        logger.info(f"Filename guess '{guessed_path}' for src_ service '{service_name}'. Using conventional path instead.")
                        pass # Fall through to conventional path logic for src_ if only filename given
                    else: # Assumed ai_agents
                        logger.info(f"Using conventional directory for filename from report: ai_agents/{guessed_path}")
                        return f"ai_agents/{guessed_path}"
            else:
                logger.info(f"File path guess '{guessed_path}' does not seem to match service name '{service_name}'. Using convention.")


        # Fallback to conventional paths
        if service_name.startswith("mcp-"):
            specific_name = normalized_service_name.split('_', 1)[1] if '_' in normalized_service_name else normalized_service_name
            path = f"mcp_servers/{specific_name}.py"
        elif service_name.startswith("src_"):
            # src_module_file -> src/module/file.py
            # src_module_submodule_file -> src/module/submodule/file.py
            parts = normalized_service_name.split('_')[1:] # Remove 'src', get ['module', 'file']
            if len(parts) > 1:
                dir_path = "/".join(parts[:-1])
                file_name = parts[-1]
                path = f"src/{dir_path}/{file_name}.py"
            elif len(parts) == 1: # e.g. src_main -> src/main.py
                path = f"src/{parts[0]}.py"
            else:
                logger.warning(f"Could not determine path for src_ service: {service_name}. Defaulting to src/{normalized_service_name}.py")
                path = f"src/{normalized_service_name}.py" # Fallback
        else: # Assumes it's an AI agent or other structure
            path = f"ai_agents/{normalized_service_name}.py"

        logger.info(f"Using conventional file path: {path} for service: {service_name}")
        return path

    async def _fetch_code_content(self, file_path: str) -> tuple[str | None, str | None]:
        """Fetches code content from FileSystemMCPServer."""
        payload = {
            "tool_name": "read_file_content",
            "arguments": {"file_path": file_path}
        }
        try:
            logger.info(f"Fetching code for {file_path} from {FILESYSTEM_MCP_URL}")
            async with self.session.post(FILESYSTEM_MCP_URL, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    # Assuming FileSystemMCPServer returns a list of content items,
                    # and the first item's "text" field contains a JSON string.
                    if isinstance(data, list) and len(data) > 0 and "text" in data[0]:
                        mcp_response_text = data[0]["text"]
                        try:
                            mcp_response = json.loads(mcp_response_text)
                            if mcp_response.get("status") == "success":
                                logger.info(f"Successfully fetched code for {file_path}")
                                return mcp_response.get("content"), None
                            else:
                                error_msg = mcp_response.get("message", "Unknown error from FileSystemMCPServer tool")
                                logger.error(f"FileSystemMCPServer tool returned error for {file_path}: {error_msg}")
                                return None, error_msg
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON response from FileSystemMCPServer for {file_path}: {mcp_response_text}")
                            return None, f"Invalid JSON response from tool: {mcp_response_text}"
                    else:
                        logger.warning(f"Unexpected response structure from FileSystemMCPServer for {file_path}. Data: {data}")
                        return None, f"Unexpected response structure: {data}"
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status} fetching code for {file_path}: {error_text}")
                    return None, f"HTTP error {response.status}: {error_text}"
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error fetching code for {file_path} from {FILESYSTEM_MCP_URL}: {e}")
            return None, f"Connection error: {e}"
        except Exception as e:
            logger.error(f"Exception fetching code for {file_path}: {e}")
            return None, f"Exception: {e}"

    def _lint_code(self, file_content: str, file_path: str) -> tuple[list[str] | None, str | None]:
        """Lints the given code content using flake8."""
        if not file_content:
            return None, "No content to lint."

        # Create a temporary file to lint (flake8 works best with files)
        temp_file_name = f"temp_{os.path.basename(file_path)}"
        temp_file_path = os.path.join("/tmp", temp_file_name) # Ensure it's in /tmp

        try:
            with open(temp_file_path, "w") as f:
                f.write(file_content)

            logger.info(f"Linting code from {file_path} (using temp file {temp_file_path})")
            process = subprocess.run(
                ["flake8", "--isolated", temp_file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            linting_results = process.stdout.splitlines()
            # Replace the temporary file path prefix with the original file path for clarity
            linting_results = [line.replace(temp_file_path + ":", file_path + ":", 1) for line in linting_results]
            logger.info(f"Linting for {file_path} complete. Found {len(linting_results)} issues.")
            return linting_results, None
        except FileNotFoundError:
            logger.error("flake8 not found. Please ensure it's installed in the agent's environment.")
            return None, "flake8 command not found."
        except subprocess.TimeoutExpired:
            logger.error(f"Linting timed out for {file_path}")
            return None, "Linting process timed out."
        except Exception as e:
            logger.error(f"Exception during linting of {file_path}: {e}")
            return None, f"Exception during linting: {e}"
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    async def analyze_code_from_report(self, error_report: dict) -> dict:
        """
        Analyzes code based on an error report.
        Fetches code using FileSystemMCPServer and lints it.
        """
        service_name = error_report.get("service_name")
        if not service_name:
            return {"status": "error", "message": "Missing service_name in error report."}

        file_path_to_analyze = self._get_service_file_path(service_name, error_report)

        analysis_result = {
            "service_name": service_name,
            "analyzed_file_path": file_path_to_analyze,
            "file_access_status": "pending",
            "file_content_preview": None, # First 5 lines
            "linting_status": "pending",
            "linting_results": None,
            "error_message": None
        }

        code_content, fetch_error = await self._fetch_code_content(file_path_to_analyze)

        if fetch_error:
            analysis_result["file_access_status"] = "error"
            analysis_result["error_message"] = fetch_error
            logger.error(f"Failed to fetch code for {file_path_to_analyze}: {fetch_error}")
            return analysis_result

        if not code_content:
            analysis_result["file_access_status"] = "error"
            analysis_result["error_message"] = "Fetched empty content."
            logger.error(f"Fetched empty content for {file_path_to_analyze}.")
            return analysis_result

        analysis_result["file_access_status"] = "success"
        analysis_result["file_content_preview"] = "\n".join(code_content.splitlines()[:5])

        linting_results, lint_error = self._lint_code(code_content, file_path_to_analyze)

        if lint_error:
            analysis_result["linting_status"] = "error"
            # Combine fetch error (if any, though unlikely if we got here) with lint error
            current_err = analysis_result.get("error_message")
            analysis_result["error_message"] = f"{current_err} | {lint_error}" if current_err else lint_error
            logger.error(f"Linting error for {file_path_to_analyze}: {lint_error}")

        # Store linting results even if there was a secondary error during the linting process itself
        analysis_result["linting_results"] = linting_results if linting_results is not None else []
        if not lint_error:
             analysis_result["linting_status"] = "success"


        return analysis_result

async def main():
    """ Example usage / test stub """
    # Ensure /tmp directory exists for linting temp files
    os.makedirs("/tmp", exist_ok=True)

    sample_error_report_mcp = {
        "task_type": "CODE_ERROR_REPORT",
        "service_name": "mcp-some-server",
        "container_id": "container_id_example_mcp",
        "timestamp": "2023-10-27T10:00:00Z",
        "error_details": {
            "type": "SyntaxError",
            "message": "invalid syntax",
            "file_path": "mcp_servers/some_server.py", # Orchestrator provides 'file_path'
            "line_number": 10 # Orchestrator provides 'line_number'
        },
        "log_snippet": "Traceback(...)\nSyntaxError: invalid syntax"
    }

    sample_error_report_agent_noguess = {
        "task_type": "CODE_ERROR_REPORT",
        "service_name": "my_analyzer_agent",
        "container_id": "container_id_example_agent",
        "timestamp": "2023-10-27T10:00:00Z",
        "error_details": {
            "type": "ImportError",
            "message": "cannot import name 'x'",
            # No file_path provided, agent will use convention
        },
        "log_snippet": "Traceback(...)\nImportError: cannot import name 'x'"
    }

    sample_error_report_src_service = {
        "task_type": "CODE_ERROR_REPORT",
        "service_name": "src_tools_utils_helper", # Expects src/tools/utils/helper.py
        "container_id": "container_id_example_src",
        "timestamp": "2023-10-27T10:00:00Z",
        "error_details": {
            "type": "NameError",
            "message": "name 'some_var' is not defined",
            "file_path": "src/tools/utils/helper.py", # Good path provided
            "line_number": 5
        },
        "log_snippet": "Traceback(...)\nNameError: name 'some_var' is not defined"
    }


    async with aiohttp.ClientSession() as session:
        analyzer = CodeAnalyzerAgent(session=session)

        logger.info("--- Testing with MCP Server Report (good path in report) ---")
        # For this test to work, FileSystemMCPServer needs to be running and able to serve this file.
        # Create a dummy file for FileSystemMCPServer to serve:
        os.makedirs("mcp_servers", exist_ok=True)
        with open("mcp_servers/some_server.py", "w") as f:
            f.write("import os\n\ndef main_func():\n  print('hello')\n  x = 1 +\n") # Intentional syntax error for flake8

        result_mcp = await analyzer.analyze_code_from_report(sample_error_report_mcp)
        logger.info(f"Analysis Result (MCP):\n{json.dumps(result_mcp, indent=2)}")

        logger.info("\n--- Testing with Agent Report (no path in report, uses convention) ---")
        os.makedirs("ai_agents", exist_ok=True)
        with open("ai_agents/my_analyzer_agent.py", "w") as f: # Matches conventional name
            f.write("import non_existent_module\n\nprint('done')\n")
        result_agent = await analyzer.analyze_code_from_report(sample_error_report_agent_noguess)
        logger.info(f"Analysis Result (Agent):\n{json.dumps(result_agent, indent=2)}")

        logger.info("\n--- Testing with src_ prefixed service (good path in report) ---")
        os.makedirs("src/tools/utils", exist_ok=True)
        with open("src/tools/utils/helper.py", "w") as f:
            f.write("def helper_function():\n    undefined_variable = 1\n    return undefined_variable\n")
        result_src = await analyzer.analyze_code_from_report(sample_error_report_src_service)
        logger.info(f"Analysis Result (src service):\n{json.dumps(result_src, indent=2)}")

        logger.info("\n--- Testing with Non-Existent File Report ---")
        # This service name will lead to conventional path: mcp_servers/non_existent_service.py
        # FileSystemMCPServer should ideally return an error for this.
        sample_error_report_non_existent = {
            "service_name": "mcp-non-existent-service",
             "error_details": { "type": "RuntimeError", "message": "File not found during execution"}
        }
        result_non_existent = await analyzer.analyze_code_from_report(sample_error_report_non_existent)
        logger.info(f"Analysis Result (Non-Existent):\n{json.dumps(result_non_existent, indent=2)}")


if __name__ == "__main__":
    # This main is for local testing of the agent's capabilities.
    # To run this test, you'd need:
    # 1. flake8 installed (`pip install flake8`)
    # 2. aiohttp installed (`pip install aiohttp`)
    # 3. A FileSystemMCPServer running on http://localhost:8001 that can serve files
    #    from `mcp_servers/`, `ai_agents/`, and `src/` relative to where this script is run.
    #    A simple mock FileSystemMCPServer would be needed for more isolated testing.

    # asyncio.run(main()) # Comment out actual execution for subtask tool validation
    pass # Ensure script is valid for syntax checking by the tool
