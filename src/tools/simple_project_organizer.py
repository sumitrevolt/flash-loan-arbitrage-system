#!/usr/bin/env python3
"""
Simple Project Organizer and Cleaner
====================================

This script organizes the project by:
1. Identifying and removing duplicate files
2. Organizing files into proper directory structure
3. Fixing common Python issues
4. Creating a clean project layout

Author: GitHub Copilot Assistant
Date: June 2025
"""

import os
import sys
import shutil
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Tuple, Callable, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simple_project_organizer.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class SimpleProjectOrganizer:
    """Simple project organizer without complex dependencies"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.report = {
            'start_time': datetime.now().isoformat(),
            'duplicates_removed': 0,
            'files_organized': 0,
            'directories_created': 0,
            'backup_files_cleaned': 0,
            'python_files_fixed': 0
        }
        
        # Target directory structure
        self.target_structure = {
            'src': ['langchain_coordinators', 'mcp_integrators', 'tools', 'utilities'],
            'mcp_servers': ['task_management', 'github_integration', 'playwright_automation', 'context_retrieval'],
            'docker': ['compose_files', 'configurations'],
            'scripts': ['deployment', 'automation', 'utilities'],
            'config': [],
            'docs': [],
            'logs': [],
            'backups': []
        }
    
    def organize_project(self) -> Dict[str, Any]:
        """Main method to organize the project"""
        logger.info("🚀 Starting simple project organization...")
        
        try:
            # Step 1: Create directory structure
            self.create_directory_structure()
            
            # Step 2: Remove duplicate files
            self.remove_duplicate_files()
            
            # Step 3: Clean backup and temporary files
            self.clean_backup_files()
            
            # Step 4: Organize files
            self.organize_files()
            
            # Step 5: Fix Python files
            self.fix_python_files()
            
            # Step 6: Generate report
            self.generate_report()
            
            logger.info("✅ Project organization completed successfully!")
            return self.report
            
        except Exception as e:
            logger.error(f"❌ Error during organization: {e}")
            return {'error': str(e)}
    
    def create_directory_structure(self) -> None:
        """Create the target directory structure"""
        logger.info("📁 Creating directory structure...")
        
        for main_dir, subdirs in self.target_structure.items():
            main_path = self.project_root / main_dir
            main_path.mkdir(exist_ok=True)
            self.report['directories_created'] += 1
            logger.info(f"📂 Created: {main_dir}")
            
            for subdir in subdirs:
                sub_path = main_path / subdir
                sub_path.mkdir(exist_ok=True)
                self.report['directories_created'] += 1
                logger.info(f"📂 Created: {main_dir}/{subdir}")
    
    def remove_duplicate_files(self) -> None:
        """Remove duplicate files based on content hash"""
        logger.info("🔍 Detecting and removing duplicate files...")
        
        file_hashes: Dict[str, List[Path]] = defaultdict(list)
        
        # Calculate hashes for all files
        for file_path in self.project_root.rglob('*'):
            if (file_path.is_file() and 
                not self._should_skip_file(file_path) and
                not self._is_in_target_dirs(file_path)):
                
                try:
                    content_hash = self._calculate_file_hash(file_path)
                    file_hashes[content_hash].append(file_path)
                except Exception as e:
                    logger.warning(f"Could not hash {file_path}: {e}")
        
        # Remove duplicates (keep the first file in each group)
        for content_hash, file_list in file_hashes.items():
            if len(file_list) > 1:
                logger.info(f"🔍 Found {len(file_list)} duplicate files:")
                for file_path in file_list:
                    logger.info(f"   - {file_path.relative_to(self.project_root)}")
                
                # Keep the first file, remove others
                for duplicate_file in file_list[1:]:
                    try:
                        duplicate_file.unlink()
                        self.report['duplicates_removed'] += 1
                        logger.info(f"🗑️  Removed: {duplicate_file.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove {duplicate_file}: {e}")
    
    def clean_backup_files(self) -> None:
        """Clean up backup and temporary files"""
        logger.info("🧹 Cleaning backup and temporary files...")
        
        backup_patterns = [
            '*.backup',
            '*.backup_*',
            '*.bak',
            '*.tmp',
            '*~',
            '*.py.backup*',
            '*.old'
        ]
        
        for pattern in backup_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    try:
                        # Move to backups directory instead of deleting
                        backup_dir = self.project_root / 'backups'
                        backup_dir.mkdir(exist_ok=True)
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                        backup_path = backup_dir / new_name
                        
                        shutil.move(str(file_path), str(backup_path))
                        self.report['backup_files_cleaned'] += 1
                        logger.info(f"📦 Moved to backup: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Could not move backup file {file_path}: {e}")
    
    def organize_files(self) -> None:
        """Organize files into appropriate directories"""
        logger.info("📁 Organizing files into proper directories...")
        
        # Get all files that are not in target directories
        files_to_organize = []
        for file_path in self.project_root.rglob('*'):
            if (file_path.is_file() and 
                not self._should_skip_file(file_path) and
                not self._is_in_target_dirs(file_path)):
                files_to_organize.append(file_path)
        
        logger.info(f"📄 Found {len(files_to_organize)} files to organize")
        
        for file_path in files_to_organize:
            target_dir = self._determine_target_directory(file_path)
            if target_dir:
                try:
                    target_path = target_dir / file_path.name
                    
                    # Avoid overwriting existing files
                    if target_path.exists():
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        target_path = target_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                    
                    shutil.move(str(file_path), str(target_path))
                    self.report['files_organized'] += 1
                    logger.info(f"📦 Moved {file_path.name} to {target_dir.relative_to(self.project_root)}")
                    
                except Exception as e:
                    logger.warning(f"Could not move {file_path}: {e}")
    
    def fix_python_files(self) -> None:
        """Fix common issues in Python files"""
        logger.info("🔧 Fixing Python files...")
        
        for py_file in self.project_root.rglob('*.py'):
            if self._should_process_python_file(py_file):
                try:
                    fixed = self._fix_python_file(py_file)
                    if fixed:
                        self.report['python_files_fixed'] += 1
                        logger.info(f"🔧 Fixed: {py_file.relative_to(self.project_root)}")
                except Exception as e:
                    logger.warning(f"Could not fix {py_file}: {e}")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if file should be skipped"""
        skip_extensions = {'.log', '.tmp', '.cache', '.pyc', '.pyo', '.pyd'}
        skip_names = {'__pycache__', '.git', '.vscode', 'node_modules'}
        
        return (
            file_path.suffix.lower() in skip_extensions or
            any(part in skip_names for part in file_path.parts) or
            file_path.name.startswith('.')
        )
    
    def _is_in_target_dirs(self, file_path: Path) -> bool:
        """Check if file is already in target directory structure"""
        try:
            relative_path = file_path.relative_to(self.project_root)
            if len(relative_path.parts) > 0:
                first_part = relative_path.parts[0]
                return first_part in self.target_structure
        except ValueError:
            pass
        return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        except Exception:
            # For text files that might have encoding issues
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    hasher.update(f.read().encode('utf-8'))
            except Exception:
                # Use file size and name as fallback
                hasher.update(f"{file_path.name}_{file_path.stat().st_size}".encode('utf-8'))
        return hasher.hexdigest()
    
    def _determine_target_directory(self, file_path: Path) -> Optional[Path]:
        """Determine appropriate target directory for a file"""
        file_name = file_path.name.lower()
        file_suffix = file_path.suffix.lower()
        
        # LangChain coordinators
        if 'langchain' in file_name and ('coordinat' in file_name or 'master' in file_name):
            return self.project_root / 'src' / 'langchain_coordinators'
        
        # MCP related files
        if 'mcp' in file_name and file_suffix == '.py':
            return self.project_root / 'src' / 'mcp_integrators'
        
        # Docker files
        if file_name.startswith('docker-compose') or file_suffix in ['.dockerfile']:
            return self.project_root / 'docker' / 'compose_files'
        
        # Scripts
        if file_suffix == '.py' and any(keyword in file_name for keyword in ['auto', 'deploy', 'setup', 'script', 'fix']):
            return self.project_root / 'scripts' / 'automation'
        
        # Documentation
        if file_suffix in ['.md', '.txt', '.rst']:
            return self.project_root / 'docs'
        
        # Configuration
        if file_suffix in ['.yaml', '.yml', '.json', '.toml', '.env']:
            return self.project_root / 'config'
        
        # Utilities
        if file_suffix == '.py' and any(keyword in file_name for keyword in ['util', 'helper', 'tool']):
            return self.project_root / 'src' / 'utilities'
        
        # Default Python files to src/tools
        if file_suffix == '.py':
            return self.project_root / 'src' / 'tools'
        
        return None
    
    def _should_process_python_file(self, file_path: Path) -> bool:
        """Determine if Python file should be processed"""
        skip_dirs = {'__pycache__', '.git', 'venv', 'env', 'node_modules'}
        return not any(part in skip_dirs for part in file_path.parts)
    
    def _fix_python_file(self, file_path: Path) -> bool:
        """Fix common issues in a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix common import issues
            import_fixes = [
                ('from langchain_openai import ChatOpenAI', 'from langchain_openai import ChatOpenAI'),
                ('tool.run(', 'tool.run('),
                ('analysis_tool.run(', 'analysis_tool.run('),
                ('fixer_tool.run(', 'fixer_tool.run('),
            ]
            
            for old_import, new_import in import_fixes:
                if old_import in content:
                    content = content.replace(old_import, new_import)
            
            # Write back if changes were made
            if content != original_content:
                # Create backup first
                backup_path = file_path.with_suffix('.py.backup')
                shutil.copy2(file_path, backup_path)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            logger.warning(f"Could not fix Python file {file_path}: {e}")
        
        return False
    
    def generate_report(self) -> None:
        """Generate organization report"""
        self.report['end_time'] = datetime.now().isoformat()
        duration = datetime.fromisoformat(self.report['end_time']) - datetime.fromisoformat(self.report['start_time'])
        self.report['duration'] = str(duration)
        
        # Create report file
        report_file = self.project_root / 'PROJECT_ORGANIZATION_REPORT.md'
        
        report_content = f"""# Project Organization Report

## Summary
- **Start Time**: {self.report['start_time']}
- **End Time**: {self.report['end_time']}  
- **Duration**: {self.report['duration']}

## Results
- **Directories Created**: {self.report['directories_created']}
- **Duplicate Files Removed**: {self.report['duplicates_removed']}
- **Files Organized**: {self.report['files_organized']}
- **Backup Files Cleaned**: {self.report['backup_files_cleaned']}
- **Python Files Fixed**: {self.report['python_files_fixed']}

## New Project Structure
```
{self._generate_structure_tree()}
```

## MCP Servers Identified
{self._list_mcp_servers()}

## Next Steps
1. Verify all file locations are correct
2. Test MCP server integrations
3. Update import paths if needed
4. Run tests to ensure functionality

Generated by: Simple Project Organizer
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Also save as JSON
        json_report_file = self.project_root / 'organization_report.json'
        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2)
        
        logger.info(f"📋 Generated reports: {report_file}")
        logger.info(f"📋 JSON report: {json_report_file}")
    
    def _generate_structure_tree(self) -> str:
        """Generate a tree view of the project structure"""
        def build_tree(directory: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
            if current_depth >= max_depth or not directory.exists():
                return ""
            
            items = []
            try:
                children = sorted([item for item in directory.iterdir() 
                                 if not item.name.startswith('.')], 
                                key=lambda x: Any: Any: (x.is_file(), x.name.lower()))
                
                for i, item in enumerate(children[:15]):  # Limit to 15 items per directory
                    is_last = i == len(children) - 1
                    current_prefix = "└── " if is_last else "├── "
                    items.append(f"{prefix}{current_prefix}{item.name}")
                    
                    if item.is_dir() and current_depth < max_depth - 1:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        items.append(build_tree(item, next_prefix, max_depth, current_depth + 1))
                
                if len(children) > 15:
                    items.append(f"{prefix}└── ... ({len(children) - 15} more items)")
                    
            except PermissionError:
                items.append(f"{prefix}└── [Permission Denied]")
            
            return "\n".join(filter(None, items))
        
        return build_tree(self.project_root)
    
    def _list_mcp_servers(self) -> str:
        """List identified MCP servers"""
        mcp_servers = []
        mcp_dir = self.project_root / 'mcp_servers'
        
        if mcp_dir.exists():
            for item in mcp_dir.rglob('*'):
                if item.is_dir() and any(keyword in item.name.lower() for keyword in ['mcp', 'server', 'task', 'github', 'playwright']):
                    mcp_servers.append(f"- {item.relative_to(self.project_root)}")
        
        return "\n".join(mcp_servers) if mcp_servers else "- No MCP servers found"

def main():
    """Main entry point"""
    project_root = Path.cwd()
    
    logger.info("🎯 Starting Simple Project Organization")
    logger.info(f"📁 Project root: {project_root}")
    
    organizer = SimpleProjectOrganizer(str(project_root))
    
    try:
        result: str = organizer.organize_project()
        logger.info("✅ Organization Results:")
        for key, value in result.items():
            if key != 'error':
                logger.info(f"   {key}: {value}")
    except Exception as e:
        logger.error(f"❌ Organization failed: {e}")

if __name__ == "__main__":
    main()
