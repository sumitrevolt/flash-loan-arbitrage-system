import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone # Added timezone
from typing import Dict, Any, Optional, List
from pathlib import Path # Added Path

import aiohttp

# Attempt to import data structures
try:
    # Assuming data_structures.py is in the same directory or PYTHONPATH is set up
    from .data_structures import CodeModificationAttempt, AttemptStatus, TestOutcome
except ImportError:
    # Fallback for environments where direct relative import might fail (e.g. some test runners)
    # This assumes 'src' is a top-level package or in PYTHONPATH
    from ai_agents.data_structures import CodeModificationAttempt, AttemptStatus, TestOutcome


# Configure logging
logger = logging.getLogger("ErrorResolutionAgent")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configuration for dependent MCP Servers
CODE_EDITING_MCP_URL = os.getenv("CODE_EDITING_MCP_URL", "http://localhost:8023/call_tool")
BASIC_FIX_TESTING_MCP_URL = os.getenv("BASIC_FIX_TESTING_MCP_URL", "http://localhost:8024/call_tool")

class ErrorResolutionAgent:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        if not session or session.closed:
            logger.warning("ErrorResolutionAgent initialized with a closed or None aiohttp session.")
            # In a real scenario, this agent might not function without a valid session.
            # The orchestrator is responsible for providing a valid session.

    def _get_iso_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _add_status_to_history(self, attempt_data: CodeModificationAttempt, status: AttemptStatus, detail: Optional[str] = None):
        timestamp = self._get_iso_timestamp()
        # Ensure status_history is initialized
        if "status_history" not in attempt_data: # Should be initialized in attempt_code_fix
            attempt_data["status_history"] = []

        attempt_data["status_history"].append({"status": status, "timestamp": timestamp, "detail": detail or ""})
        attempt_data["current_status"] = status
        attempt_data["last_updated_at"] = timestamp
        logger.info(f"Attempt ID {attempt_data.get('attempt_id', 'N/A')}: Status changed to {status}. Detail: {detail or 'N/A'}")


    async def _call_mcp_tool(self, server_url: str, payload: Dict[str, Any], timeout_seconds: int = 60) -> Optional[Dict[str, Any]]:
        """Helper method to call a tool on an MCP server via HTTP and parse JSON response."""
        if not self.session or self.session.closed:
            logger.error(f"AIOHTTP session not available or closed. Cannot call MCP tool at {server_url}.")
            return {"status": "error", "message": "AIOHTTP session unavailable."}
        try:
            logger.debug(f"Calling MCP tool at {server_url} with payload: {json.dumps(payload)}")
            async with self.session.post(server_url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) > 0 and data[0].get("type") == "application/json" and "text" in data[0]:
                        tool_response_json_str = data[0]["text"]
                        try:
                            tool_response_dict = json.loads(tool_response_json_str)
                            logger.debug(f"Successfully called MCP tool at {server_url}. Response: {json.dumps(tool_response_dict)}")
                            return tool_response_dict
                        except json.JSONDecodeError as je:
                            logger.error(f"JSONDecodeError parsing tool response from {server_url}: {je}. Raw text: {tool_response_json_str}")
                            return {"status": "error", "message": f"Failed to parse tool JSON response: {tool_response_json_str}"}
                    else:
                        logger.error(f"Unexpected response structure from MCP tool at {server_url}. Data: {data}")
                        return {"status": "error", "message": f"Unexpected response structure: {data}"}
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status} calling MCP tool at {server_url}: {error_text}")
                    return {"status": "error", "message": f"HTTP error {response.status}: {error_text}"}
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error calling MCP tool at {server_url}: {e}")
            return {"status": "error", "message": f"Connection error: {e}"}
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling MCP tool at {server_url}")
            return {"status": "error", "message": f"Request timed out after {timeout_seconds}s"}
        except Exception as e:
            logger.error(f"Exception calling MCP tool at {server_url}: {e}", exc_info=True)
            return {"status": "error", "message": f"Generic exception: {str(e)}"}

    async def attempt_code_fix(self, code_error_report: dict, llm_suggestion_response: dict) -> CodeModificationAttempt:
        attempt_id = uuid.uuid4().hex
        service_name = code_error_report.get("service_name", "UnknownService")

        # 'analyzed_file_path' from CodeAnalyzerAgent (via orchestrator) is expected to be project-relative.
        file_to_modify_project_rel = code_error_report.get("analyzed_file_path",
                                       code_error_report.get("error_details", {}).get("file_path", "unknown_file.py"))

        # target_file_relative_for_sandbox should be relative to the service's root directory.
        # Example: if project_rel is "mcp_servers/my_service/util.py", and service is "mcp-my-service"
        # which maps to "mcp_servers/my_service/", then relative is "util.py".
        # For a single file service, project_rel = "mcp_servers/my_service.py", relative = "my_service.py".
        # Using Path.name is a simplification. A robust solution would need to understand service roots.
        target_file_relative_for_sandbox = Path(file_to_modify_project_rel).name

        suggestion_to_apply = llm_suggestion_response.get("suggestion", "")
        current_ts = self._get_iso_timestamp()

        # Initial attempt data structure
        attempt_data: CodeModificationAttempt = {
            "attempt_id": attempt_id,
            "original_report_id": code_error_report.get("task_id", code_error_report.get("id")),
            "service_name": service_name,
            "file_path_to_modify": file_to_modify_project_rel,
            "original_code_snippet_preview": code_error_report.get("code_analyzer_result", {}).get("file_content_preview"),
            "llm_suggestion_raw": llm_suggestion_response.get("raw_suggestion", ""),
            "processed_suggestion_to_apply": suggestion_to_apply,
            "sandbox_id": f"fix_attempt_{attempt_id}", # Pre-assign sandbox_id for clarity
            "sandboxed_file_path": None,
            "status_history": [],
            "current_status": "pending", # Initial status
            "compilation_test_outcome": "not_run", "compilation_test_details": None,
            "linting_test_outcome": "not_run", "linting_test_details": None,
            "created_at": current_ts, "last_updated_at": current_ts,
            "attempt_process_error_message": None,
            "final_outcome_summary": None
        }
        self._add_status_to_history(attempt_data, "pending", "Fix attempt initiated.")


        if not suggestion_to_apply:
            logger.warning(f"Attempt ID {attempt_id}: No applicable code suggestion found in LLM response.")
            self._add_status_to_history(attempt_data, "error_during_process", "No valid code suggestion from LLM to apply.")
            attempt_data["attempt_process_error_message"] = "No valid code suggestion from LLM to apply."
            attempt_data["final_outcome_summary"] = "Skipped: No valid code suggestion from LLM."
            return attempt_data

        sandboxed_code_root_str: Optional[str] = None
        modified_file_in_sandbox_str: Optional[str] = None

        try:
            # 1. Sandbox and Apply Fix
            self._add_status_to_history(attempt_data, "sandbox_creation_started", f"Requesting sandbox for {service_name}")
            apply_fix_payload = {
                "tool_name": "sandbox_apply_fix",
                "arguments": {
                    "service_name": service_name,
                    "target_file_relative_path": target_file_relative_for_sandbox,
                    "suggested_full_file_content": suggestion_to_apply,
                    "sandbox_id": attempt_data["sandbox_id"] # Use pre-assigned sandbox_id
                }
            }
            apply_fix_response = await self._call_mcp_tool(CODE_EDITING_MCP_URL, apply_fix_payload, timeout_seconds=120) # Longer timeout for file ops

            if apply_fix_response and apply_fix_response.get("status") == "success":
                sandboxed_code_root_str = apply_fix_response.get("sandboxed_service_root") # Corrected key
                modified_file_in_sandbox_str = apply_fix_response.get("modified_file_path") # Corrected key
                attempt_data["sandboxed_file_path"] = modified_file_in_sandbox_str
                self._add_status_to_history(attempt_data, "fix_applied_in_sandbox", f"Fix applied in sandbox: {modified_file_in_sandbox_str}")
            else:
                err_msg = f"Failed to apply fix in sandbox: {apply_fix_response.get('message', 'Unknown error') if apply_fix_response else 'No response'}"
                self._add_status_to_history(attempt_data, "fix_application_failed", err_msg)
                attempt_data["attempt_process_error_message"] = err_msg
                attempt_data["final_outcome_summary"] = "Error: Failed to apply fix in sandbox."
                # Proceed to cleanup (will happen outside this try block)

        except Exception as e: # Catch any other unexpected error during this phase
            logger.error(f"Attempt ID {attempt_id}: Exception during sandbox_apply_fix phase: {e}", exc_info=True)
            self._add_status_to_history(attempt_data, "error_during_process", f"Exception applying fix: {str(e)}")
            attempt_data["attempt_process_error_message"] = str(e)
            attempt_data["final_outcome_summary"] = "Error: Exception during fix application."
            # Proceed to cleanup

        # 2. Basic Tests (only if fix was applied successfully)
        if attempt_data["current_status"] == "fix_applied_in_sandbox" and sandboxed_code_root_str and modified_file_in_sandbox_str:
            self._add_status_to_history(attempt_data, "testing_started", f"Running basic tests on {modified_file_in_sandbox_str}")

            # `target_file_relative_path` for testing is relative to `sandboxed_code_root_str`.
            # This should be the same relative path used for applying the fix.
            test_target_relative = target_file_relative_for_sandbox

            testing_payload = {
                "tool_name": "run_basic_tests",
                "arguments": {
                    "service_name": service_name,
                    "sandboxed_code_root": sandboxed_code_root_str,
                    "target_file_relative_path": str(test_target_relative)
                }
            }
            testing_response = await self._call_mcp_tool(BASIC_FIX_TESTING_MCP_URL, testing_payload, timeout_seconds=90) # Timeout for tests

            if testing_response and testing_response.get("status") == "success":
                comp_check = testing_response.get("compilation_check", {})
                lint_check = testing_response.get("linting_check", {})
                attempt_data["compilation_test_outcome"] = comp_check.get("outcome", "error_running_test")
                attempt_data["compilation_test_details"] = comp_check.get("details")
                attempt_data["linting_test_outcome"] = lint_check.get("outcome", "error_running_test")
                attempt_data["linting_test_details"] = lint_check.get("issues_found")

                overall_test_outcome = testing_response.get("overall_outcome", "failed")
                if overall_test_outcome == "passed":
                    self._add_status_to_history(attempt_data, "testing_completed", "All basic tests passed in sandbox.")
                    attempt_data["final_outcome_summary"] = "Fix applied and passed basic tests in sandbox."
                    self._add_status_to_history(attempt_data, "completed_fix_successful", "Fix successful in sandbox.")
                else:
                    test_fail_detail = f"Compilation: {attempt_data['compilation_test_outcome']}, Linting: {attempt_data['linting_test_outcome']}."
                    self._add_status_to_history(attempt_data, "testing_failed_overall", f"Basic tests failed in sandbox. {test_fail_detail}")
                    attempt_data["final_outcome_summary"] = f"Fix applied but failed basic tests in sandbox. {test_fail_detail}"
                    self._add_status_to_history(attempt_data, "completed_fix_failed_tests", test_fail_detail)
            else: # Testing tool call failed or returned error status
                err_msg = f"Failed to run tests or parse response: {testing_response.get('message', 'Unknown error') if testing_response else 'No response'}"
                self._add_status_to_history(attempt_data, "error_during_process", err_msg)
                attempt_data["attempt_process_error_message"] = (attempt_data.get("attempt_process_error_message") or "") + " | " + err_msg
                attempt_data["final_outcome_summary"] = attempt_data.get("final_outcome_summary") or "Error: Failed to execute tests in sandbox."
                # If tests couldn't run, it's effectively a test failure for this attempt
                self._add_status_to_history(attempt_data, "testing_failed_overall", "Could not execute tests.")
        elif attempt_data["current_status"] not in ["fix_application_failed", "error_during_process"]:
            # If fix wasn't applied, but no major error occurred before this point.
            logger.info(f"Attempt ID {attempt_id}: Skipping testing phase as fix was not successfully applied.")
            self._add_status_to_history(attempt_data, "error_during_process", "Skipped testing as fix application was not successful.")


        # 3. Cleanup Sandbox (always attempt this if sandbox_id was set)
        if attempt_data["sandbox_id"]:
            self._add_status_to_history(attempt_data, "sandbox_cleanup_started", f"Requesting cleanup for sandbox {attempt_data['sandbox_id']}")
            cleanup_payload = {
                "tool_name": "cleanup_sandbox",
                "arguments": {"sandbox_id": attempt_data["sandbox_id"]}
            }
            cleanup_response = await self._call_mcp_tool(CODE_EDITING_MCP_URL, cleanup_payload, timeout_seconds=120) # Longer for file ops

            if cleanup_response and cleanup_response.get("status") == "success":
                self._add_status_to_history(attempt_data, "sandbox_cleaned_up_successfully", f"Sandbox {attempt_data['sandbox_id']} cleaned up.")
            else:
                err_msg = f"Failed to cleanup sandbox {attempt_data['sandbox_id']}: {cleanup_response.get('message', 'Unknown error') if cleanup_response else 'No response'}"
                self._add_status_to_history(attempt_data, "sandbox_cleanup_failed", err_msg)
                # Append to existing process errors, don't overwrite
                current_proc_err = attempt_data.get("attempt_process_error_message")
                attempt_data["attempt_process_error_message"] = f"{current_proc_err} | {err_msg}" if current_proc_err else err_msg

        # Ensure a final summary if one wasn't set due to an error path
        if not attempt_data["final_outcome_summary"]:
            if attempt_data["current_status"] == "completed_fix_successful":
                 attempt_data["final_outcome_summary"] = "Fix successful in sandbox."
            elif attempt_data["current_status"] == "completed_fix_failed_tests":
                 attempt_data["final_outcome_summary"] = "Fix applied but failed tests in sandbox."
            else:
                attempt_data["final_outcome_summary"] = f"Process ended with status: {attempt_data['current_status']}. Check error messages for details."

        attempt_data["last_updated_at"] = self._get_iso_timestamp() # Final update before returning
        return attempt_data


async def main_test():
    """ Example usage / test stub for ErrorResolutionAgent """
    sample_code_error_report = {
        "task_id": "err_report_xyz789",
        "service_name": "mcp-example-service",
        "analyzed_file_path": "mcp_servers/example_service.py",
        "error_details": {"type": "NameError", "message": "name 'x' is not defined", "file_path": "mcp_servers/example_service.py"},
        "log_snippet": "NameError: name 'x' is not defined on line 10",
        "code_analyzer_result": {
            "file_content_preview": "def my_func():\n  y = 5\n  z = x + y # x is not defined\n  return z"
        }
    }
    sample_llm_suggestion = {
        "status": "success",
        "suggestion": "def my_func():\n  x = 10 # Define x\n  y = 5\n  z = x + y\n  return z",
        "raw_suggestion": "```python\ndef my_func():\n  x = 10 # Define x\n  y = 5\n  z = x + y\n  return z\n```"
    }

    # This test requires mock MCP servers or actual running servers.
    # For subtask validation, direct execution is commented out.
    # Setup:
    # 1. Create dummy files CODEBASE_ROOT/mcp_servers/example_service.py
    #    CODEBASE_ROOT should be '/app' if using default.
    #    os.makedirs("/app/mcp_servers", exist_ok=True)
    #    with open("/app/mcp_servers/example_service.py", "w") as f:
    #        f.write("def my_func():\n  y = 5\n  z = x + y # x is not defined\n  return z\n")

    async with aiohttp.ClientSession() as session:
        agent = ErrorResolutionAgent(session=session)

        logger.info("--- [Test Case 1] Attempting code fix with a valid suggestion ---")
        # result1 = await agent.attempt_code_fix(sample_code_error_report, sample_llm_suggestion)
        # logger.info(f"Test Case 1 Result:\n{json.dumps(result1, indent=2)}")

        logger.info("\n--- [Test Case 2] Attempting code fix with no valid LLM suggestion ---")
        empty_llm_suggestion = {"status": "success", "suggestion": "", "raw_suggestion": ""} # Empty suggestion
        result2 = await agent.attempt_code_fix(sample_code_error_report, empty_llm_suggestion)
        logger.info(f"Test Case 2 Result (No Suggestion):\n{json.dumps(result2, indent=2)}")

        logger.info("\n--- [Test Case 3] LLM suggestion leads to compilation error ---")
        bad_llm_suggestion = {
            "status": "success",
            "suggestion": "def my_func():\n  x = 10\n  y = 5\n  z = x + y\n  return z\n  invalid syntax here -", # Introduce syntax error
            "raw_suggestion": "def my_func():\n  x = 10\n  y = 5\n  z = x + y\n  return z\n  invalid syntax here -"
        }
        # result3 = await agent.attempt_code_fix(sample_code_error_report, bad_llm_suggestion)
        # logger.info(f"Test Case 3 Result (Bad Suggestion):\n{json.dumps(result3, indent=2)}")


if __name__ == "__main__":
    # Ensure the logger for the agent is visible during tests
    # logging.getLogger("ErrorResolutionAgent").setLevel(logging.DEBUG)
    # logging.getLogger("DummyMCPForCodeEditing").setLevel(logging.INFO) # If using dummy servers
    # logging.getLogger("DummyMCPForBasicTesting").setLevel(logging.INFO)

    # asyncio.run(main_test()) # Commented out for subtask validation
    pass
