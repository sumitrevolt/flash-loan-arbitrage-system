#!/usr/bin/env python3
"""
Comprehensive Duplicate Cleaner for Flash Loan Project
=====================================================

This script identifies and removes various types of duplicates:
1. Multiple backup folders with different timestamps
2. Files with timestamp patterns (_20250617, _20250619, etc.)
3. Backup files with .backup extension  
4. Exact duplicate files based on content hash
5. Similar files with minor differences

Author: GitHub Copilot Assistant
Date: June 19, 2025
"""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
import re
import difflib

class ComprehensiveDuplicateCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_root = self.project_root / "backups" / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "categories": {
                "backup_folders": {"found": 0, "removed": 0, "files": []},
                "timestamp_files": {"found": 0, "removed": 0, "files": []},
                "backup_extensions": {"found": 0, "removed": 0, "files": []},
                "exact_duplicates": {"found": 0, "removed": 0, "groups": []},
                "similar_files": {"found": 0, "removed": 0, "groups": []},
                "empty_dirs": {"found": 0, "removed": 0, "dirs": []}
            },
            "total_space_saved": 0,
            "errors": []
        }
        
        # Patterns to identify duplicates
        self.timestamp_patterns = [
            r'_\d{8}_\d{6}',  # _20250617_143117
            r'_\d{8}',        # _20250617
            r'_\d{6}',        # _143117
            r'_\d{4}\d{2}\d{2}_\d{6}',  # _20250617_143117
        ]
        
        self.backup_extensions = ['.backup', '.bak', '.old', '.orig']
        
        # Directories to skip
        self.skip_dirs = {
            '.git', '.vscode', '__pycache__', 'node_modules', 
            '.pytest_cache', '.mypy_cache', 'venv', 'env'
        }

    def run_cleanup(self, dry_run: bool = False) -> Dict:
        """Run the complete cleanup process"""
        print(f"🔍 Starting comprehensive duplicate cleanup...")
        print(f"📁 Project root: {self.project_root}")
        print(f"💾 Backup location: {self.backup_root}")
        print(f"🔄 Mode: {'DRY RUN' if dry_run else 'LIVE CLEANUP'}")
        print("=" * 60)
        
        try:
            # Step 1: Clean backup folders
            print("\n📂 Step 1: Cleaning backup folders...")
            self.clean_backup_folders(dry_run)
            
            # Step 2: Clean timestamp files
            print("\n📅 Step 2: Cleaning timestamp files...")
            self.clean_timestamp_files(dry_run)
            
            # Step 3: Clean backup extensions
            print("\n🔄 Step 3: Cleaning backup extensions...")
            self.clean_backup_extensions(dry_run)
            
            # Step 4: Find and remove exact duplicates
            print("\n🔗 Step 4: Finding exact duplicates...")
            self.clean_exact_duplicates(dry_run)
            
            # Step 5: Find and merge similar files
            print("\n📝 Step 5: Finding similar files...")
            self.clean_similar_files(dry_run)
            
            # Step 6: Clean empty directories
            print("\n📁 Step 6: Cleaning empty directories...")
            self.clean_empty_directories(dry_run)
            
            # Generate report
            self.generate_report(dry_run)
            
        except Exception as e:
            self.report["errors"].append(f"General error: {str(e)}")
            print(f"❌ Error during cleanup: {e}")
        
        return self.report

    def clean_backup_folders(self, dry_run: bool = False):
        """Remove redundant backup folders"""
        backup_folders = []
        
        # Find all backup-related folders
        for root, dirs, files in os.walk(self.project_root):
            for dir_name in dirs:
                if any(pattern in dir_name.lower() for pattern in 
                       ['backup', 'pre_merge', 'pre_organization', 'archive']):
                    folder_path = Path(root) / dir_name
                    backup_folders.append(folder_path)
        
        # Group by timestamp patterns
        grouped_backups = {}
        for folder in backup_folders:
            base_name = re.sub(r'_\d{8}_\d{6}', '', folder.name)
            if base_name not in grouped_backups:
                grouped_backups[base_name] = []
            grouped_backups[base_name].append(folder)
        
        # Keep only the newest in each group
        for group_name, folders in grouped_backups.items():
            if len(folders) > 1:
                # Sort by modification time, keep newest
                folders_sorted = sorted(folders, key=lambda x: x.stat().st_mtime, reverse=True)
                keep_folder = folders_sorted[0]
                
                for folder in folders_sorted[1:]:
                    self.report["categories"]["backup_folders"]["found"] += 1
                    self.report["categories"]["backup_folders"]["files"].append(str(folder))
                    
                    if not dry_run:
                        try:
                            # Move to backup before deletion
                            backup_path = self.backup_root / "removed_backup_folders" / folder.name
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(folder), str(backup_path))
                            self.report["categories"]["backup_folders"]["removed"] += 1
                            print(f"🗑️  Moved backup folder: {folder.name}")
                        except Exception as e:
                            self.report["errors"].append(f"Failed to remove backup folder {folder}: {e}")

    def clean_timestamp_files(self, dry_run: bool = False):
        """Remove files with timestamp patterns"""
        timestamp_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Check if file has timestamp pattern
                has_timestamp = any(re.search(pattern, file_name) for pattern in self.timestamp_patterns)
                
                if has_timestamp:
                    # Check if there's a non-timestamp version
                    base_name = file_name
                    for pattern in self.timestamp_patterns:
                        base_name = re.sub(pattern, '', base_name)
                    
                    base_path = file_path.parent / base_name
                    if base_path.exists() and base_path != file_path:
                        timestamp_files.append(file_path)
        
        # Remove timestamp files
        for file_path in timestamp_files:
            self.report["categories"]["timestamp_files"]["found"] += 1
            self.report["categories"]["timestamp_files"]["files"].append(str(file_path))
            
            if not dry_run:
                try:
                    # Move to backup
                    backup_path = self.backup_root / "timestamp_files" / file_path.relative_to(self.project_root)
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(backup_path))
                    self.report["categories"]["timestamp_files"]["removed"] += 1
                    print(f"🗑️  Moved timestamp file: {file_path.name}")
                except Exception as e:
                    self.report["errors"].append(f"Failed to remove timestamp file {file_path}: {e}")

    def clean_backup_extensions(self, dry_run: bool = False):
        """Remove files with backup extensions"""
        backup_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Check if file has backup extension
                if any(file_name.endswith(ext) for ext in self.backup_extensions):
                    backup_files.append(file_path)
        
        # Remove backup files
        for file_path in backup_files:
            self.report["categories"]["backup_extensions"]["found"] += 1
            self.report["categories"]["backup_extensions"]["files"].append(str(file_path))
            
            if not dry_run:
                try:
                    # Move to backup
                    backup_path = self.backup_root / "backup_extensions" / file_path.relative_to(self.project_root)
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(backup_path))
                    self.report["categories"]["backup_extensions"]["removed"] += 1
                    print(f"🗑️  Moved backup file: {file_path.name}")
                except Exception as e:
                    self.report["errors"].append(f"Failed to remove backup file {file_path}: {e}")

    def clean_exact_duplicates(self, dry_run: bool = False):
        """Find and remove exact duplicate files"""
        file_hashes = {}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Skip very large files and certain types
                if file_path.stat().st_size > 100 * 1024 * 1024:  # Skip files > 100MB
                    continue
                
                if file_path.suffix.lower() in {'.exe', '.dll', '.so', '.dylib'}:
                    continue
                
                try:
                    # Calculate file hash
                    hash_value = self.calculate_file_hash(file_path)
                    if hash_value not in file_hashes:
                        file_hashes[hash_value] = []
                    file_hashes[hash_value].append(file_path)
                except Exception as e:
                    self.report["errors"].append(f"Failed to hash file {file_path}: {e}")
        
        # Process duplicate groups
        for hash_value, files in file_hashes.items():
            if len(files) > 1:
                # Sort by priority (keep files in main directories)
                priority_order = ['src', 'scripts', 'contracts', 'docs', 'mcp_servers', 'ai_agents']
                
                def get_priority(file_path: Path) -> int:
                    parts = file_path.parts
                    for i, priority_dir in enumerate(priority_order):
                        if priority_dir in parts:
                            return i
                    return len(priority_order)
                
                sorted_files = sorted(files, key=get_priority)
                keep_file = sorted_files[0]
                duplicate_files = sorted_files[1:]
                
                self.report["categories"]["exact_duplicates"]["groups"].append({
                    "keep": str(keep_file),
                    "remove": [str(f) for f in duplicate_files]
                })
                
                for file_path in duplicate_files:
                    self.report["categories"]["exact_duplicates"]["found"] += 1
                    
                    if not dry_run:
                        try:
                            # Move to backup
                            backup_path = self.backup_root / "exact_duplicates" / file_path.relative_to(self.project_root)
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(file_path), str(backup_path))
                            self.report["categories"]["exact_duplicates"]["removed"] += 1
                            print(f"🗑️  Moved duplicate: {file_path.name}")
                        except Exception as e:
                            self.report["errors"].append(f"Failed to remove duplicate {file_path}: {e}")

    def clean_similar_files(self, dry_run: bool = False):
        """Find and merge similar files"""
        # Group files by name similarity
        file_groups = {}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Only process text files
                if file_path.suffix.lower() not in {'.py', '.js', '.md', '.txt', '.json', '.yaml', '.yml'}:
                    continue
                
                # Group by base name (without extensions and modifiers)
                base_name = self.get_base_name(file_name)
                if base_name not in file_groups:
                    file_groups[base_name] = []
                file_groups[base_name].append(file_path)
        
        # Process similar file groups
        for base_name, files in file_groups.items():
            if len(files) > 1:
                similar_groups = self.find_similar_files(files)
                for group in similar_groups:
                    if len(group) > 1:
                        # Keep the most complete version
                        keep_file = max(group, key=lambda x: x.stat().st_size)
                        remove_files = [f for f in group if f != keep_file]
                        
                        self.report["categories"]["similar_files"]["groups"].append({
                            "keep": str(keep_file),
                            "remove": [str(f) for f in remove_files]
                        })
                        
                        for file_path in remove_files:
                            self.report["categories"]["similar_files"]["found"] += 1
                            
                            if not dry_run:
                                try:
                                    # Move to backup
                                    backup_path = self.backup_root / "similar_files" / file_path.relative_to(self.project_root)
                                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(file_path), str(backup_path))
                                    self.report["categories"]["similar_files"]["removed"] += 1
                                    print(f"🗑️  Moved similar file: {file_path.name}")
                                except Exception as e:
                                    self.report["errors"].append(f"Failed to remove similar file {file_path}: {e}")

    def clean_empty_directories(self, dry_run: bool = False):
        """Remove empty directories"""
        empty_dirs = []
        
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()) and dir_name not in self.skip_dirs:
                        empty_dirs.append(dir_path)
                except (OSError, PermissionError):
                    continue
        
        for dir_path in empty_dirs:
            self.report["categories"]["empty_dirs"]["found"] += 1
            self.report["categories"]["empty_dirs"]["dirs"].append(str(dir_path))
            
            if not dry_run:
                try:
                    dir_path.rmdir()
                    self.report["categories"]["empty_dirs"]["removed"] += 1
                    print(f"🗑️  Removed empty directory: {dir_path.name}")
                except Exception as e:
                    self.report["errors"].append(f"Failed to remove empty directory {dir_path}: {e}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_base_name(self, file_name: str) -> str:
        """Get base name without modifiers"""
        # Remove extensions
        base = file_name.split('.')[0]
        
        # Remove common modifiers
        modifiers = ['_fixed', '_final', '_new', '_old', '_copy', '_backup', '_temp', '_test']
        for modifier in modifiers:
            base = base.replace(modifier, '')
        
        # Remove timestamp patterns
        for pattern in self.timestamp_patterns:
            base = re.sub(pattern, '', base)
        
        return base.lower()

    def find_similar_files(self, files: List[Path]) -> List[List[Path]]:
        """Group files by content similarity"""
        groups = []
        processed = set()
        
        for i, file1 in enumerate(files):
            if file1 in processed:
                continue
            
            group = [file1]
            processed.add(file1)
            
            for j, file2 in enumerate(files[i+1:], i+1):
                if file2 in processed:
                    continue
                
                try:
                    if self.are_files_similar(file1, file2):
                        group.append(file2)
                        processed.add(file2)
                except Exception:
                    continue
            
            if len(group) > 1:
                groups.append(group)
        
        return groups

    def are_files_similar(self, file1: Path, file2: Path, threshold: float = 0.8) -> bool:
        """Check if two files are similar based on content"""
        try:
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f1:
                content1 = f1.readlines()
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f2:
                content2 = f2.readlines()
            
            # Use difflib to calculate similarity
            similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
            return similarity >= threshold
        except Exception:
            return False

    def generate_report(self, dry_run: bool = False):
        """Generate cleanup report"""
        report_path = self.project_root / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Calculate totals
        total_found = sum(cat["found"] for cat in self.report["categories"].values())
        total_removed = sum(cat["removed"] for cat in self.report["categories"].values())
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE DUPLICATE CLEANUP SUMMARY")
        print("=" * 60)
        print(f"🔍 Total duplicates found: {total_found}")
        print(f"🗑️  Total duplicates {'would be' if dry_run else ''} removed: {total_removed}")
        print(f"📁 Backup location: {self.backup_root}")
        
        for category, data in self.report["categories"].items():
            if data["found"] > 0:
                print(f"📂 {category.replace('_', ' ').title()}: {data['found']} found, {data['removed']} {'would be' if dry_run else ''} removed")
        
        if self.report["errors"]:
            print(f"⚠️  Errors encountered: {len(self.report['errors'])}")
        
        # Save detailed report
        if not dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False)
            print(f"📋 Detailed report saved: {report_path}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    # Ask for confirmation
    print("🧹 Comprehensive Duplicate Cleaner")
    print("=" * 40)
    print(f"Project root: {project_root}")
    print("\nThis will clean up:")
    print("  • Redundant backup folders")
    print("  • Files with timestamp patterns") 
    print("  • Files with backup extensions")
    print("  • Exact duplicate files")
    print("  • Similar files with minor differences")
    print("  • Empty directories")
    
    mode = input("\nChoose mode (1=Dry Run, 2=Live Cleanup, 3=Cancel): ").strip()
    
    if mode == "3":
        print("🚫 Cleanup cancelled.")
        return
    
    dry_run = mode != "2"
    
    if not dry_run:
        confirm = input("⚠️  Are you sure you want to proceed with live cleanup? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("🚫 Cleanup cancelled.")
            return
    
    # Run cleanup
    cleaner = ComprehensiveDuplicateCleaner(project_root)
    report = cleaner.run_cleanup(dry_run=dry_run)
    
    print(f"\n✅ Cleanup {'simulation' if dry_run else 'completed'} successfully!")

if __name__ == "__main__":
    main()
