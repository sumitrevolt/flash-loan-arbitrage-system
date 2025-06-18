#!/usr/bin/env python3
"""
Flash Loan Project Organizer
============================

This script will organize the flash loan project by:
1. Identifying and removing duplicate files (backups, timestamped copies)
2. Organizing files into proper directory structure
3. Removing unnecessary files and logs
4. Creating a clean, maintainable project structure
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

class ProjectOrganizer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "cleanup_backup"
        self.deleted_files = []
        self.moved_files = []
        self.stats = {
            'files_deleted': 0,
            'files_moved': 0,
            'directories_created': 0,
            'space_saved': 0
        }
        
        # File patterns to remove
        self.remove_patterns = [
            '*.backup*',
            '*20250616*',
            '*.log',
            '__pycache__',
            '*.pyc',
            '*.tmp',
            '*.temp',
            'node_modules',
            '.env.example',
            '.env.template',
            'yarn.lock'
        ]
        
        # Directories to organize
        self.target_structure = {
            'core/': [
                'aave_flash_loan_expanded_system.py',
                'aave_flash_loan_profit_target.py',
                'aave_flash_loan_real_prices.py', 
                'aave_integration.py',
                'flash_loan_commander.py',
                'main.py'
            ],
            'mcp_servers/': ['*mcp*.py', 'check_mcp_status.py'],
            'ai_agents/': ['*agent*.py', '*coordinator*.py'],
            'docker/': ['docker*', 'Dockerfile*', '*.yml'],
            'scripts/': ['*.bat', '*.ps1', '*deploy*.py', '*launcher*.py'],
            'config/': ['*.json', '*.env*', 'aave_config.json'],
            'docs/': ['*.md', '*.txt'],
            'tests/': ['test_*.py', '*test*.py'],
            'logs/': ['*.log'],
            'utils/': ['*util*.py', '*helper*.py', '*monitor*.py']
        }

    def create_backup_dir(self):
        """Create backup directory for safety"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
            print(f"📁 Created backup directory: {self.backup_dir}")

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size
        except:
            return 0

    def should_remove_file(self, file_path: Path) -> bool:
        """Check if file matches removal patterns"""
        file_name = file_path.name.lower()
        for pattern in self.remove_patterns:
            pattern = pattern.replace('*', '')
            if pattern in file_name:
                return True
        return False

    def identify_duplicates(self) -> Dict[str, List[Path]]:
        """Identify duplicate files based on name patterns"""
        files_by_base = {}
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                # Get base name without backup suffixes
                name = file_path.name
                base_name = name
                
                # Remove common backup suffixes
                suffixes_to_remove = [
                    '.backup', '_backup', '.bak', '_bak',
                    '_20250616_124908', '_20250616_125148', '_20250616_133829',
                    '_20250616_133850', '_20250616_123711'
                ]
                
                for suffix in suffixes_to_remove:
                    if suffix in base_name:
                        base_name = base_name.replace(suffix, '')
                        break
                
                if base_name not in files_by_base:
                    files_by_base[base_name] = []
                files_by_base[base_name].append(file_path)
        
        # Filter to only return groups with multiple files
        duplicates = {k: v for k, v in files_by_base.items() if len(v) > 1}
        return duplicates

    def remove_duplicates(self):
        """Remove duplicate files, keeping the most recent or main version"""
        print("\n🗑️  REMOVING DUPLICATES...")
        print("=" * 50)
        
        duplicates = self.identify_duplicates()
        
        for base_name, file_list in duplicates.items():
            if len(file_list) <= 1:
                continue
                
            print(f"\n📋 Processing duplicates for: {base_name}")
            
            # Sort by modification time, keeping newest
            file_list.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep the first (newest/main) file, remove others
            keep_file = file_list[0]
            remove_files = file_list[1:]
            
            # Prefer non-backup files
            for file_path in file_list:
                if not any(suffix in file_path.name for suffix in ['.backup', '_backup', '20250616']):
                    keep_file = file_path
                    remove_files = [f for f in file_list if f != keep_file]
                    break
            
            print(f"   ✅ Keeping: {keep_file.relative_to(self.project_root)}")
            
            for remove_file in remove_files:
                try:
                    size = self.get_file_size(remove_file)
                    remove_file.unlink()
                    self.deleted_files.append(str(remove_file.relative_to(self.project_root)))
                    self.stats['files_deleted'] += 1
                    self.stats['space_saved'] += size
                    print(f"   🗑️  Removed: {remove_file.relative_to(self.project_root)}")
                except Exception as e:
                    print(f"   ❌ Error removing {remove_file}: {e}")

    def remove_unnecessary_files(self):
        """Remove log files, cache, and other unnecessary files"""
        print("\n🧹 REMOVING UNNECESSARY FILES...")
        print("=" * 50)
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and self.should_remove_file(file_path):
                try:
                    size = self.get_file_size(file_path)
                    file_path.unlink()
                    self.deleted_files.append(str(file_path.relative_to(self.project_root)))
                    self.stats['files_deleted'] += 1
                    self.stats['space_saved'] += size
                    print(f"🗑️  Removed: {file_path.relative_to(self.project_root)}")
                except Exception as e:
                    print(f"❌ Error removing {file_path}: {e}")

    def organize_files(self):
        """Organize remaining files into proper directory structure"""
        print("\n📂 ORGANIZING FILES...")
        print("=" * 50)
        
        # Create target directories
        for dir_name in self.target_structure.keys():
            target_dir = self.project_root / dir_name
            if not target_dir.exists():
                target_dir.mkdir(parents=True)
                self.stats['directories_created'] += 1
                print(f"📁 Created directory: {dir_name}")

        # Move files to appropriate directories
        for file_path in self.project_root.iterdir():
            if file_path.is_file():
                moved = False
                for target_dir, patterns in self.target_structure.items():
                    for pattern in patterns:
                        if self.matches_pattern(file_path.name, pattern):
                            target_path = self.project_root / target_dir / file_path.name
                            if not target_path.exists():
                                try:
                                    shutil.move(str(file_path), str(target_path))
                                    self.moved_files.append(f"{file_path.name} -> {target_dir}")
                                    self.stats['files_moved'] += 1
                                    print(f"📂 Moved: {file_path.name} -> {target_dir}")
                                    moved = True
                                    break
                                except Exception as e:
                                    print(f"❌ Error moving {file_path.name}: {e}")
                    if moved:
                        break

    def matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern"""
        if pattern.startswith('*') and pattern.endswith('*'):
            return pattern[1:-1] in filename.lower()
        elif pattern.startswith('*'):
            return filename.lower().endswith(pattern[1:].lower())
        elif pattern.endswith('*'):
            return filename.lower().startswith(pattern[:-1].lower())
        else:
            return filename.lower() == pattern.lower()

    def remove_empty_directories(self):
        """Remove empty directories"""
        print("\n🗂️  REMOVING EMPTY DIRECTORIES...")
        print("=" * 50)
        
        for dir_path in self.project_root.rglob('*'):
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):  # Directory is empty
                        dir_path.rmdir()
                        print(f"🗑️  Removed empty directory: {dir_path.relative_to(self.project_root)}")
                except:
                    pass  # Directory not empty or other error

    def create_report(self):
        """Create organization report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'deleted_files': self.deleted_files,
            'moved_files': self.moved_files,
            'space_saved_mb': round(self.stats['space_saved'] / 1024 / 1024, 2)
        }
        
        report_path = self.project_root / 'PROJECT_ORGANIZATION_REPORT.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 ORGANIZATION COMPLETE!")
        print("=" * 50)
        print(f"Files deleted: {self.stats['files_deleted']}")
        print(f"Files moved: {self.stats['files_moved']}")
        print(f"Directories created: {self.stats['directories_created']}")
        print(f"Space saved: {report['space_saved_mb']} MB")
        print(f"Report saved: PROJECT_ORGANIZATION_REPORT.json")

    def run(self):
        """Run the complete organization process"""
        print("🚀 FLASH LOAN PROJECT ORGANIZER")
        print("=" * 50)
        print(f"Project root: {self.project_root}")
        
        self.create_backup_dir()
        self.remove_duplicates()
        self.remove_unnecessary_files()
        self.organize_files()
        self.remove_empty_directories()
        self.create_report()
        
        print("\n✅ Project organization complete!")

if __name__ == "__main__":
    organizer = ProjectOrganizer(".")
    organizer.run()
