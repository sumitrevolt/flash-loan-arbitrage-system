from typing import TypedDict, List, Optional, Literal, Dict
# No need to import datetime for type hints if only using strings,
# but if datetime objects were stored, it would be needed.
# For ISO datetime strings, `str` is sufficient.

# Literal types for status fields to provide better type checking and auto-completion
AttemptStatus = Literal[
    "pending",
    "sandbox_creation_started",
    "sandbox_created_successfully",
    "sandbox_creation_failed",
    "fix_application_started",
    "fix_applied_in_sandbox",
    "fix_application_failed",
    "testing_started",
    "test_compilation_passed",
    "test_compilation_failed",
    "test_linting_passed",
    "test_linting_failed",
    # "test_unit_passed", # Future use
    # "test_unit_failed", # Future use
    "testing_completed", # General status indicating tests ran
    "testing_failed_overall", # If any crucial test part fails
    "sandbox_cleanup_started",
    "sandbox_cleaned_up_successfully",
    "sandbox_cleanup_failed",
    "completed_fix_successful", # If applied and tested successfully (in sandbox)
    "completed_fix_failed_tests", # If applied but failed tests
    "error_during_process" # Generic error for the attempt itself
]

TestOutcome = Literal["not_run", "passed", "failed", "error_running_test"]

class CodeModificationAttempt(TypedDict):
    attempt_id: str # A unique identifier for this attempt, e.g., UUID
    original_report_id: Optional[str] # ID from the CODE_ERROR_REPORT task or similar
    service_name: str
    file_path_to_modify: str

    original_code_snippet_preview: Optional[str] # e.g., a few lines around the error from CodeAnalyzerAgent
    llm_suggestion_raw: str # The raw suggestion from the LLM
    # The specific part of the LLM suggestion that will be applied (e.g., just the code block)
    processed_suggestion_to_apply: str

    sandbox_id: Optional[str] # Identifier for the sandbox environment used (e.g., directory name)
    sandboxed_file_path: Optional[str] # Full path to the modified file within the sandbox

    # History of status changes for detailed tracking
    status_history: List[Dict[str, str]]
    # Example entry: {"status": AttemptStatus, "timestamp": "iso_datetime_str", "detail": "Optional message"}

    current_status: AttemptStatus # The latest status of the attempt

    # Test results
    compilation_test_outcome: TestOutcome
    compilation_test_details: Optional[str] # e.g., compiler error message

    linting_test_outcome: TestOutcome
    linting_test_details: Optional[List[str]] # List of linting messages from flake8

    # Placeholder for future, more comprehensive test results
    # unit_test_outcome: TestOutcome
    # unit_test_details: Optional[str]

    created_at: str # ISO datetime string when the attempt was initiated
    last_updated_at: str # ISO datetime string of the last status update

    # Optional field for any errors encountered during the attempt process itself (e.g., sandbox creation failure)
    attempt_process_error_message: Optional[str]

    # Summary of the outcome
    final_outcome_summary: Optional[str] # e.g., "Fix applied and passed basic tests in sandbox."
