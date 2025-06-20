#!/usr/bin/env python3
"""
GitHub Integration for Automatic Error Handling
Provides capabilities to create issues, PRs, and automated fixes
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
import json
import base64

logger = logging.getLogger("GitHubIntegration")

class GitHubIntegration:
    """GitHub integration for automated error handling and code fixes"""
    
    def __init__(self, github_token: str, repo_owner: str = None, repo_name: str = None):
        self.github_token = github_token
        self.repo_owner = repo_owner or "your-username"  # Configure this
        self.repo_name = repo_name or "flash-loan-system"  # Configure this
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "FlashLoan-Orchestrator/1.0"
        }
    
    async def create_error_issue(self, error: Exception, context: str, stack_trace: str = None) -> Optional[str]:
        """Create a GitHub issue for an error"""
        try:
            issue_title = f"🚨 Automatic Error Report: {type(error).__name__} in {context}"
            issue_body = self._generate_error_issue_body(error, context, stack_trace)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues"
                
                payload = {
                    "title": issue_title,
                    "body": issue_body,
                    "labels": ["bug", "automatic", "orchestrator", context.replace("_", "-")]
                }
                
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status == 201:
                        result = await response.json()
                        issue_url = result.get("html_url")
                        logger.info(f"✅ Created GitHub issue: {issue_url}")
                        return issue_url
                    else:
                        logger.error(f"❌ Failed to create GitHub issue: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return None
    
    async def create_fix_pull_request(self, error_context: str, fix_description: str, file_changes: Dict[str, str]) -> Optional[str]:
        """Create a pull request with automated fixes"""
        try:
            branch_name = f"auto-fix-{error_context}-{int(datetime.now().timestamp())}"
            
            # Create branch
            if not await self._create_branch(branch_name):
                return None
            
            # Apply file changes
            for file_path, new_content in file_changes.items():
                if not await self._update_file(file_path, new_content, branch_name, f"Auto-fix: {fix_description}"):
                    logger.error(f"Failed to update file: {file_path}")
            
            # Create pull request
            pr_url = await self._create_pull_request(
                branch_name,
                f"🔧 Auto-fix: {fix_description}",
                self._generate_fix_pr_body(error_context, fix_description, file_changes)
            )
            
            if pr_url:
                logger.info(f"✅ Created fix PR: {pr_url}")
            
            return pr_url
            
        except Exception as e:
            logger.error(f"Failed to create fix PR: {e}")
            return None
    
    async def get_repository_files(self, path: str = "") -> List[Dict[str, Any]]:
        """Get repository file structure"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get repository files: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to get repository files: {e}")
            return []
    
    async def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a specific file"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = base64.b64decode(result["content"]).decode('utf-8')
                        return content
                    else:
                        logger.error(f"Failed to get file content: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            return None
    
    async def _create_branch(self, branch_name: str) -> bool:
        """Create a new branch"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get main branch SHA
                main_url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/git/refs/heads/main"
                async with session.get(main_url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get main branch SHA: {response.status}")
                        return False
                    
                    main_data = await response.json()
                    main_sha = main_data["object"]["sha"]
                
                # Create new branch
                branch_url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/git/refs"
                payload = {
                    "ref": f"refs/heads/{branch_name}",
                    "sha": main_sha
                }
                
                async with session.post(branch_url, headers=self.headers, json=payload) as response:
                    if response.status == 201:
                        logger.info(f"✅ Created branch: {branch_name}")
                        return True
                    else:
                        logger.error(f"❌ Failed to create branch: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            return False
    
    async def _update_file(self, file_path: str, content: str, branch_name: str, commit_message: str) -> bool:
        """Update a file in the repository"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get current file SHA
                file_url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
                async with session.get(file_url, headers=self.headers) as response:
                    file_sha = None
                    if response.status == 200:
                        file_data = await response.json()
                        file_sha = file_data["sha"]
                
                # Update file
                payload = {
                    "message": commit_message,
                    "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                    "branch": branch_name
                }
                
                if file_sha:
                    payload["sha"] = file_sha
                
                async with session.put(file_url, headers=self.headers, json=payload) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Updated file: {file_path}")
                        return True
                    else:
                        logger.error(f"❌ Failed to update file: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to update file: {e}")
            return False
    
    async def _create_pull_request(self, branch_name: str, title: str, body: str) -> Optional[str]:
        """Create a pull request"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls"
                
                payload = {
                    "title": title,
                    "body": body,
                    "head": branch_name,
                    "base": "main"
                }
                
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status == 201:
                        result = await response.json()
                        return result.get("html_url")
                    else:
                        logger.error(f"Failed to create PR: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None
    
    def _generate_error_issue_body(self, error: Exception, context: str, stack_trace: str = None) -> str:
        """Generate issue body for error reports"""
        body = f"""## 🚨 Automatic Error Report

**Error Type:** `{type(error).__name__}`
**Context:** `{context}`
**Timestamp:** `{datetime.now().isoformat()}`

### Error Details
```
{str(error)}
```

### Context Information
- **Service:** Enhanced LangChain Orchestrator
- **Component:** {context}
- **Environment:** Docker Container
- **Auto-reported:** Yes

### Stack Trace
```python
{stack_trace or "Stack trace not available"}
```

### Suggested Actions
- [ ] Investigate root cause
- [ ] Implement error handling improvements
- [ ] Add monitoring for this error type
- [ ] Test fix in development environment

### System Status
This error was automatically detected and reported by the Enhanced LangChain Orchestrator's error handling system.

**Generated by:** FlashLoan Orchestrator v1.0
"""
        return body
    
    def _generate_fix_pr_body(self, error_context: str, fix_description: str, file_changes: Dict[str, str]) -> str:
        """Generate PR body for automated fixes"""
        files_list = "\n".join([f"- `{file_path}`" for file_path in file_changes.keys()])
        
        body = f"""## 🔧 Automated Fix

**Context:** `{error_context}`
**Fix Description:** {fix_description}

### Changes Made
{files_list}

### Fix Details
This pull request contains automated fixes generated by the Enhanced LangChain Orchestrator's error handling system.

### Testing
- [ ] Automated tests pass
- [ ] Manual testing completed
- [ ] No regression issues identified

### Deployment
- [ ] Ready for staging deployment
- [ ] Ready for production deployment

**Auto-generated by:** FlashLoan Orchestrator v1.0
**Timestamp:** {datetime.now().isoformat()}
"""
        return body

    async def search_similar_issues(self, error_type: str, context: str) -> List[Dict[str, Any]]:
        """Search for similar issues in the repository"""
        try:
            query = f"repo:{self.repo_owner}/{self.repo_name} is:issue {error_type} {context}"
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search/issues"
                params = {"q": query, "sort": "updated", "order": "desc"}
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("items", [])
                    else:
                        logger.error(f"Failed to search issues: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to search similar issues: {e}")
            return []
