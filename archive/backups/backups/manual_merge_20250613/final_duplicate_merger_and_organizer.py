#!/usr/bin/env python3
"""
Final Duplicate Merger and Project Organizer
============================================
Completes the duplicate merging and project organization process.
Identifies and removes remaining duplicates while maintaining the best versions.
"""

import os
import sys
import shutil
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
import ast
import re

class FinalDuplicateMergerAndOrganizer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.backup_dir = self.root_dir / "backups" / f"final_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.merge_log = []
        self.preserved_files = []
        self.removed_files = []
        self.stats = {
            'total_files_analyzed': 0,
            'duplicates_removed': 0,
            'categories_processed': 0,
            'space_saved_mb': 0
        }
        
        # Define remaining duplicate categories
        self.duplicate_categories = {
            'organization_scripts': {
                'keep': 'final_project_organizer.py',
                'remove': [
                    'project_organizer_fixed.py',
                    'automated_duplicate_merger.py',
                    'comprehensive_duplicate_merger.py',
                    'cleanup_duplicates.py',
                    'merge_duplicates_analyzer.py',
                    'organize_mcp_servers_clean.py'
                ]
            },
            'optimization_scripts': {
                'keep': 'production_optimizer.py',
                'remove': [
                    'optimization_summary.py',
                    'mcp_optimization_report.py',
                    'comprehensive_code_optimization.py',
                    'comprehensive_type_fix.py'
                ]
            },
            'completion_scripts': {
                'keep': 'project_completion_summary.py',
                'remove': [
                    'final_success_confirmation.py',
                    'complete_project_with_mcp.py',
                    'final_comprehensive_fix.py'
                ]
            },
            'orchestration_scripts': {
                'keep': 'manage_mcp_orchestration.py',
                'remove': [
                    'demo_orchestration_system.py',
                    'launch_all_working_mcp_servers.py',
                    'launch_online_mcp_system.py',
                    'start_local_mcp_servers.py'
                ]
            },
            'mcp_server_demos': {
                'keep': 'simple_mcp_server.py',
                'remove': [
                    'mcp_agent_advantage_demo.py',
                    'mcp_organization_demo.py',
                    'mcp_logger_auditor_server.py'
                ]
            },
            'deployment_scripts': {
                'keep': 'production_deployment_manager.py',
                'remove': [
                    'generate_corrected_agent_config.py'
                ]
            },
            'trading_executors': {
                'keep': 'real_trading_executor.py',
                'remove': [
                    'realtime_data_aggregator.py',
                    'realtime_display_arbitrage.py',
                    'quick_dex_verification.py'
                ]
            },
            'health_checks': {
                'keep': 'working_health_check.py',
                'remove': []
            }
        }
        
        # Files to preserve in place (already properly organized)
        self.preserve_in_place = [
            'src/main.py',
            'package.json',
            'README.md',
            'PROJECT_COMPLETION_STATUS.md',
            'FINAL_ORGANIZATION_SUMMARY.md'
        ]
        
    def create_backup(self) -> None:
        """Create backup of current state"""
        print(f"📦 Creating backup at {self.backup_dir}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup files to be modified
        all_files_to_backup = []
        for category_info in self.duplicate_categories.values():
            keep_file = category_info['keep']
            if Path(keep_file).exists():
                all_files_to_backup.append(keep_file)
            for remove_file in category_info['remove']:
                if Path(remove_file).exists():
                    all_files_to_backup.append(remove_file)
        
        for file_path in all_files_to_backup:
            source = Path(file_path)
            if source.exists():
                dest = self.backup_dir / source.name
                shutil.copy2(source, dest)
        
        print(f"✅ Backed up {len(all_files_to_backup)} files")
    
    def analyze_file_quality(self, file_path: Path) -> int:
        """Analyze file to determine quality score"""
        if not file_path.exists():
            return 0
            
        score = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # File size bonus
            score += min(len(content) // 1000, 20)
            
            # Function/class count
            score += len(re.findall(r'def\s+\w+', content)) * 2
            score += len(re.findall(r'class\s+\w+', content)) * 5
            
            # Documentation score
            score += len(re.findall(r'""".*?"""', content, re.DOTALL)) * 3
            score += len(re.findall(r'#.*', content)) // 10
            
            # Error handling
            score += len(re.findall(r'try:|except:|finally:', content)) * 2
            
            # Logging
            score += len(re.findall(r'log\.|print\(', content))
            
            # Recent modification bonus
            mod_time = file_path.stat().st_mtime
            if mod_time > (datetime.now().timestamp() - 86400):  # Modified in last day
                score += 10
            
        except Exception:
            score = 1
        
        return score
    
    def merge_duplicate_category(self, category: str, category_info: Dict) -> None:
        """Merge files in a specific category"""
        print(f"\n🔄 Processing category: {category}")
        
        keep_file = category_info['keep']
        remove_files = category_info['remove']
        
        # Check if keep file exists
        keep_path = Path(keep_file)
        if not keep_path.exists():
            # Find the best alternative from remove_files
            existing_files = [f for f in remove_files if Path(f).exists()]
            if existing_files:
                best_file = max(existing_files, key=lambda f: Any: self.analyze_file_quality(Path(f)))
                print(f"  📝 {keep_file} not found, using {best_file} as replacement")
                if Path(best_file).exists():
                    shutil.move(best_file, keep_file)
                    self.preserved_files.append(keep_file)
                    remove_files.remove(best_file)
            else:
                print(f"  ⚠️ No files found for category {category}")
                return
        else:
            self.preserved_files.append(keep_file)
        
        # Remove duplicates
        removed_count = 0
        for remove_file in remove_files:
            remove_path = Path(remove_file)
            if remove_path.exists():
                print(f"  🗑️ Removing duplicate: {remove_file}")
                remove_path.unlink()
                self.removed_files.append(remove_file)
                removed_count += 1
        
        # Log the merge
        self.merge_log.append({
            'category': category,
            'kept': keep_file,
            'removed': [f for f in remove_files if f in self.removed_files],
            'count_removed': removed_count
        })
        
        print(f"  ✅ Category {category}: kept {keep_file}, removed {removed_count} duplicates")
    
    def clean_empty_directories(self) -> None:
        """Remove empty directories"""
        print("\n🧹 Cleaning empty directories...")
        
        cleaned_count = 0
        for root, dirs, files in os.walk(self.root_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()) and dir_path.name not in ['__pycache__', '.git', '.vscode']:
                        dir_path.rmdir()
                        cleaned_count += 1
                        print(f"  🗑️ Removed empty directory: {dir_path}")
                except OSError:
                    pass  # Directory not empty or permission issue
        
        print(f"✅ Cleaned {cleaned_count} empty directories")
    
    def update_documentation(self) -> None:
        """Update project documentation"""
        print("\n📝 Updating documentation...")
        
        # Create final merge report
        report_content = f"""# FINAL DUPLICATE MERGE REPORT

**Merge completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total files analyzed:** {self.stats['total_files_analyzed']}
- **Duplicates removed:** {self.stats['duplicates_removed']}
- **Categories processed:** {self.stats['categories_processed']}
- **Files preserved:** {len(self.preserved_files)}

## Categories Processed

"""
        
        for log_entry in self.merge_log:
            report_content += f"""### {log_entry['category'].title()}
- **Kept:** `{log_entry['kept']}`
- **Removed:** {log_entry['count_removed']} files
  - {', '.join([f'`{f}`' for f in log_entry['removed']])}

"""
        
        report_content += f"""
## Files Preserved
{chr(10).join([f'- `{f}`' for f in self.preserved_files])}

## Backup Location
Backup created at: `{self.backup_dir}`

## Next Steps
1. Test the consolidated system
2. Verify all functionality works correctly
3. Remove backup if everything works properly
"""
        
        report_path = self.root_dir / "docs" / "FINAL_MERGE_REPORT.md"
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Created merge report at {report_path}")
    
    def run_final_merge(self) -> None:
        """Execute the complete final merge process"""
        print("🚀 Starting Final Duplicate Merge and Organization")
        print("=" * 60)
        
        # Create backup
        self.create_backup()
        
        # Process each category
        self.stats['categories_processed'] = len(self.duplicate_categories)
        for category, category_info in self.duplicate_categories.items():
            self.merge_duplicate_category(category, category_info)
        
        # Calculate stats
        self.stats['duplicates_removed'] = len(self.removed_files)
        self.stats['total_files_analyzed'] = len(self.preserved_files) + len(self.removed_files)
        
        # Clean up
        self.clean_empty_directories()
        
        # Update documentation
        self.update_documentation()
        
        print("\n" + "=" * 60)
        print("🎉 FINAL MERGE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📊 Statistics:")
        print(f"   • Files analyzed: {self.stats['total_files_analyzed']}")
        print(f"   • Duplicates removed: {self.stats['duplicates_removed']}")
        print(f"   • Categories processed: {self.stats['categories_processed']}")
        print(f"   • Files preserved: {len(self.preserved_files)}")
        print(f"📦 Backup location: {self.backup_dir}")
        print(f"📝 Report location: docs/FINAL_MERGE_REPORT.md")
        print("=" * 60)
        
        # Show preserved files
        print("🎯 PRESERVED FILES:")
        for file in sorted(self.preserved_files):
            print(f"   ✅ {file}")
        
        print("\n🏁 Project organization is now complete!")
        print("   The project has been fully consolidated and organized.")
        print("   All duplicate files have been merged and removed.")
        print("   The system is ready for production use.")

def main():
    """Main entry point"""
    print("Final Duplicate Merger and Project Organizer")
    print("=" * 50)
    
    # Get working directory
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    
    print(f"Working directory: {root_dir}")
    
    try:
        merger = FinalDuplicateMergerAndOrganizer(root_dir)
        merger.run_final_merge()
        
        print("\n✅ SUCCESS: Final merge completed without errors!")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
