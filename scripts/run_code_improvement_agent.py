import asyncio
import os
import argparse
import logging
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import shutil
from datetime import datetime

# Attempt to import from src, assuming the script is run from the project root
# or PYTHONPATH is set up.
try:
    from src.ai_agents.automated_langchain_project_fixer import AutomatedProjectFixer
    from src.ai_agents.github_integration import GitHubIntegration
except ImportError:
    logging.warning("Could not import directly from src. Ensure PYTHONPATH is set or run from project root.")
    AutomatedProjectFixer = None
    GitHubIntegration = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CodeImprovementAgentRunner")

async def process_repository(project_path_str: str, github_token: str, repo_owner: str, repo_name: str,
                             is_local_run: bool, ollama_model_name: str, dry_run: bool,
                             include_patterns: Optional[List[str]], exclude_patterns: Optional[List[str]],
                             min_severity: str):
    project_path = Path(project_path_str)
    logger.info(f"Processing repository at: {project_path} using Ollama model: {ollama_model_name}, min severity: {min_severity}")
    if dry_run:
        logger.info("🌵 DRY RUN active. No remote changes will be made. Git operations will be logged.")

    if not AutomatedProjectFixer or not GitHubIntegration:
        logger.error("Core classes AutomatedProjectFixer or GitHubIntegration not loaded in process_repository. Exiting.")
        return

    # 1. Run AutomatedProjectFixer
    logger.info("Initializing AutomatedProjectFixer...")
    project_fixer = AutomatedProjectFixer(
        project_root=str(project_path),
        ollama_model_name=ollama_model_name,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        min_severity=min_severity
    )

    try:
        logger.info("Starting project fix process...")
        report_file_path = await project_fixer.run_complete_fix()
        logger.info(f"AutomatedProjectFixer completed. Report generated at: {report_file_path}")
    except Exception as e:
        logger.error(f"Error running AutomatedProjectFixer on {project_path}: {e}")
        return # Stop processing this repo if fixer fails

    try:
        # Git status
        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=project_path, check=True, capture_output=True, text=True)
        if not status_result.stdout.strip():
            logger.info(f"No changes in {project_path} after fixer. Nothing to commit.")
            return

        logger.info(f"Changes detected in {project_path}:\n{status_result.stdout.strip()}")

        # Git branch
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        branch_name = f"code-improvements-{timestamp}"
        if not dry_run:
            try:
                subprocess.run(["git", "checkout", "-b", branch_name], cwd=project_path, check=True, capture_output=True)
                logger.info(f"Created and switched to new branch: {branch_name} in {project_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create branch {branch_name} in {project_path}. Stderr: {e.stderr.decode(errors='ignore')}")
                # Attempt to switch to it if it already exists (e.g. from a previous failed run partway)
                try:
                    subprocess.run(["git", "checkout", branch_name], cwd=project_path, check=True, capture_output=True)
                    logger.info(f"Switched to existing branch: {branch_name} in {project_path}")
                except subprocess.CalledProcessError as e_checkout:
                    logger.error(f"Failed to switch to branch {branch_name} in {project_path}. Stderr: {e_checkout.stderr.decode(errors='ignore')}")
                    return
        else:
            logger.info(f"[DRY RUN] Would create and switch to new branch: {branch_name} in {project_path}")

        # Git add (all changes)
        if not dry_run:
            subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
            logger.info(f"Added all changes to staging in {project_path}")
        else:
            logger.info(f"[DRY RUN] Would add all changes to staging in {project_path}")

        # Git commit
        commit_message = f"Automated code improvements by CodeImprovementAgent ({timestamp})"
        if not dry_run:
            subprocess.run(["git", "commit", "-m", commit_message], cwd=project_path, check=True, capture_output=True)
            logger.info(f"Committed changes in {project_path} with message: '{commit_message}'")
        else:
            logger.info(f"[DRY RUN] Would commit changes in {project_path} with message: '{commit_message}'")

        gh_integration = GitHubIntegration(github_token, repo_owner, repo_name)

        # Git push and PR creation
        if not is_local_run:
            if not dry_run:
                logger.info(f"Pushing branch {branch_name} to origin for {project_path}...")
                subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=project_path, check=True, capture_output=True)
                logger.info(f"Successfully pushed branch {branch_name} to remote for {repo_owner}/{repo_name}")

                # Create PR
                pr_title = f"Automated Code Improvements ({timestamp})"
                pr_body = (f"This PR contains automated code improvements by the Code Improvement Agent.\n\n"
                           f"Branch: `{branch_name}`\n"
                           f"Timestamp: {timestamp}\n\n"
                           f"Please review the changes carefully.")

                # Determine base branch (common defaults)
                base_branch = "main" # Default base branch
                try:
                    # Attempt to get the default branch from remote
                    remote_head_ref_result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=project_path, capture_output=True, text=True, check=True)
                    remote_default_branch = remote_head_ref_result.stdout.strip().split('/')[-1]
                    if remote_default_branch:
                        base_branch = remote_default_branch
                        logger.info(f"Detected default remote branch: {base_branch}")
                    else: # Fallback if detection is not as expected
                         logger.warning(f"Could not reliably detect default remote branch, defaulting to '{base_branch}'. Output: {remote_head_ref_result.stdout.strip()}")

                except subprocess.CalledProcessError as e:
                    logger.warning(f"Could not detect default remote branch, defaulting to '{base_branch}'. Error: {e.stderr}")

                logger.info(f"Attempting to create Pull Request from {branch_name} to {base_branch} for {repo_owner}/{repo_name}")
                pr_url = await gh_integration.create_pull_request(
                    branch_name,
                    base_branch,
                    pr_title,
                    pr_body
                )
                if pr_url:
                    logger.info(f"Pull request created successfully: {pr_url}")
                else:
                    logger.error(f"Failed to create pull request for branch {branch_name}.")
            else:
                logger.info(f"[DRY RUN] Would push branch {branch_name} to remote for {repo_owner}/{repo_name}")
                logger.info(f"[DRY RUN] Would create Pull Request from {branch_name} for {repo_owner}/{repo_name}")
        else:
            if dry_run:
                logger.info(f"[DRY RUN] Running on a local path {project_path}. Git operations (branch, add, commit) logged above. No push or PR.")
            else:
                logger.info(f"Running on a local path {project_path}. Skipping 'git push' and Pull Request creation.")
                logger.info(f"Branch '{branch_name}' created locally with commits. Please push manually and create PR if desired.")

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed in {project_path}: {e.cmd}. Stdout: {e.stdout.decode(errors='ignore') if e.stdout else 'N/A'}. Stderr: {e.stderr.decode(errors='ignore') if e.stderr else 'N/A'}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the Git workflow for {project_path}: {e}", exc_info=True)


async def main(repo_url_or_path: str, github_token: str,
             target_repo_owner: str = None, target_repo_name: str = None,
             ollama_model_name: str = "codellama", dry_run: bool = False,
             include_patterns: Optional[List[str]] = None,
             exclude_patterns: Optional[List[str]] = None,
             min_severity: str = "info"):
    if not AutomatedProjectFixer or not GitHubIntegration:
        logger.error("Core classes AutomatedProjectFixer or GitHubIntegration not loaded. Exiting.")
        logger.error("Please ensure you run this script from the project root or have set up PYTHONPATH correctly.")
        return

    is_local_path = Path(repo_url_or_path).is_dir()

    if is_local_path:
        if not target_repo_owner or not target_repo_name:
            logger.error("For local paths, --target-repo-owner and --target-repo-name must be specified for GitHub operations.")
            return
        project_path_str = str(Path(repo_url_or_path).resolve())
        # For local paths, we assume the .git directory is properly configured if git operations are to succeed.
        # The 'is_local_run=True' flag will prevent push and PR creation by default.
        await process_repository(project_path_str, github_token, target_repo_owner, target_repo_name,
                                 True, ollama_model_name, dry_run, include_patterns, exclude_patterns, min_severity)
    else: # Git URL
        parsed_url = urlparse(repo_url_or_path)
        path_parts = parsed_url.path.strip('/').split('/')

        owner_from_url = path_parts[-2] if len(path_parts) >= 2 else None
        name_from_url = path_parts[-1].replace('.git', '') if len(path_parts) >= 2 else None

        final_repo_owner = target_repo_owner or owner_from_url
        final_repo_name = target_repo_name or name_from_url

        if not final_repo_owner or not final_repo_name:
            logger.error(f"Could not determine repository owner/name from URL {repo_url_or_path}. Please specify with --owner and --name.")
            return

        with tempfile.TemporaryDirectory(prefix="code_agent_") as temp_dir:
            project_path_to_clone_into = str(Path(temp_dir) / final_repo_name)
            logger.info(f"Cloning {repo_url_or_path} into {project_path_to_clone_into}")

            clone_url = repo_url_or_path
            if github_token and parsed_url.scheme == 'https': # Assumes HTTPS URL
                # Ensure the token is part of the URL for private repositories
                clone_url = f"https://oauth2:{github_token}@{parsed_url.netloc}{parsed_url.path}"

            try:
                # Clone the specific repository into the designated subfolder within temp_dir
                subprocess.run(["git", "clone", clone_url, project_path_to_clone_into], check=True, capture_output=True)
                logger.info(f"Successfully cloned {final_repo_owner}/{final_repo_name} to {project_path_to_clone_into}")
                await process_repository(project_path_to_clone_into, github_token, final_repo_owner, final_repo_name,
                                         False, ollama_model_name, dry_run, include_patterns, exclude_patterns, min_severity)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository: {e.cmd}. Stdout: {e.stdout.decode(errors='ignore') if e.stdout else 'N/A'}. Stderr: {e.stderr.decode(errors='ignore') if e.stderr else 'N/A'}")
            except FileNotFoundError:
                logger.error("Git command not found. Ensure Git is installed and in your PATH.")
            except Exception as e:
                logger.error(f"An unexpected error occurred during cloning or processing of {repo_url_or_path}: {e}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Automated Code Improvement Agent.")
    parser.add_argument("repo_url_or_path", help="URL of the GitHub repository or path to a local repository.")
    parser.add_argument("--token", help="GitHub token. If not provided, defaults to GITHUB_TOKEN env var.", default=os.getenv("GITHUB_TOKEN"))
    parser.add_argument("--owner", help="GitHub repository owner. Parsed from URL if not provided for remote repos. Required for local paths.")
    parser.add_argument("--name", help="GitHub repository name. Parsed from URL if not provided for remote repos. Required for local paths.")
    parser.add_argument(
        "--ollama-model",
        default="codellama",
        help="Name of the Ollama model to use (e.g., 'codellama', 'codellama:7b'). Default is 'codellama'."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run. Analyze and log intended actions without making remote changes (no push, no PR)."
    )
    parser.add_argument(
        "--include",
        action="append", # Allows multiple --include arguments
        help="Glob pattern for files/directories to include (e.g., '*.py', 'src/**/*.js'). Can be used multiple times."
    )
    parser.add_argument(
        "--exclude",
        action="append", # Allows multiple --exclude arguments
        help="Glob pattern for files/directories to exclude (e.g., '*/test/*', 'data/*'). Can be used multiple times."
    )
    parser.add_argument(
        "--min-severity",
        default="info",
        choices=["info", "low", "medium", "high"],
        help="Minimum severity of issues to report and fix. Default is 'info'."
    )

    args = parser.parse_args()

    if not args.token:
        logger.error("GitHub token not provided via --token argument or GITHUB_TOKEN environment variable.")
        exit(1)

    if not AutomatedProjectFixer or not GitHubIntegration:
        logger.error("AutomatedProjectFixer or GitHubIntegration classes not available. Check imports and PYTHONPATH.")
        exit(1)

    asyncio.run(main(args.repo_url_or_path, args.token, args.owner, args.name,
                     args.ollama_model, args.dry_run, args.include, args.exclude, args.min_severity))
