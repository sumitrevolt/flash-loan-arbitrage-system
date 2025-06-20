#!/usr/bin/env python3
"""
Targeted Duplicate Cleaner for Flash Loan Project
================================================

This script focuses on cleaning the most obvious duplicates:
1. Multiple backup folders with timestamps (backups/pre_merge_20250619_*)
2. Files with _20250617 timestamp patterns  
3. Files with .backup extensions
4. Empty directories

Author: GitHub Copilot Assistant
Date: June 19, 2025
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
import re

class TargetedDuplicateCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_root = self.project_root / "cleanup_backup" / f"targeted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.removed_items = []
        self.errors = []
        self.space_saved = 0

    def clean_backup_folders(self, dry_run: bool = False):
        """Remove redundant backup folders"""
        print("🔍 Scanning for redundant backup folders...")
        
        backup_base = self.project_root / "backups"
        if not backup_base.exists():
            print("No backups folder found")
            return
        
        # Find all pre_merge folders with timestamps
        pre_merge_folders = []
        for item in backup_base.iterdir():
            if item.is_dir() and item.name.startswith("pre_merge_20250619"):
                pre_merge_folders.append(item)
        
        if len(pre_merge_folders) <= 1:
            print("No redundant backup folders found")
            return
        
        # Sort by creation time, keep the newest
        pre_merge_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        keep_folder = pre_merge_folders[0]
        remove_folders = pre_merge_folders[1:]
        
        print(f"📁 Found {len(remove_folders)} redundant backup folders")
        print(f"✅ Keeping: {keep_folder.name}")
        
        for folder in remove_folders:
            folder_size = self.get_folder_size(folder)
            print(f"🗑️  {'Would remove' if dry_run else 'Removing'}: {folder.name} ({self.format_size(folder_size)})")
            
            if not dry_run:
                try:
                    shutil.rmtree(folder)
                    self.removed_items.append(f"Backup folder: {folder.name}")
                    self.space_saved += folder_size
                except Exception as e:
                    self.errors.append(f"Failed to remove {folder}: {e}")
                    print(f"❌ Error removing {folder.name}: {e}")

    def clean_timestamp_files(self, dry_run: bool = False):
        """Remove files with _20250617 patterns that have non-timestamp equivalents"""
        print("🔍 Scanning for timestamp files...")
        
        timestamp_files = []
        
        # Find files with timestamp patterns
        for root, dirs, files in os.walk(self.project_root):
            # Skip backup directories we just cleaned
            if "backup" in root.lower():
                continue
                
            for file_name in files:
                if "_20250617" in file_name:
                    file_path = Path(root) / file_name
                    
                    # Check if non-timestamp version exists
                    base_name = file_name.replace("_20250617_143117", "").replace("_20250617_143116", "").replace("_20250617", "")
                    base_path = file_path.parent / base_name
                    
                    if base_path.exists() and base_path != file_path:
                        timestamp_files.append(file_path)
        
        print(f"📁 Found {len(timestamp_files)} timestamp files with base equivalents")
        
        for file_path in timestamp_files:
            file_size = file_path.stat().st_size
            print(f"🗑️  {'Would remove' if dry_run else 'Removing'}: {file_path.relative_to(self.project_root)} ({self.format_size(file_size)})")
            
            if not dry_run:
                try:
                    file_path.unlink()
                    self.removed_items.append(f"Timestamp file: {file_path.name}")
                    self.space_saved += file_size
                except Exception as e:
                    self.errors.append(f"Failed to remove {file_path}: {e}")
                    print(f"❌ Error removing {file_path.name}: {e}")

    def clean_backup_extensions(self, dry_run: bool = False):
        """Remove .backup files"""
        print("🔍 Scanning for .backup files...")
        
        backup_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            if "backup" in root.lower():
                continue
                
            for file_name in files:
                if file_name.endswith('.backup'):
                    file_path = Path(root) / file_name
                    backup_files.append(file_path)
        
        print(f"📁 Found {len(backup_files)} .backup files")
        
        for file_path in backup_files:
            file_size = file_path.stat().st_size
            print(f"🗑️  {'Would remove' if dry_run else 'Removing'}: {file_path.relative_to(self.project_root)} ({self.format_size(file_size)})")
            
            if not dry_run:
                try:
                    file_path.unlink()
                    self.removed_items.append(f"Backup file: {file_path.name}")
                    self.space_saved += file_size
                except Exception as e:
                    self.errors.append(f"Failed to remove {file_path}: {e}")
                    print(f"❌ Error removing {file_path.name}: {e}")

    def clean_obvious_duplicates(self, dry_run: bool = False):
        """Remove some obvious duplicate files"""
        print("🔍 Scanning for obvious duplicate files...")
        
        # Specific files we know are duplicates
        obvious_duplicates = [
            "src/tools/simple_duplicate_merger.py",  # Keep the one in the root level
            "master_project_organizer.py"  # Multiple copies exist
        ]
        
        for duplicate_pattern in obvious_duplicates:
            matching_files = list(self.project_root.rglob(duplicate_pattern))
            
            if len(matching_files) > 1:
                # Keep the one in the main directory level
                main_file = None
                others = []
                
                for file_path in matching_files:
                    if len(file_path.parts) <= 4:  # Closer to root
                        main_file = file_path
                    else:
                        others.append(file_path)
                
                if main_file and others:
                    print(f"✅ Keeping: {main_file.relative_to(self.project_root)}")
                    
                    for file_path in others:
                        file_size = file_path.stat().st_size
                        print(f"🗑️  {'Would remove' if dry_run else 'Removing'}: {file_path.relative_to(self.project_root)}")
                        
                        if not dry_run:
                            try:
                                file_path.unlink()
                                self.removed_items.append(f"Duplicate file: {file_path.name}")
                                self.space_saved += file_size
                            except Exception as e:
                                self.errors.append(f"Failed to remove {file_path}: {e}")

    def clean_empty_directories(self, dry_run: bool = False):
        """Remove empty directories"""
        print("🔍 Scanning for empty directories...")
        
        empty_dirs = []
        
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()) and dir_name not in {'.git', '.vscode', '__pycache__'}:
                        empty_dirs.append(dir_path)
                except (OSError, PermissionError):
                    continue
        
        print(f"📁 Found {len(empty_dirs)} empty directories")
        
        for dir_path in empty_dirs:
            print(f"🗑️  {'Would remove' if dry_run else 'Removing'} empty dir: {dir_path.relative_to(self.project_root)}")
            
            if not dry_run:
                try:
                    dir_path.rmdir()
                    self.removed_items.append(f"Empty directory: {dir_path.name}")
                except Exception as e:
                    self.errors.append(f"Failed to remove {dir_path}: {e}")

    def get_folder_size(self, folder_path: Path) -> int:
        """Calculate total size of folder"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file_name in files:
                    file_path = Path(root) / file_name
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except Exception:
            pass
        return total_size

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def run_cleanup(self, dry_run: bool = False):
        """Run the targeted cleanup"""
        print("🎯 Starting targeted duplicate cleanup...")
        print(f"📁 Project root: {self.project_root}")
        print(f"🔄 Mode: {'DRY RUN' if dry_run else 'LIVE CLEANUP'}")
        print("=" * 60)
        
        # Step 1: Clean backup folders
        self.clean_backup_folders(dry_run)
        print()
        
        # Step 2: Clean timestamp files
        self.clean_timestamp_files(dry_run)
        print()
        
        # Step 3: Clean backup extensions
        self.clean_backup_extensions(dry_run)
        print()
        
        # Step 4: Clean obvious duplicates
        self.clean_obvious_duplicates(dry_run)
        print()
        
        # Step 5: Clean empty directories
        self.clean_empty_directories(dry_run)
        print()
        
        # Summary
        print("=" * 60)
        print("📊 TARGETED CLEANUP SUMMARY")
        print("=" * 60)
        print(f"🗑️  Items {'would be' if dry_run else ''} removed: {len(self.removed_items)}")
        print(f"💾 Space {'would be' if dry_run else ''} saved: {self.format_size(self.space_saved)}")
        
        if self.errors:
            print(f"⚠️  Errors: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"   {error}")
        
        if not dry_run and self.removed_items:
            # Save log
            log_path = self.project_root / f"cleanup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("Targeted Duplicate Cleanup Log\n")
                f.write(f"Date: {datetime.now().isoformat()}\n")
                f.write(f"Removed {len(self.removed_items)} items\n")
                f.write(f"Space saved: {self.format_size(self.space_saved)}\n\n")
                f.write("Removed items:\n")
                for item in self.removed_items:
                    f.write(f"- {item}\n")
                if self.errors:
                    f.write("\nErrors:\n")
                    for error in self.errors:
                        f.write(f"- {error}\n")
            print(f"📋 Log saved: {log_path}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    print("🎯 Targeted Duplicate Cleaner")
    print("=" * 40)
    print(f"Project root: {project_root}")
    print("\nThis will clean up:")
    print("  • Redundant backup folders (pre_merge_20250619_*)")
    print("  • Files with _20250617 timestamps") 
    print("  • Files with .backup extensions")
    print("  • Some obvious duplicate files")
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
    cleaner = TargetedDuplicateCleaner(project_root)
    cleaner.run_cleanup(dry_run=dry_run)
    
    print(f"\n✅ Targeted cleanup {'simulation' if dry_run else 'completed'} successfully!")

if __name__ == "__main__":
    main()
