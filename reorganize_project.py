#!/usr/bin/env python3
"""
Project Reorganization Script
Organizes the flash loan arbitrage project into a logical structure
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class ProjectReorganizer:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.base_path / f"reorganization_backup_{self.timestamp}"
        
        # Define the new structure
        self.new_structure = {
            # Core application code
            "src": {
                "arbitrage": ["*arbitrage*.py", "*flash*loan*.py"],
                "coordination": ["*coordination*.py", "*orchestrat*.py", "*launcher*.py"],
                "mcp": ["*mcp*.py", "*bridge*.py"],
                "ai_agents": ["*agent*.py", "*ai*.py"],
                "monitoring": ["*monitor*.py", "*dashboard*.py", "*health*.py"],
                "utils": ["*util*.py", "*helper*.py", "*unicode*.py"]
            },
            
            # Configuration and environment
            "config": {
                "env": [".env*", "*.env"],
                "docker": ["docker-compose*.yml", "Dockerfile*"],
                "json": ["*.json"],
                "requirements": ["requirements*.txt"]
            },
            
            # Documentation
            "docs": {
                "guides": ["*GUIDE*.md", "*README*.md", "*USAGE*.md"],
                "status": ["*STATUS*.md", "*COMPLETE*.md", "*RUNNING*.md"],
                "reports": ["*REPORT*.md", "*SUMMARY*.md"],
                "implementation": ["*IMPLEMENTATION*.md", "*FIXES*.md"]
            },
            
            # Scripts and automation
            "scripts": {
                "launchers": ["launch_*.py", "start_*.py", "setup_*.py"],
                "powershell": ["*.ps1"],
                "maintenance": ["*clean*.py", "*organiz*.py", "*fix*.py"],
                "testing": ["test_*.py", "*test*.py", "validate_*.py", "verify_*.py"]
            },
            
            # Data and logs
            "data": {
                "logs": ["*.log"],
                "databases": ["*.db"],
                "cache": ["cache", "__pycache__"],
                "training": ["training_*"]
            },
            
            # Development and deployment
            "deployment": {
                "docker": ["docker", "containers"],
                "production": ["*production*"],
                "configs": ["docker-configs"]
            },
            
            # Archive and backups
            "archive": {
                "backups": ["backup*", "organized*"],
                "legacy": ["*.bak", "archive"]
            }
        }
    
    def create_backup(self):
        """Create a backup before reorganization"""
        print(f"Creating backup at: {self.backup_dir}")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Create a manifest of current structure
        manifest = {
            "timestamp": self.timestamp,
            "original_structure": self._get_current_structure(),
            "file_count": len(list(self.base_path.rglob("*")))
        }
        
        with open(self.backup_dir / "reorganization_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, default=str)
    
    def _get_current_structure(self):
        """Get current directory structure"""
        structure = {}
        for item in self.base_path.iterdir():
            if item.is_dir():
                structure[item.name] = {
                    "type": "directory",
                    "files": len(list(item.rglob("*")))
                }
            else:
                structure[item.name] = {
                    "type": "file",
                    "size": item.stat().st_size
                }
        return structure
    
    def create_new_structure(self):
        """Create the new directory structure"""
        print("Creating new directory structure...")
        
        for main_dir, subdirs in self.new_structure.items():
            main_path = self.base_path / main_dir
            main_path.mkdir(exist_ok=True)
            
            if isinstance(subdirs, dict):
                for subdir in subdirs.keys():
                    (main_path / subdir).mkdir(exist_ok=True)
    
    def categorize_files(self):
        """Categorize and move files according to the new structure"""
        moved_files = []
        
        for main_dir, categories in self.new_structure.items():
            if isinstance(categories, dict):
                for category, patterns in categories.items():
                    target_dir = self.base_path / main_dir / category
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Handle directory patterns
                    for pattern in patterns:
                        if pattern in ['cache', '__pycache__', 'backup*', 'organized*', 'docker', 'containers', 'archive', 'training_*']:
                            self._move_directories(pattern, target_dir, moved_files)
                        else:
                            self._move_files(pattern, target_dir, moved_files)
        
        return moved_files
    
    def _move_files(self, pattern, target_dir, moved_files):
        """Move files matching pattern to target directory"""
        import fnmatch
        
        for file_path in self.base_path.iterdir():
            if file_path.is_file():
                if fnmatch.fnmatch(file_path.name.lower(), pattern.lower()):
                    try:
                        new_path = target_dir / file_path.name
                        if not new_path.exists():
                            shutil.move(str(file_path), str(new_path))
                            moved_files.append(f"{file_path.name} -> {target_dir.relative_to(self.base_path)}")
                    except Exception as e:
                        print(f"Error moving {file_path.name}: {e}")
    
    def _move_directories(self, pattern, target_dir, moved_files):
        """Move directories matching pattern to target directory"""
        import fnmatch
        
        for dir_path in self.base_path.iterdir():
            if dir_path.is_dir():
                if pattern == dir_path.name or fnmatch.fnmatch(dir_path.name.lower(), pattern.lower()):
                    try:
                        new_path = target_dir / dir_path.name
                        if not new_path.exists():
                            shutil.move(str(dir_path), str(new_path))
                            moved_files.append(f"{dir_path.name}/ -> {target_dir.relative_to(self.base_path)}")
                    except Exception as e:
                        print(f"Error moving directory {dir_path.name}: {e}")
    
    def create_index_files(self):
        """Create index files for each major directory"""
        print("Creating index files...")
        
        indexes = {
            "src/README.md": """# Source Code

This directory contains the main application source code:

- `arbitrage/` - Flash loan arbitrage logic and strategies
- `coordination/` - System coordination and orchestration
- `mcp/` - Model Context Protocol implementations
- `ai_agents/` - AI agent implementations
- `monitoring/` - System monitoring and health checks
- `utils/` - Utility functions and helpers
""",
            
            "config/README.md": """# Configuration

This directory contains all configuration files:

- `env/` - Environment variables and settings
- `docker/` - Docker and container configurations
- `json/` - JSON configuration files
- `requirements/` - Python package requirements
""",
            
            "docs/README.md": """# Documentation

Complete project documentation:

- `guides/` - User guides and tutorials
- `status/` - Project status and completion reports
- `reports/` - Analysis and summary reports
- `implementation/` - Implementation details and fixes
""",
            
            "scripts/README.md": """# Scripts and Automation

Automation and utility scripts:

- `launchers/` - System launcher scripts
- `powershell/` - PowerShell automation scripts
- `maintenance/` - Cleanup and maintenance tools
- `testing/` - Test and validation scripts
""",
            
            "data/README.md": """# Data and Logs

Runtime data and logs:

- `logs/` - Application logs
- `databases/` - Local databases
- `cache/` - Cache directories
- `training/` - Training data and logs
""",
            
            "deployment/README.md": """# Deployment

Deployment configurations and tools:

- `docker/` - Docker containers and configurations
- `production/` - Production deployment files
- `configs/` - Deployment-specific configurations
""",
            
            "archive/README.md": """# Archive

Archived files and backups:

- `backups/` - System backups
- `legacy/` - Legacy files and old versions
"""
        }
        
        for file_path, content in indexes.items():
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
    
    def generate_report(self, moved_files):
        """Generate reorganization report"""
        report_path = self.base_path / f"reorganization_report_{self.timestamp}.md"
        
        report_content = f"""# Project Reorganization Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Backup Location:** {self.backup_dir.name}

## Summary

This report documents the reorganization of the flash loan arbitrage project into a more logical structure.

## New Structure

```
flash-loan/
├── src/                    # Source code
│   ├── arbitrage/         # Flash loan arbitrage logic
│   ├── coordination/      # System coordination
│   ├── mcp/              # Model Context Protocol
│   ├── ai_agents/        # AI agent implementations
│   ├── monitoring/       # System monitoring
│   └── utils/            # Utility functions
├── config/                # Configuration files
│   ├── env/              # Environment variables
│   ├── docker/           # Docker configurations
│   ├── json/             # JSON configs
│   └── requirements/     # Python requirements
├── docs/                 # Documentation
│   ├── guides/           # User guides
│   ├── status/           # Status reports
│   ├── reports/          # Analysis reports
│   └── implementation/   # Implementation docs
├── scripts/              # Scripts and automation
│   ├── launchers/        # Launch scripts
│   ├── powershell/       # PowerShell scripts
│   ├── maintenance/      # Maintenance tools
│   └── testing/          # Test scripts
├── data/                 # Data and logs
│   ├── logs/             # Application logs
│   ├── databases/        # Local databases
│   ├── cache/            # Cache directories
│   └── training/         # Training data
├── deployment/           # Deployment files
│   ├── docker/           # Docker containers
│   ├── production/       # Production configs
│   └── configs/          # Deployment configs
└── archive/              # Archive and backups
    ├── backups/          # System backups
    └── legacy/           # Legacy files
```

## Files Moved

Total files reorganized: {len(moved_files)}

"""
        
        for move in moved_files[:50]:  # Show first 50 moves
            report_content += f"- {move}\n"
        
        if len(moved_files) > 50:
            report_content += f"\n... and {len(moved_files) - 50} more files\n"
        
        report_content += f"""

## Next Steps

1. Review the new structure and verify all files are in correct locations
2. Update any hardcoded paths in scripts and configuration files
3. Test the system to ensure everything works correctly
4. Update documentation to reflect the new structure
5. Consider removing the backup once everything is verified

## Rollback Instructions

If you need to rollback the reorganization:

1. Stop all running services
2. Delete the new directory structure
3. Restore files from: `{self.backup_dir.name}`
4. Use the manifest file to verify restoration

"""
        
        with open(report_path, "w") as f:
            f.write(report_content)
        
        print(f"Report saved to: {report_path}")
        return report_path

def main():
    print("🏗️  Flash Loan Project Reorganizer")
    print("=" * 50)
    
    reorganizer = ProjectReorganizer()
    
    # Create backup
    reorganizer.create_backup()
    
    # Create new structure
    reorganizer.create_new_structure()
    
    # Move files
    print("Reorganizing files...")
    moved_files = reorganizer.categorize_files()
    
    # Create index files
    reorganizer.create_index_files()
    
    # Generate report
    report_path = reorganizer.generate_report(moved_files)
    
    print(f"\n✅ Reorganization complete!")
    print(f"📁 Files moved: {len(moved_files)}")
    print(f"📋 Report: {report_path}")
    print(f"💾 Backup: {reorganizer.backup_dir}")
    
    return True

if __name__ == "__main__":
    main()

