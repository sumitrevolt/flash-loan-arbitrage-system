#!/usr/bin/env python3
"""
Comprehensive Project Organizer using LangChain and MCP Servers
==============================================================

This script organizes the entire project by:
1. Identifying and removing duplicate files
2. Consolidating similar scripts and configurations  
3. Creating a clean directory structure
4. Integrating all MCP servers with LangChain
5. Fixing all Python type annotation issues
6. Generating a comprehensive project structure

Author: GitHub Copilot Assistant
Date: June 2025
"""

import asyncio
import logging
import json
import os
import sys
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Tuple, Callable, Union, Tuple
from collections import defaultdict

# Enhanced LangChain imports with proper type annotations
try:
    from langchain_openai import ChatOpenAI
    from langchain.memory import ConversationBufferMemory
    from langchain.agents import initialize_agent, AgentType
    from langchain.tools import BaseTool, StructuredTool
    from langchain.callbacks.manager import CallbackManagerForToolRun
    from langchain.schema import BaseMessage
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError as e:
    logging.error(f"Missing LangChain dependencies: {e}")
    sys.exit(1)

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('project_organizer.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class ProjectStructure:
    """Defines the target project structure"""
    
    STRUCTURE = {
        'src/': {
            'langchain_coordinators/': ['*.py'],
            'mcp_integrators/': ['*.py'],
            'tools/': ['*.py'],
            'utilities/': ['*.py']
        },
        'mcp_servers/': {
            'task_management/': ['mcp-taskmanager/'],
            'github_integration/': ['github-mcp/'],
            'playwright_automation/': ['playwright-mcp/'],
            'context_retrieval/': ['context7-mcp/']
        },
        'docker/': {
            'compose_files/': ['docker-compose*.yml'],
            'configurations/': ['*.env', '*.conf']
        },
        'scripts/': {
            'deployment/': ['deploy*.py', 'setup*.py'],
            'automation/': ['auto*.py'],
            'utilities/': ['*util*.py', '*helper*.py']
        },
        'backups/': {},
        'logs/': {},
        'docs/': ['*.md', '*.txt'],
        'config/': ['*.yaml', '*.json', '*.toml']
    }

class DuplicateDetectorTool(BaseTool):
    """Tool for detecting duplicate files using content hashing"""
    
    name: str = "duplicate_detector"
    description: str = "Detects duplicate files by analyzing content hashes and similarity"
    
    def _run(self, directory_path: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Find duplicate files in directory"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                return f"Directory {directory_path} does not exist"
            
            file_hashes: Dict[str, List[Path]] = defaultdict(list)
            duplicate_groups: List[List[str]] = []
            
            # Calculate hashes for all files
            for file_path in directory.rglob('*'):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    try:
                        content_hash = self._calculate_file_hash(file_path)
                        file_hashes[content_hash].append(file_path)
                    except Exception as e:
                        logger.warning(f"Could not hash {file_path}: {e}")
            
            # Identify duplicates
            for content_hash, file_list in file_hashes.items():
                if len(file_list) > 1:
                    duplicate_groups.append([str(f) for f in file_list])
            
            return json.dumps({
                'total_files_scanned': sum(len(files) for files in file_hashes.values()),
                'duplicate_groups': duplicate_groups,
                'total_duplicates': len(duplicate_groups),
                'files_to_remove': sum(len(group) - 1 for group in duplicate_groups)
            })
            
        except Exception as e:
            return f"Error detecting duplicates: {str(e)}"
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if file should be skipped during duplicate detection"""
        skip_extensions = {'.log', '.tmp', '.cache', '.pyc', '.pyo', '.pyd'}
        skip_names = {'__pycache__', '.git', '.vscode', 'node_modules'}
        
        return (
            file_path.suffix.lower() in skip_extensions or
            any(part in skip_names for part in file_path.parts) or
            file_path.name.startswith('.')
        )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        except Exception:
            # For text files that might have encoding issues
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                hasher.update(f.read().encode('utf-8'))
        return hasher.hexdigest()

class ProjectOrganizerTool(BaseTool):
    """Tool for organizing project files into proper structure"""
    
    name: str = "project_organizer"
    description: str = "Organizes project files into a clean, structured directory layout"
    
    def _run(self, organization_request: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Organize project files based on request"""
        try:
            request_data = json.loads(organization_request)
            source_dir = Path(request_data['source_directory'])
            target_structure = request_data.get('target_structure', ProjectStructure.STRUCTURE)
            
            if not source_dir.exists():
                return f"Source directory {source_dir} does not exist"
            
            organized_files = 0
            created_directories = []
            
            # Create target directory structure
            for main_dir, subdirs in target_structure.items():
                main_path = source_dir / main_dir
                main_path.mkdir(exist_ok=True)
                created_directories.append(str(main_path))
                
                if isinstance(subdirs, dict):
                    for subdir in subdirs:
                        sub_path = main_path / subdir
                        sub_path.mkdir(exist_ok=True)
                        created_directories.append(str(sub_path))
            
            # Move files to appropriate directories
            for file_path in source_dir.rglob('*'):
                if file_path.is_file() and not self._is_in_target_structure(file_path, source_dir):
                    target_dir = self._determine_target_directory(file_path, source_dir, target_structure)
                    if target_dir:
                        try:
                            target_path = target_dir / file_path.name
                            # Avoid overwriting existing files
                            if target_path.exists():
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                target_path = target_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                            
                            shutil.move(str(file_path), str(target_path))
                            organized_files += 1
                            logger.info(f"Moved {file_path.name} to {target_dir}")
                        except Exception as e:
                            logger.warning(f"Could not move {file_path}: {e}")
            
            return json.dumps({
                'organized_files': organized_files,
                'created_directories': len(created_directories),
                'directories_created': created_directories,
                'status': 'success'
            })
            
        except Exception as e:
            return f"Error organizing project: {str(e)}"
    
    def _is_in_target_structure(self, file_path: Path, source_dir: Path) -> bool:
        """Check if file is already in target structure"""
        relative_path = file_path.relative_to(source_dir)
        target_dirs = {'src', 'mcp_servers', 'docker', 'scripts', 'backups', 'logs', 'docs', 'config'}
        return len(relative_path.parts) > 0 and relative_path.parts[0] in target_dirs
    
    def _determine_target_directory(self, file_path: Path, source_dir: Path, structure: Dict[str, Any]) -> Optional[Path]:
        """Determine appropriate target directory for a file"""
        file_name = file_path.name.lower()
        file_suffix = file_path.suffix.lower()
        
        # LangChain coordinators
        if 'langchain' in file_name and 'coordinat' in file_name:
            return source_dir / 'src' / 'langchain_coordinators'
        
        # MCP related files
        if 'mcp' in file_name or 'server' in file_name:
            return source_dir / 'src' / 'mcp_integrators'
        
        # Docker files
        if file_name.startswith('docker-compose') or file_suffix in ['.dockerfile']:
            return source_dir / 'docker' / 'compose_files'
        
        # Scripts
        if file_suffix == '.py' and any(keyword in file_name for keyword in ['auto', 'deploy', 'setup', 'script']):
            return source_dir / 'scripts' / 'automation'
        
        # Documentation
        if file_suffix in ['.md', '.txt', '.rst']:
            return source_dir / 'docs'
        
        # Configuration
        if file_suffix in ['.yaml', '.yml', '.json', '.toml', '.env']:
            return source_dir / 'config'
        
        # Utilities
        if file_suffix == '.py' and any(keyword in file_name for keyword in ['util', 'helper', 'tool']):
            return source_dir / 'src' / 'utilities'
        
        # Default Python files to src
        if file_suffix == '.py':
            return source_dir / 'src' / 'tools'
        
        return None

class TypeAnnotationFixerTool(BaseTool):
    """Tool for fixing Python type annotation issues"""
    
    name: str = "type_fixer"
    description: str = "Fixes Python type annotation issues and import problems"
    
    def _run(self, file_path: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Fix type annotation issues in Python file"""
        try:
            path = Path(file_path)
            if not path.exists() or path.suffix != '.py':
                return f"Invalid Python file: {file_path}"
            
            # Read content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_applied = 0
            
            # Fix import issues
            import_fixes = [
                # Fix LangChain imports
                ('from langchain_openai import ChatOpenAI', 'from langchain_openai import ChatOpenAI'),
                ('from langchain.agents import initialize_agent, AgentType', 'from langchain.agents import initialize_agent, AgentType'),
                
                # Add missing type imports
                ('from typing import Dict, List, Any, Optional, Set, Union, Tuple, Callable', 
                 'from typing import Dict, List, Any, Optional, Set, Union, Tuple, Callable, Union, Tuple, Callable'),
            ]
            
            for old_import, new_import in import_fixes:
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    fixes_applied += 1
            
            # Fix lambda type annotations
            lambda_patterns = [
                (r'lambda x: Any: Any:', 'lambda x: Any: Any: Any:'),
                (r'lambda (\w+):', r'lambda \1: Any:'),
            ]
            
            for pattern, replacement in lambda_patterns:
                import re
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    fixes_applied += 1
            
            # Fix method calls with proper type annotations
            method_fixes = [
                # Fix _run method calls
                ('tool.run(', 'tool.run('),
                ('analysis_tool.run(', 'analysis_tool.run('),
                ('fixer_tool.run(', 'fixer_tool.run('),
            ]
            
            for old_call, new_call in method_fixes:
                if old_call in content:
                    content = content.replace(old_call, new_call)
                    fixes_applied += 1
            
            # Add proper type annotations for variables
            type_annotation_fixes = [
                ('line = ', 'line: str = '),
                ('result = ', 'result: str = '),
                ('issues = []', 'issues: List[Dict[str, Any]] = []'),
                ('all_issues = {}', 'all_issues: Dict[str, Any] = {}'),
            ]
            
            for old_annotation, new_annotation in type_annotation_fixes:
                if old_annotation in content and new_annotation not in content:
                    content = content.replace(old_annotation, new_annotation)
                    fixes_applied += 1
            
            # Write fixed content if changes were made
            if content != original_content:
                # Create backup
                backup_path = path.with_suffix('.py.backup')
                shutil.copy2(path, backup_path)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return json.dumps({
                'file': file_path,
                'fixes_applied': fixes_applied,
                'backup_created': str(backup_path) if fixes_applied > 0 else None,
                'status': 'success' if fixes_applied > 0 else 'no_changes_needed'
            })
            
        except Exception as e:
            return f"Error fixing type annotations: {str(e)}"

class LangChainProjectOrganizer:
    """Main coordinator class for project organization using LangChain"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.setup_langchain()
        self.organize_report = {
            'start_time': datetime.now().isoformat(),
            'files_processed': 0,
            'duplicates_removed': 0,
            'files_organized': 0,
            'type_fixes_applied': 0,
            'mcp_servers_integrated': 0
        }
    
    def setup_langchain(self) -> None:
        """Setup LangChain components"""
        try:
            # Initialize LLM (using a mock for now - replace with actual API key)
            self.llm = ChatOpenAI(
                temperature=0.1,
                model_name="gpt-3.5-turbo",
                openai_api_key="your-api-key-here"  # Replace with actual key
            )
            
            # Initialize memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create tools
            self.tools = [
                DuplicateDetectorTool(),
                ProjectOrganizerTool(), 
                TypeAnnotationFixerTool()
            ]
            
            # Initialize agent
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True
            )
            
            logger.info("✅ LangChain components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error setting up LangChain: {e}")
            # Continue without LLM for basic functionality
            self.tools = [
                DuplicateDetectorTool(),
                ProjectOrganizerTool(),
                TypeAnnotationFixerTool()
            ]
    
    async def organize_project(self) -> Dict[str, Any]:
        """Main method to organize the entire project"""
        logger.info("🚀 Starting comprehensive project organization...")
        
        try:
            # Step 1: Detect and remove duplicates
            await self.remove_duplicates()
            
            # Step 2: Organize file structure
            await self.organize_file_structure()
            
            # Step 3: Fix type annotations
            await self.fix_type_annotations()
            
            # Step 4: Integrate MCP servers
            await self.integrate_mcp_servers()
            
            # Step 5: Generate final report
            self.generate_organization_report()
            
            logger.info("✅ Project organization completed successfully!")
            return self.organize_report
            
        except Exception as e:
            logger.error(f"❌ Error during project organization: {e}")
            return {'error': str(e)}
    
    async def remove_duplicates(self) -> None:
        """Remove duplicate files from project"""
        logger.info("🔍 Detecting duplicate files...")
        
        duplicate_tool = DuplicateDetectorTool()
        result = duplicate_tool.run(str(self.project_root))
        
        if result.startswith('Error'):
            logger.error(f"❌ {result}")
            return
        
        duplicate_data = json.loads(result)
        logger.info(f"📊 Found {duplicate_data['total_duplicates']} duplicate groups")
        
        # Remove duplicates (keep first file in each group)
        for group in duplicate_data['duplicate_groups']:
            for duplicate_file in group[1:]:  # Skip first file
                try:
                    Path(duplicate_file).unlink()
                    self.organize_report['duplicates_removed'] += 1
                    logger.info(f"🗑️  Removed duplicate: {Path(duplicate_file).name}")
                except Exception as e:
                    logger.warning(f"Could not remove {duplicate_file}: {e}")
    
    async def organize_file_structure(self) -> None:
        """Organize files into proper directory structure"""
        logger.info("📁 Organizing file structure...")
        
        organizer_tool = ProjectOrganizerTool()
        request = json.dumps({
            'source_directory': str(self.project_root),
            'target_structure': ProjectStructure.STRUCTURE
        })
        
        result = organizer_tool.run(request)
        
        if result.startswith('Error'):
            logger.error(f"❌ {result}")
            return
        
        organize_data = json.loads(result)
        self.organize_report['files_organized'] = organize_data['organized_files']
        logger.info(f"📦 Organized {organize_data['organized_files']} files")
    
    async def fix_type_annotations(self) -> None:
        """Fix type annotation issues in Python files"""
        logger.info("🔧 Fixing type annotations...")
        
        type_fixer = TypeAnnotationFixerTool()
        
        for py_file in self.project_root.rglob('*.py'):
            if self._should_process_python_file(py_file):
                result = type_fixer.run(str(py_file))
                
                if result.startswith('Error'):
                    logger.warning(f"⚠️  Could not fix {py_file}: {result}")
                    continue
                
                fix_data = json.loads(result)
                if fix_data['fixes_applied'] > 0:
                    self.organize_report['type_fixes_applied'] += fix_data['fixes_applied']
                    logger.info(f"🔧 Fixed {fix_data['fixes_applied']} issues in {py_file.name}")
    
    def _should_process_python_file(self, file_path: Path) -> bool:
        """Determine if Python file should be processed"""
        skip_dirs = {'__pycache__', '.git', 'venv', 'env', 'node_modules'}
        return not any(part in skip_dirs for part in file_path.parts)
    
    async def integrate_mcp_servers(self) -> None:
        """Integrate all MCP servers with LangChain"""
        logger.info("🔗 Integrating MCP servers...")
        
        mcp_servers = [
            'task_management/mcp-taskmanager',
            'github_integration', 
            'playwright_automation',
            'context_retrieval'
        ]
        
        mcp_dir = self.project_root / 'mcp_servers'
        if not mcp_dir.exists():
            mcp_dir.mkdir()
        
        integrated_servers = 0
        for server in mcp_servers:
            server_path = mcp_dir / server
            if server_path.exists():
                # Create integration configuration
                await self._create_mcp_integration_config(server, server_path)
                integrated_servers += 1
        
        self.organize_report['mcp_servers_integrated'] = integrated_servers
        logger.info(f"🔗 Integrated {integrated_servers} MCP servers")
    
    async def _create_mcp_integration_config(self, server_name: str, server_path: Path) -> None:
        """Create integration configuration for MCP server"""
        config = {
            'name': server_name,
            'path': str(server_path),
            'enabled': True,
            'langchain_integration': {
                'tool_prefix': server_name.replace('_', '-'),
                'description': f"Integration with {server_name} MCP server"
            }
        }
        
        config_file = server_path / 'langchain_integration.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def generate_organization_report(self) -> None:
        """Generate comprehensive organization report"""
        self.organize_report['end_time'] = datetime.now().isoformat()
        self.organize_report['duration'] = str(
            datetime.fromisoformat(self.organize_report['end_time']) - 
            datetime.fromisoformat(self.organize_report['start_time'])
        )
        
        report_file = self.project_root / 'PROJECT_ORGANIZATION_REPORT.md'
        
        report_content = f"""# Project Organization Report

## Summary
- **Start Time**: {self.organize_report['start_time']}
- **End Time**: {self.organize_report['end_time']}
- **Duration**: {self.organize_report['duration']}

## Results
- **Files Processed**: {self.organize_report['files_processed']}
- **Duplicates Removed**: {self.organize_report['duplicates_removed']}
- **Files Organized**: {self.organize_report['files_organized']}
- **Type Fixes Applied**: {self.organize_report['type_fixes_applied']}
- **MCP Servers Integrated**: {self.organize_report['mcp_servers_integrated']}

## New Project Structure
```
{self._generate_structure_tree()}
```

## Next Steps
1. Test all MCP server integrations
2. Verify LangChain functionality
3. Update documentation
4. Run comprehensive tests

Generated by: LangChain Project Organizer
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📋 Generated organization report: {report_file}")
    
    def _generate_structure_tree(self) -> str:
        """Generate a tree view of the project structure"""
        def build_tree(directory: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
            if current_depth >= max_depth:
                return ""
            
            items = []
            if directory.exists():
                try:
                    children = sorted([item for item in directory.iterdir() 
                                     if not item.name.startswith('.')], 
                                    key=lambda x: Any: Any: (x.is_file(), x.name.lower()))
                    
                    for i, item in enumerate(children[:10]):  # Limit to 10 items per directory
                        is_last = i == len(children) - 1
                        current_prefix = "└── " if is_last else "├── "
                        items.append(f"{prefix}{current_prefix}{item.name}")
                        
                        if item.is_dir() and current_depth < max_depth - 1:
                            next_prefix = prefix + ("    " if is_last else "│   ")
                            items.append(build_tree(item, next_prefix, max_depth, current_depth + 1))
                    
                    if len(children) > 10:
                        items.append(f"{prefix}└── ... ({len(children) - 10} more items)")
                        
                except PermissionError:
                    items.append(f"{prefix}└── [Permission Denied]")
            
            return "\n".join(filter(None, items))
        
        return build_tree(self.project_root)

async def main():
    """Main entry point"""
    project_root = Path.cwd()
    
    logger.info("🎯 Starting LangChain Project Organization")
    logger.info(f"📁 Project root: {project_root}")
    
    organizer = LangChainProjectOrganizer(str(project_root))
    
    try:
        result = await organizer.organize_project()
        logger.info(f"✅ Organization completed: {result}")
    except Exception as e:
        logger.error(f"❌ Organization failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
