#!/usr/bin/env python3
"""
Master Project Organizer with MCP Server and AI Agent Integration
================================================================

This script organizes the entire flash loan project by:
1. Removing duplicate files intelligently
2. Fixing syntax errors in all Python scripts
3. Organizing directory structure
4. Integrating all MCP servers and AI agents
5. Creating unified configuration files
6. Generating deployment ready structure

Author: GitHub Copilot Assistant
Date: June 17, 2025
"""

import asyncio
import logging
import json
import os
import sys
import shutil
import hashlib
import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Tuple
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_organization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterProjectOrganizer:
    """Master project organizer with MCP and AI integration"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.duplicates_found = defaultdict(list)
        self.syntax_errors = []
        self.organized_files = 0
        self.mcp_servers = []
        self.ai_agents = []
        self.fixed_files = []
        
        # Define clean directory structure
        self.target_structure = {
            'src': {
                'contracts': [],
                'scripts': [],
                'tests': [],
                'mcp_servers': [],
                'ai_agents': [],
                'utilities': [],
                'integrations': []
            },
            'config': [],
            'docs': [],
            'archive': {
                'duplicates': [],
                'backups': [],
                'old_versions': []
            },
            'deployment': {
                'production': [],
                'staging': [],
                'development': []
            }
        }
    
    async def organize_project(self):
        """Main organization method"""
        logger.info("🚀 Starting Master Project Organization")
        logger.info("=" * 60)
        
        try:
            # Step 1: Analyze current structure
            await self._analyze_current_structure()
            
            # Step 2: Find and remove duplicates
            await self._find_and_handle_duplicates()
            
            # Step 3: Fix syntax errors
            await self._fix_syntax_errors()
            
            # Step 4: Organize directory structure
            await self._organize_directory_structure()
            
            # Step 5: Integrate MCP servers
            await self._integrate_mcp_servers()
            
            # Step 6: Integrate AI agents
            await self._integrate_ai_agents()
            
            # Step 7: Create unified configurations
            await self._create_unified_configurations()
            
            # Step 8: Generate final report
            await self._generate_organization_report()
            
            logger.info("✅ Project organization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Organization failed: {e}")
            raise
    
    async def _analyze_current_structure(self):
        """Analyze current project structure"""
        logger.info("📊 Analyzing current project structure...")
        
        # Count files by type
        file_counts = defaultdict(int)
        total_files = 0
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                total_files += 1
                suffix = file_path.suffix.lower()
                file_counts[suffix] += 1
                
                # Identify MCP servers and AI agents
                if "mcp" in str(file_path).lower() and file_path.suffix == ".py":
                    self.mcp_servers.append(file_path)
                elif "ai" in str(file_path).lower() and file_path.suffix == ".py":
                    self.ai_agents.append(file_path)
        
        logger.info(f"📁 Total files: {total_files}")
        logger.info(f"🔧 MCP servers found: {len(self.mcp_servers)}")
        logger.info(f"🤖 AI agents found: {len(self.ai_agents)}")
        
        for suffix, count in sorted(file_counts.items()):
            if count > 5:  # Only show common file types
                logger.info(f"   {suffix}: {count} files")
    
    async def _find_and_handle_duplicates(self):
        """Find and handle duplicate files"""
        logger.info("🔍 Finding duplicate files...")
        
        file_hashes = defaultdict(list)
        
        # Calculate file hashes
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not any(skip in str(file_path) for skip in 
                                             ['.git', 'node_modules', '__pycache__', '.vscode']):
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        file_hashes[file_hash].append(file_path)
                except (IOError, OSError):
                    continue
        
        # Find duplicates
        duplicates_count = 0
        for file_hash, files in file_hashes.items():
            if len(files) > 1:
                duplicates_count += len(files) - 1
                self.duplicates_found[file_hash] = files
        
        logger.info(f"📋 Found {duplicates_count} duplicate files in {len(self.duplicates_found)} groups")
        
        # Handle duplicates
        await self._handle_duplicates()
    
    async def _handle_duplicates(self):
        """Handle duplicate files intelligently"""
        if not self.duplicates_found:
            return
        
        duplicates_dir = self.project_root / "archive" / "duplicates"
        duplicates_dir.mkdir(parents=True, exist_ok=True)
        
        removed_count = 0
        
        for file_hash, files in self.duplicates_found.items():
            # Keep the file in the most appropriate location
            best_file = self._choose_best_duplicate(files)
            
            for file_path in files:
                if file_path != best_file:
                    # Move duplicate to archive
                    relative_path = file_path.relative_to(self.project_root)
                    archive_path = duplicates_dir / relative_path
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.move(str(file_path), str(archive_path))
                        removed_count += 1
                        logger.info(f"🗑️  Moved duplicate: {relative_path}")
                    except Exception as e:
                        logger.warning(f"Failed to move {file_path}: {e}")
        
        logger.info(f"✅ Removed {removed_count} duplicate files")
    
    def _choose_best_duplicate(self, files: List[Path]) -> Path:
        """Choose the best file to keep from duplicates"""
        # Prioritize files in main directories over backup/archive directories
        priority_keywords = ['src', 'contracts', 'scripts', 'mcp_servers']
        avoid_keywords = ['backup', 'archive', 'old', 'temp', 'duplicate']
        
        scored_files = []
        for file_path in files:
            score = 0
            path_str = str(file_path).lower()
            
            # Positive score for priority keywords
            for keyword in priority_keywords:
                if keyword in path_str:
                    score += 10
            
            # Negative score for avoid keywords
            for keyword in avoid_keywords:
                if keyword in path_str:
                    score -= 20
            
            # Prefer shorter paths (less nested)
            score -= len(file_path.parts)
            
            scored_files.append((score, file_path))
        
        # Return file with highest score
        return max(scored_files, key=lambda x: x[0])[1]
    
    async def _fix_syntax_errors(self):
        """Fix syntax errors in Python files"""
        logger.info("🔧 Fixing syntax errors in Python files...")
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['.git', 'node_modules', '__pycache__', 'archive']):
                continue
            
            try:
                await self._fix_file_syntax(py_file)
            except Exception as e:
                logger.warning(f"Failed to fix {py_file}: {e}")
        
        logger.info(f"✅ Fixed syntax in {len(self.fixed_files)} files")
    
    async def _fix_file_syntax(self, file_path: Path):
        """Fix syntax errors in a specific file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for syntax errors
            try:
                ast.parse(content)
                return  # No syntax errors
            except SyntaxError as e:
                logger.info(f"🔍 Fixing syntax error in {file_path.name}: {e}")
            
            # Common fixes
            fixed_content = content
            
            # Fix common import issues
            fixed_content = self._fix_import_issues(fixed_content)
            
            # Fix indentation issues
            fixed_content = self._fix_indentation_issues(fixed_content)
            
            # Fix type annotation issues
            fixed_content = self._fix_type_annotation_issues(fixed_content)
            
            # Fix async/await issues
            fixed_content = self._fix_async_issues(fixed_content)
            
            # Verify the fix worked
            try:
                ast.parse(fixed_content)
                
                # Create backup
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                shutil.copy2(file_path, backup_path)
                
                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                self.fixed_files.append(file_path)
                logger.info(f"✅ Fixed: {file_path.name}")
                
            except SyntaxError:
                logger.warning(f"⚠️  Could not fix syntax in {file_path.name}")
                
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")
    
    def _fix_import_issues(self, content: str) -> str:
        """Fix common import issues"""
        # Fix missing imports
        if "Union" in content and "from typing import" in content:
            if "Union" not in content.split("from typing import")[1].split("\n")[0]:
                content = content.replace(
                    "from typing import",
                    "from typing import Union,"
                )
        
        # Fix duplicate imports
        lines = content.split('\n')
        seen_imports = set()
        fixed_lines = []
        
        for line in lines:
            if line.startswith(('import ', 'from ')):
                if line not in seen_imports:
                    seen_imports.add(line)
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_indentation_issues(self, content: str) -> str:
        """Fix indentation issues"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Convert tabs to spaces
            if '\t' in line:
                line = line.replace('\t', '    ')
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_type_annotation_issues(self, content: str) -> str:
        """Fix type annotation issues"""
        # Fix missing type imports
        if "Dict" in content and "from typing import" in content:
            if "Dict" not in content.split("from typing import")[1].split("\n")[0]:
                content = content.replace(
                    "from typing import",
                    "from typing import Dict,"
                )
        
        if "List" in content and "from typing import" in content:
            if "List" not in content.split("from typing import")[1].split("\n")[0]:
                content = content.replace(
                    "from typing import",
                    "from typing import List,"
                )
        
        return content
    
    def _fix_async_issues(self, content: str) -> str:
        """Fix async/await issues"""
        # Add async to functions that use await
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if "await " in line and i > 0:
                # Check if the function definition above is async
                for j in range(i-1, -1, -1):
                    if lines[j].strip().startswith("def "):
                        if "async " not in lines[j]:
                            lines[j] = lines[j].replace("def ", "async def ")
                        break
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    async def _organize_directory_structure(self):
        """Organize directory structure"""
        logger.info("📁 Organizing directory structure...")
        
        # Create target directories
        for dir_name, subdirs in self.target_structure.items():
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            
            if isinstance(subdirs, dict):
                for subdir_name in subdirs:
                    subdir_path = dir_path / subdir_name
                    subdir_path.mkdir(exist_ok=True)
        
        # Move files to appropriate locations
        await self._move_files_to_structure()
        
        logger.info("✅ Directory structure organized")
    
    async def _move_files_to_structure(self):
        """Move files to appropriate directory structure"""
        moves_count = 0
        
        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file():
                continue
            
            if any(skip in str(file_path) for skip in ['.git', 'node_modules', 'archive', 'src']):
                continue
            
            target_dir = self._determine_target_directory(file_path)
            if target_dir:
                target_path = self.project_root / target_dir / file_path.name
                
                # Avoid moving if already in correct location
                if target_path.parent == file_path.parent:
                    continue
                
                try:
                    # Ensure target directory exists
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Handle naming conflicts
                    if target_path.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_path = target_path.with_stem(f"{target_path.stem}_{timestamp}")
                    
                    shutil.move(str(file_path), str(target_path))
                    moves_count += 1
                    logger.info(f"📦 Moved: {file_path.name} → {target_dir}")
                    
                except Exception as e:
                    logger.warning(f"Failed to move {file_path.name}: {e}")
        
        logger.info(f"📦 Moved {moves_count} files to organized structure")
    
    def _determine_target_directory(self, file_path: Path) -> Optional[str]:
        """Determine target directory for a file"""
        filename = file_path.name.lower()
        path_str = str(file_path).lower()
        
        # Contract files
        if file_path.suffix == '.sol':
            return 'src/contracts'
        
        # Script files
        if file_path.suffix in ['.js', '.ts'] and any(keyword in filename for keyword in ['deploy', 'setup', 'verify', 'script']):
            return 'src/scripts'
        
        # Test files
        if file_path.suffix in ['.js', '.ts', '.py'] and 'test' in filename:
            return 'src/tests'
        
        # MCP servers
        if 'mcp' in path_str and file_path.suffix == '.py':
            return 'src/mcp_servers'
        
        # AI agents
        if 'ai' in path_str and file_path.suffix == '.py':
            return 'src/ai_agents'
        
        # Configuration files
        if file_path.suffix in ['.json', '.yaml', '.yml', '.env'] and any(keyword in filename for keyword in ['config', 'settings']):
            return 'config'
        
        # Documentation
        if file_path.suffix in ['.md', '.txt', '.rst']:
            return 'docs'
        
        # Python utilities
        if file_path.suffix == '.py' and any(keyword in filename for keyword in ['util', 'helper', 'tool']):
            return 'src/utilities'
        
        return None
    
    async def _integrate_mcp_servers(self):
        """Integrate all MCP servers"""
        logger.info("🔗 Integrating MCP servers...")
        
        mcp_dir = self.project_root / "src" / "mcp_servers"
        mcp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unified MCP configuration
        mcp_config = {
            "servers": {},
            "global_configuration": {
                "health_check_interval": 30,
                "auto_restart": True,
                "log_level": "INFO"
            }
        }
        
        server_id = 3000
        for mcp_file in self.mcp_servers:
            if mcp_file.exists():
                server_name = mcp_file.stem.replace('_mcp_server', '').replace('mcp_', '')
                
                mcp_config["servers"][server_name] = {
                    "name": server_name,
                    "type": "python",
                    "path": f"src/mcp_servers/{mcp_file.name}",
                    "port": server_id,
                    "enabled": True,
                    "auto_restart": True,
                    "environment_variables": {
                        "MCP_SERVER_NAME": server_name,
                        "PORT": str(server_id)
                    }
                }
                server_id += 1
        
        # Save MCP configuration
        config_path = self.project_root / "config" / "unified_mcp_config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        
        logger.info(f"✅ Integrated {len(mcp_config['servers'])} MCP servers")
    
    async def _integrate_ai_agents(self):
        """Integrate all AI agents"""
        logger.info("🤖 Integrating AI agents...")
        
        ai_dir = self.project_root / "src" / "ai_agents"
        ai_dir.mkdir(parents=True, exist_ok=True)
        
        # Create AI agent configuration
        ai_config = {
            "agents": {},
            "coordination": {
                "master_coordinator": "src/ai_agents/master_coordinator.py",
                "communication_protocol": "http",
                "task_distribution": "round_robin"
            }
        }
        
        port = 5000
        for ai_file in self.ai_agents:
            if ai_file.exists():
                agent_name = ai_file.stem.replace('_ai_agent', '').replace('ai_', '')
                
                ai_config["agents"][agent_name] = {
                    "name": agent_name,
                    "file": f"src/ai_agents/{ai_file.name}",
                    "port": port,
                    "role": self._determine_agent_role(agent_name),
                    "capabilities": self._determine_agent_capabilities(agent_name)
                }
                port += 1
        
        # Save AI configuration
        config_path = self.project_root / "config" / "ai_agents_config.json"
        
        with open(config_path, 'w') as f:
            json.dump(ai_config, f, indent=2)
        
        logger.info(f"✅ Integrated {len(ai_config['agents'])} AI agents")
    
    def _determine_agent_role(self, agent_name: str) -> str:
        """Determine role for AI agent"""
        if 'coordinator' in agent_name:
            return 'coordination'
        elif 'analyzer' in agent_name or 'analysis' in agent_name:
            return 'analysis'
        elif 'executor' in agent_name or 'trading' in agent_name:
            return 'execution'
        elif 'monitor' in agent_name:
            return 'monitoring'
        else:
            return 'general'
    
    def _determine_agent_capabilities(self, agent_name: str) -> List[str]:
        """Determine capabilities for AI agent"""
        capabilities = []
        
        if 'flash' in agent_name or 'loan' in agent_name:
            capabilities.extend(['flash_loan_analysis', 'arbitrage_detection'])
        
        if 'trading' in agent_name:
            capabilities.extend(['trading_execution', 'order_management'])
        
        if 'risk' in agent_name:
            capabilities.extend(['risk_assessment', 'portfolio_analysis'])
        
        if 'monitor' in agent_name:
            capabilities.extend(['system_monitoring', 'alert_management'])
        
        return capabilities or ['general_ai_assistance']
    
    async def _create_unified_configurations(self):
        """Create unified configuration files"""
        logger.info("⚙️  Creating unified configurations...")
        
        config_dir = self.project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Master configuration
        master_config = {
            "project": {
                "name": "Flash Loan Arbitrage System",
                "version": "1.0.0",
                "description": "Automated flash loan arbitrage trading system"
            },
            "environment": {
                "development": {
                    "rpc_url": "http://localhost:8545",
                    "network": "hardhat"
                },
                "staging": {
                    "rpc_url": "${POLYGON_MUMBAI_RPC_URL}",
                    "network": "mumbai"
                },
                "production": {
                    "rpc_url": "${POLYGON_RPC_URL}",
                    "network": "polygon"
                }
            },
            "services": {
                "mcp_servers": "config/unified_mcp_config.json",
                "ai_agents": "config/ai_agents_config.json",
                "database": "config/database_config.json"
            }
        }
        
        with open(config_dir / "master_config.json", 'w') as f:
            json.dump(master_config, f, indent=2)
        
        # Package.json update
        await self._update_package_json()
        
        logger.info("✅ Unified configurations created")
    
    async def _update_package_json(self):
        """Update package.json with new scripts"""
        package_json_path = self.project_root / "package.json"
        
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Add new scripts
            new_scripts = {
                "organize": "python master_project_organizer.py",
                "start:mcp": "python src/mcp_servers/unified_mcp_coordinator.py",
                "start:ai": "python src/ai_agents/master_coordinator.py",
                "deploy:all": "npm run compile && npm run deploy:ai && npm run setup:mcp",
                "test:all": "npm run test && python -m pytest src/tests/",
                "lint:fix": "python -m flake8 --max-line-length=120 src/ && eslint src/ --fix"
            }
            
            package_data["scripts"].update(new_scripts)
            
            # Add dependencies
            new_dependencies = {
                "axios": "^1.6.0",
                "ws": "^8.14.0",
                "express": "^4.18.0",
                "cors": "^2.8.5"
            }
            
            if "dependencies" not in package_data:
                package_data["dependencies"] = {}
            
            package_data["dependencies"].update(new_dependencies)
            
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
    
    async def _generate_organization_report(self):
        """Generate final organization report"""
        logger.info("📊 Generating organization report...")
        
        report = {
            "organization_date": datetime.now().isoformat(),
            "summary": {
                "duplicates_removed": sum(len(files) - 1 for files in self.duplicates_found.values()),
                "syntax_errors_fixed": len(self.fixed_files),
                "files_organized": self.organized_files,
                "mcp_servers_integrated": len(self.mcp_servers),
                "ai_agents_integrated": len(self.ai_agents)
            },
            "duplicates_found": {
                file_hash: [str(f) for f in files] 
                for file_hash, files in self.duplicates_found.items()
            },
            "syntax_fixes": [str(f) for f in self.fixed_files],
            "mcp_servers": [str(f) for f in self.mcp_servers],
            "ai_agents": [str(f) for f in self.ai_agents],
            "recommendations": [
                "Run 'npm install' to install new dependencies",
                "Update .env file with required environment variables",
                "Test MCP servers with 'npm run start:mcp'",
                "Test AI agents with 'npm run start:ai'",
                "Run full deployment with 'npm run deploy:all'"
            ]
        }
        
        # Save report
        reports_dir = self.project_root / "docs" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"organization_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown summary
        await self._generate_markdown_summary(report, reports_dir / f"ORGANIZATION_SUMMARY_{timestamp}.md")
        
        logger.info(f"📋 Organization report saved to: {report_path}")
    
    async def _generate_markdown_summary(self, report: Dict, output_path: Path):
        """Generate markdown summary report"""
        markdown_content = f"""# Project Organization Summary

**Date:** {report['organization_date']}

## Summary

- **Duplicates Removed:** {report['summary']['duplicates_removed']}
- **Syntax Errors Fixed:** {report['summary']['syntax_errors_fixed']}
- **Files Organized:** {report['summary']['files_organized']}
- **MCP Servers Integrated:** {report['summary']['mcp_servers_integrated']}
- **AI Agents Integrated:** {report['summary']['ai_agents_integrated']}

## Project Structure

```
flash-loan/
├── src/
│   ├── contracts/          # Solidity contracts
│   ├── scripts/           # Deployment and setup scripts
│   ├── tests/             # Test files
│   ├── mcp_servers/       # MCP server implementations
│   ├── ai_agents/         # AI agent implementations
│   ├── utilities/         # Utility functions
│   └── integrations/      # Third-party integrations
├── config/                # Configuration files
├── docs/                  # Documentation
├── deployment/            # Deployment configurations
└── archive/              # Archived/backup files
```

## Next Steps

{chr(10).join(f"- {rec}" for rec in report['recommendations'])}

## MCP Servers

{chr(10).join(f"- {server}" for server in report['mcp_servers'][:10])}
{f"... and {len(report['mcp_servers']) - 10} more" if len(report['mcp_servers']) > 10 else ""}

## AI Agents

{chr(10).join(f"- {agent}" for agent in report['ai_agents'][:10])}
{f"... and {len(report['ai_agents']) - 10} more" if len(report['ai_agents']) > 10 else ""}

---
*Generated by Master Project Organizer*
"""
        
        with open(output_path, 'w') as f:
            f.write(markdown_content)


async def main():
    """Main entry point"""
    try:
        organizer = MasterProjectOrganizer()
        await organizer.organize_project()
        return True
    except Exception as e:
        logger.error(f"Organization failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
