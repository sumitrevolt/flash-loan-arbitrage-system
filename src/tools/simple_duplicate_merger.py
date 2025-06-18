#!/usr/bin/env python3
"""
Simple Duplicate File Merger
============================

A straightforward script to identify and merge duplicate files based on:
1. Exact content matches (MD5 hash)
2. File name patterns
3. Simple text similarity

Author: GitHub Copilot Assistant
"""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
import difflib

class SimpleDuplicateMerger:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.duplicates = {}
        self.merge_report = {
            "timestamp": datetime.now().isoformat(),
            "total_files_scanned": 0,
            "duplicate_groups": 0,
            "files_merged": 0,
            "space_saved": 0,
            "details": []
        }
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"Error hashing {file_path}: {e}")
            return ""
    
    def find_duplicates(self) -> Dict[str, List[Path]]:
        """Find duplicate files by content hash"""
        hash_to_files = {}
        
        # Scan all files
        for file_path in self.root_dir.rglob("*"):
            if file_path.is_file():
                self.merge_report["total_files_scanned"] += 1
                
                # Skip certain file types
                if file_path.suffix.lower() in ['.pyc', '.pyo', '.log', '.tmp']:
                    continue
                
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    if file_hash not in hash_to_files:
                        hash_to_files[file_hash] = []
                    hash_to_files[file_hash].append(file_path)
        
        # Filter to only groups with duplicates
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        self.merge_report["duplicate_groups"] = len(duplicates)
        
        return duplicates
    
    def find_similar_names(self) -> Dict[str, List[Path]]:
        """Find files with similar names that might be duplicates"""
        name_groups = {}
        
        for file_path in self.root_dir.rglob("*"):
            if file_path.is_file():
                # Group by base name (without extension)
                base_name = file_path.stem.lower()
                
                # Skip common names
                if base_name in ['readme', 'index', 'main', 'app', 'config']:
                    continue
                
                if base_name not in name_groups:
                    name_groups[base_name] = []
                name_groups[base_name].append(file_path)
        
        # Filter to groups with multiple files
        return {name: files for name, files in name_groups.items() if len(files) > 1}
    
    def merge_duplicate_group(self, files: List[Path], dry_run: bool = False) -> bool:
        """Merge a group of duplicate files"""
        if len(files) < 2:
            return False
        
        # Choose the "best" file to keep (prefer shorter path, no backup suffix)
        def file_priority(f: Path) -> Tuple[int, int, str]:
            # Lower numbers = higher priority
            backup_penalty = 10 if any(suffix in f.name.lower() for suffix in ['.backup', '.bak', '_backup', '_old']) else 0
            return (backup_penalty, len(str(f)), str(f))
        
        sorted_files = sorted(files, key=file_priority)
        keep_file = sorted_files[0]
        remove_files = sorted_files[1:]
        
        total_size = sum(f.stat().st_size for f in files)
        saved_size = sum(f.stat().st_size for f in remove_files)
        
        merge_detail = {
            "kept_file": str(keep_file),
            "removed_files": [str(f) for f in remove_files],
            "total_size": total_size,
            "space_saved": saved_size
        }
        
        if not dry_run:
            # Create backup directory
            backup_dir = self.root_dir / "duplicate_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Move duplicates to backup
            for file_to_remove in remove_files:
                try:
                    backup_path = backup_dir / file_to_remove.name
                    shutil.move(str(file_to_remove), str(backup_path))
                    print(f"Moved {file_to_remove} to backup: {backup_path}")
                except Exception as e:
                    print(f"Error moving {file_to_remove}: {e}")
                    merge_detail["errors"] = merge_detail.get("errors", []) + [str(e)]
        
        self.merge_report["details"].append(merge_detail)
        self.merge_report["files_merged"] += len(remove_files)
        self.merge_report["space_saved"] += saved_size
        
        return True
    
    def analyze_text_similarity(self, file1: Path, file2: Path) -> float:
        """Calculate text similarity between two files"""
        try:
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f1:
                content1 = f1.read()
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f2:
                content2 = f2.read()
            
            # Use difflib to calculate similarity
            return difflib.SequenceMatcher(None, content1, content2).ratio()
        except Exception:
            return 0.0
    
    def merge_similar_files(self, similarity_threshold: float = 0.8, dry_run: bool = False):
        """Merge files that are very similar but not identical"""
        similar_groups = self.find_similar_names()
        
        for group_name, files in similar_groups.items():
            if len(files) < 2:
                continue
            
            # Check text similarity within the group
            to_merge = []
            for i, file1 in enumerate(files):
                for file2 in files[i+1:]:
                    similarity = self.analyze_text_similarity(file1, file2)
                    if similarity >= similarity_threshold:
                        # Group similar files
                        group = [file1, file2]
                        for existing_group in to_merge:
                            if file1 in existing_group or file2 in existing_group:
                                existing_group.extend(group)
                                break
                        else:
                            to_merge.append(group)
            
            # Merge each similar group
            for similar_files in to_merge:
                unique_files = list(set(similar_files))  # Remove duplicates
                if len(unique_files) > 1:
                    print(f"Merging similar files in group '{group_name}': {[str(f) for f in unique_files]}")
                    self.merge_duplicate_group(unique_files, dry_run)
    
    def run_merge(self, dry_run: bool = False, include_similar: bool = True):
        """Run the complete merge process"""
        print(f"{'DRY RUN: ' if dry_run else ''}Scanning for duplicates in: {self.root_dir}")
        
        # Find exact duplicates
        exact_duplicates = self.find_duplicates()
        print(f"Found {len(exact_duplicates)} groups of exact duplicates")
        
        # Merge exact duplicates
        for file_hash, files in exact_duplicates.items():
            print(f"Merging duplicate group: {[str(f) for f in files]}")
            self.merge_duplicate_group(files, dry_run)
        
        # Merge similar files if requested
        if include_similar:
            print("Analyzing similar files...")
            self.merge_similar_files(dry_run=dry_run)
        
        # Generate report
        report_path = self.root_dir / f"duplicate_merge_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if not dry_run:
            with open(report_path, 'w') as f:
                json.dump(self.merge_report, f, indent=2)
            print(f"Merge report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*50)
        print("DUPLICATE MERGE SUMMARY")
        print("="*50)
        print(f"Total files scanned: {self.merge_report['total_files_scanned']}")
        print(f"Duplicate groups found: {self.merge_report['duplicate_groups']}")
        print(f"Files merged: {self.merge_report['files_merged']}")
        print(f"Space saved: {self.merge_report['space_saved']:,} bytes")
        
        return self.merge_report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Duplicate File Merger")
    parser.add_argument("--directory", "-d", default=".", help="Directory to scan for duplicates")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--no-similar", action="store_true", help="Only merge exact duplicates, skip similar files")
    
    args = parser.parse_args()
    
    merger = SimpleDuplicateMerger(args.directory)
    merger.run_merge(dry_run=args.dry_run, include_similar=not args.no_similar)

if __name__ == "__main__":
    main()
