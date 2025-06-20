# Code Improvement Agent Guide

## 1. Overview

**Purpose:**
The Code Improvement Agent is a powerful tool designed to automate the process of enhancing codebases. It scans your projects for various issues, including syntax errors, coding style violations, potential bugs, and deprecated code usage. Leveraging the capabilities of local Large Language Models (LLMs) and predefined rules, it can suggest fixes and, if desired, automatically apply them by creating GitHub Pull Requests.

**Key Technologies:**
*   **Python 3.8+:** The core language for the agent.
*   **LangChain:** Used for orchestrating LLM interactions and building intelligent agentic workflows.
*   **Ollama:** Enables running local LLMs (e.g., CodeLlama, Mistral) for code analysis and generation, ensuring privacy and offline capabilities.
*   **GitHub API:** For interacting with GitHub repositories, including cloning, creating branches, pushing changes, and opening Pull Requests.

## 2. Setup Instructions

### Prerequisites
*   **Python:** Version 3.8 or higher installed.
*   **Git:** Git must be installed and accessible via your system's PATH.
*   **Ollama:** Ollama must be installed and running. You can download it from [ollama.com](https://ollama.com/).

### Installation
1.  **Clone the Repository:**
    If you haven't already, clone the repository containing the agent:
    ```bash
    # Replace with the actual clone command for your repository
    git clone <your_repository_url>
    cd <repository_directory>
    ```

2.  **Install Dependencies:**
    Install the necessary Python packages. The `AutomatedProjectFixer` tool, when run, may update or create a `requirements.txt` or `requirements-complete.txt`. It's recommended to use the most comprehensive one if available.
    ```bash
    pip install -r requirements-complete.txt
    # Or: pip install -r requirements.txt
    ```

### Ollama Setup
1.  **Verify Ollama is Running:**
    Open your terminal and check if the Ollama service is active:
    ```bash
    ollama list
    ```
    This command should list any models you have already pulled.

2.  **Pull a Code Model:**
    The agent uses a local LLM through Ollama for code analysis. You need to pull a suitable model. `codellama` is the default model used by the agent.
    ```bash
    ollama pull codellama
    ```
    You can also use other models that are effective for coding tasks, such as specific versions like `codellama:7b`, or other models like `mistral` or `llama3`. The model can be specified at runtime using the `--ollama-model` argument.

### GitHub Token
To interact with GitHub (clone private repositories, create branches, push changes, and open Pull Requests), the agent requires a GitHub Personal Access Token (PAT).

1.  **Create a Personal Access Token (PAT):**
    *   Go to your GitHub account settings.
    *   Navigate to `Developer settings` -> `Personal access tokens` -> `Tokens (classic)`.
    *   Click "Generate new token" (or "Generate new token (classic)").
    *   Give your token a descriptive name (e.g., "CodeImprovementAgent").
    *   **Select the `repo` scope.** This scope grants permissions for accessing and modifying repositories.
    *   Set an expiration date for the token as per your security policies.
    *   Click "Generate token" and **copy the token immediately**. You won't be able to see it again.

2.  **Set the Environment Variable:**
    For security and convenience, set your PAT as an environment variable named `GITHUB_TOKEN`.
    ```bash
    export GITHUB_TOKEN="your_copied_pat_here"
    ```
    You can add this line to your shell's configuration file (e.g., `.bashrc`, `.zshrc`) to make it persistent across sessions. Alternatively, you can provide the token directly using the `--token` command-line argument, but using an environment variable is generally recommended.

## 3. Running the Agent

The primary script for running the agent is `run_code_improvement_agent.py` located in the `scripts/` directory.

**Basic Command:**
```bash
python scripts/run_code_improvement_agent.py <repository_url_or_local_path>
```
*   `<repository_url_or_local_path>`: This is a positional argument. It can be a URL to a GitHub repository (e.g., `https://github.com/owner/repo.git`) or a path to a local directory already containing a Git repository.

If the `GITHUB_TOKEN` environment variable is set, the agent will use it automatically. Otherwise, you must provide the token using the `--token` argument.

**Command-Line Arguments:**

*   `repository_url_or_local_path`: (Positional) URL of the GitHub repository or path to a local repository.
*   `--token TEXT`: Your GitHub Personal Access Token. Overrides the `GITHUB_TOKEN` environment variable if both are set.
*   `--owner TEXT`: The owner of the target GitHub repository (e.g., "myusername"). This is optional if the agent can parse it from the repository URL. **Required if you are processing a local repository path and intend for the agent to perform GitHub operations like creating a PR.**
*   `--name TEXT`: The name of the target GitHub repository (e.g., "myproject"). This is optional if the agent can parse it from the repository URL. **Required for local paths if GitHub operations are intended.**
*   `--ollama-model TEXT`: Specifies the Ollama model to be used for analysis.
    *   Default: `codellama`
    *   Example: `--ollama-model codellama:7b`
*   `--dry-run`: If set, the agent will perform the analysis and log intended actions (like creating branches, committing, pushing, or creating PRs) without actually making any remote changes or local commits. Local file modifications by the fixer *will* still occur, allowing you to see proposed changes.
*   `--include TEXT`: Glob pattern for files or directories to *include* in the scan. This argument can be used multiple times to specify several patterns. If omitted, default file extensions (e.g., `.py`, `.js`) are used.
    *   Example: `--include '*.py' --include 'src/**/*.js'`
*   `--exclude TEXT`: Glob pattern for files or directories to *exclude* from the scan. This argument can be used multiple times. Default exclusions for directories like `.git`, `node_modules`, etc., are always applied.
    *   Example: `--exclude '*/tests/*' --exclude 'build/*'`
*   `--min-severity TEXT`: Sets the minimum severity level for issues to be processed and fixed.
    *   Choices: `info`, `low`, `medium`, `high`
    *   Default: `info` (processes all detected issues).
    *   Example: `--min-severity medium`

**Examples:**

1.  **Dry run on a remote repository:**
    ```bash
    python scripts/run_code_improvement_agent.py https://github.com/your-username/your-repo --dry-run
    ```

2.  **Process a local repository, specify owner/name, set minimum severity, and include only Python files:**
    ```bash
    python scripts/run_code_improvement_agent.py /path/to/your/local/repo --owner your-username --name your-repo --min-severity medium --include '*.py'
    ```

3.  **Process a remote repository with a specific Ollama model and exclude test files:**
    ```bash
    python scripts/run_code_improvement_agent.py https://github.com/your-username/another-repo --ollama-model codellama:13b --exclude '*/tests/*'
    ```

## 4. Interpreting Output

*   **Console Logs:** The agent provides verbose logging to the console during its execution. Look for:
    *   Initialization messages for LangChain and Ollama.
    *   Cloning progress (for remote repositories).
    *   Files being scanned by `AutomatedProjectFixer`.
    *   Issues detected and fixes applied (or proposed).
    *   Git operations (branch creation, commits, push) - these will be prefixed with `[DRY RUN]` if `--dry-run` is active.
    *   Pull Request creation status.
    *   Error messages if any step fails.

*   **GitHub Pull Request:** If `dry-run` is not enabled and changes are made and pushed, the agent will attempt to create a Pull Request on GitHub.
    *   The PR title will typically be like "Automated Code Improvements (YYYYMMDDHHMMSS)".
    *   The PR body will contain a brief message indicating it was created by the agent and the branch it originated from.
    *   Review the "Files changed" tab in the PR to see the diffs.

*   **Local Changes:** The `AutomatedProjectFixer` modifies files directly in the local clone of the repository. If you run the agent on a local path, your files will be changed in place (after backups are made by the fixer tool for changed files). If it's a remote repository, these changes occur in a temporary directory where the repo was cloned.

*   **JSON Report (`automated_fix_report_*.json`):** The `AutomatedProjectFixer` generates a JSON report in the root of the processed project (either your local directory or the temporary clone). This report contains:
    *   Start and end times of the fix process.
    *   Number of files processed, issues found, and fixes applied.
    *   A list of files that had issues.
    *   A summary of the fixes.
    *   (Details on specific issues per file may vary based on implementation).

## 5. How it Works (Brief Overview)

1.  **Repository Acquisition:** The `run_code_improvement_agent.py` script either uses the provided local repository path or clones the remote repository URL into a temporary local directory.
2.  **AutomatedProjectFixer Execution:**
    *   An instance of `AutomatedProjectFixer` is created with the project path and other configurations (Ollama model, include/exclude patterns, min severity).
    *   `AutomatedProjectFixer.run_complete_fix()` is called.
    *   This initializes LangChain with the specified Ollama LLM.
    *   It scans project files (respecting include/exclude patterns) using `CodeAnalysisTool`. This tool uses both rule-based checks (e.g., for deprecated imports, security patterns) and potentially the LLM for more nuanced analysis.
    *   Identified issues are filtered by the minimum severity.
    *   `CodeFixerTool` attempts to apply fixes to the issues in the local files.
    *   Dependency checks might be performed and `requirements.txt` potentially updated.
    *   A JSON report summarizing the process is generated.
3.  **Change Detection:** Back in `run_code_improvement_agent.py`, `git status --porcelain` is used to detect if any files were modified by `AutomatedProjectFixer`.
4.  **Git Workflow & PR Creation (if not dry-run):**
    *   If changes are detected:
        *   A new local Git branch is created (e.g., `code-improvements-YYYYMMDDHHMMSS`).
        *   All changed files are added to the Git staging area.
        *   The changes are committed.
        *   If it's not a local repository run (`is_local_run` is false), the new branch is pushed to the remote repository (`origin`). The clone URL is configured with the GitHub token for authentication.
        *   The `GitHubIntegration` class is used to create a Pull Request from the new branch to the repository's default branch (e.g., `main` or `master`).

## 6. Troubleshooting

*   **"Git command not found"**:
    *   Ensure Git is installed on your system.
    *   Verify that the directory containing the Git executable is in your system's PATH environment variable.

*   **"Ollama connection error" / "Model not found" / "Local LLM (Ollama) initialization failed"**:
    *   Make sure the Ollama application or service is running. You can usually check this with `ollama list` in your terminal.
    *   If you specified a model with `--ollama-model`, ensure you have pulled it using `ollama pull <model_name>`.
    *   Check Ollama server logs for more detailed errors.

*   **"GitHub API error" / "401 Unauthorized" / "Failed to clone repository" (with auth errors)**:
    *   Verify that your `GITHUB_TOKEN` environment variable is correctly set or that you are providing a valid token via the `--token` argument.
    *   Ensure the token has the necessary `repo` scope.
    *   If the token has expired, generate a new one.

*   **"Permission denied" when cloning or pushing / "Failed to create pull request"**:
    *   Check that the PAT has the `repo` scope.
    *   Ensure the account associated with the PAT has the required permissions for the target repository (e.g., write access to push branches, permission to create PRs). For organization repositories, ensure third-party application access via PATs is allowed if applicable.

*   **Python Import Errors (e.g., `ImportError: No module named langchain_openai`)**:
    *   Make sure you have installed all dependencies from the `requirements-complete.txt` (or `requirements.txt`) file into the correct Python environment.
    *   Ensure you are running the script using the Python interpreter from the environment where dependencies were installed. Consider using virtual environments (e.g., `venv`, `conda`).

*   **No changes detected after running the fixer:**
    *   Check the `--min-severity` level. If it's too high, legitimate but lower-severity issues might be filtered out.
    *   Verify your `--include` and `--exclude` patterns. They might be too restrictive or incorrect, causing the agent to skip the files you intend to analyze. Check the agent logs for messages about files found after filtering.
    *   The code might genuinely have no issues detectable by the current rules and LLM capabilities.
```
