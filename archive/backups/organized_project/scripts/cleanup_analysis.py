#!/usr/bin/env python3
"""
Duplicate Detection and Cleanup Script
Identifies remaining duplicate files that can be safely archived
"""

import os
import hashlib
from pathlib import Path
from collections import defaultdict

def get_file_hash(filepath):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def find_duplicates(root_dir):
    """Find duplicate files in the project"""
    file_hashes = defaultdict(list)
    duplicates = []
    
    # Walk through all files
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.venv', 'node_modules', 'organized_project'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            filepath = os.path.join(root, file)
            if os.path.isfile(filepath) and not file.startswith('.'):
                file_hash = get_file_hash(filepath)
                if file_hash:
                    file_hashes[file_hash].append(filepath)
    
    # Identify duplicates
    for hash_val, files in file_hashes.items():
        if len(files) > 1:
            duplicates.append(files)
    
    return duplicates

def identify_files_to_archive(root_dir):
    """Identify files that should be archived"""
    archive_candidates = []
    
    patterns = [
        '*.bak',
        '*.backup',
        '*_backup*',
        '*_old*',
        '*_duplicate*',
        '*.log',
        '*test_report*',
        'backup_*'
    ]
    
    for pattern in patterns:
        for filepath in Path(root_dir).rglob(pattern):
            if 'organized_project' not in str(filepath):
                archive_candidates.append(str(filepath))
    
    return archive_candidates

def main():
    root_dir = r"c:\Users\Ratanshila\Documents\flash loan"
    
    print("=== Flash Loan Project Cleanup Report ===")
    print()
    
    print("1. DUPLICATE FILES DETECTED:")
    duplicates = find_duplicates(root_dir)
    for i, dup_group in enumerate(duplicates, 1):
        print(f"\n   Group {i}:")
        for filepath in dup_group:
            print(f"     - {filepath}")
    
    print(f"\n   Total duplicate groups: {len(duplicates)}")
    
    print("\n2. FILES TO ARCHIVE:")
    archive_files = identify_files_to_archive(root_dir)
    for filepath in archive_files[:20]:  # Show first 20
        print(f"     - {filepath}")
    
    if len(archive_files) > 20:
        print(f"     ... and {len(archive_files) - 20} more files")
    
    print(f"\n   Total files to archive: {len(archive_files)}")
    
    print("\n3. ORGANIZATION SUMMARY:")
    organized_path = os.path.join(root_dir, "organized_project")
    if os.path.exists(organized_path):
        print(f"   ✓ Organized project created at: {organized_path}")
        
        # Count files in organized structure
        total_files = 0
        for root, dirs, files in os.walk(organized_path):
            total_files += len([f for f in files if not f.startswith('.')])
        
        print(f"   ✓ Total files in organized structure: {total_files}")
        
        # Show structure
        print("   ✓ Directory structure:")
        for item in os.listdir(organized_path):
            item_path = os.path.join(organized_path, item)
            if os.path.isdir(item_path):
                file_count = sum(len(files) for _, _, files in os.walk(item_path))
                print(f"     - {item}/ ({file_count} files)")
    
    print("\n4. RECOMMENDED NEXT STEPS:")
    print("   1. Review organized_project/ structure")
    print("   2. Test system functionality with new structure")
    print("   3. Update any hardcoded paths in configuration files")
    print("   4. Archive or remove duplicate files from original locations")
    print("   5. Update documentation with new structure")

if __name__ == "__main__":
    main()
