#!/usr/bin/env python3
"""
Enhanced Duplicate Script Cleanup Tool
=====================================

This script identifies and consolidates duplicate scripts in the flash loan project,
removing unnecessary files and merging similar functionality.
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

class EnhancedDuplicateCleanup:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.duplicates_found = {}
        self.files_to_remove = []
        self.files_to_keep = []
        self.consolidation_plan = {}
        self.cleanup_log = []
        
    def analyze_duplicates(self) -> Dict:
        """Analyze the project for duplicate scripts"""
        print("🔍 Analyzing project for duplicate scripts...")
        
        # Build comprehensive consolidation plan
        self.consolidation_plan = {
            "Additional Foundry MCP Servers": {
                "keep": "foundry-mcp-server/working_enhanced_foundry_mcp_server.py",
                "remove": [
                    "foundry-mcp-server/enhanced_arbitrage_server.py",
                    "foundry-mcp-server/enhanced_production_mcp_server.py"
                ],
                "reason": "Consolidate to single working enhanced foundry server"
            },
            
            "Dashboard Scripts": {
                "keep": "enhanced_mcp_dashboard_with_chat.py",
                "remove": [
                    "mcp_dashboard.py"
                ],
                "reason": "Keep the enhanced dashboard with chat functionality"
            },
            
            "Test Scripts - Additional": {
                "keep": "test_enhanced_mcp_integration.py", 
                "remove": [
                    "test_event_loop_fix.py",
                    "test_production_live.py",
                    "simple_mcp_test.py",
                    "test_cleaned_servers.py"
                ],
                "reason": "Keep only the comprehensive integration test"
            },
            
            "Old Log Files": {
                "keep": None,
                "remove": [
                    "revenue_bot.log",
                    "web3_revenue_bot.log",
                    "launcher.log"
                ],
                "reason": "Remove old log files from yesterday"
            },
            
            "Backup Directories": {
                "keep": "backup_before_cleanup_20250605_161424",
                "remove": [
                    "archive",
                    "archive_cleanup_20250604",
                    "deprecated"
                ],
                "reason": "Keep only the most recent backup, remove old archives"
            },
            
            "Config Directories": {
                "keep": "config",
                "remove": [
                    "configuration"
                ],
                "reason": "Consolidate configuration in single config directory"
            },
            
            "Launcher Scripts": {
                "keep": "FINAL_LAUNCHER.py",
                "remove": [
                    "quick_start.py"
                ],
                "reason": "FINAL_LAUNCHER is the main entry point"
            },
            
            "Monitoring Scripts": {
                "keep": "monitoring",
                "remove": [],
                "reason": "Keep monitoring directory organized"
            },
            
            "Production/Scripts Directories": {
                "keep": None,
                "remove": [
                    "production",
                    "scripts",
                    "scripts_active"
                ],
                "reason": "These appear to be empty or deprecated directories"
            }
        }
        
        return self.consolidation_plan
    
    def identify_cache_and_temp_files(self) -> List[str]:
        """Identify cache and temporary files"""
        patterns_to_remove = [
            "**/__pycache__",
            "**/.pytest_cache",
            "**/node_modules",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.tmp",
            "**/*.temp",
            "**/*~",
            "**/*.bak",
            "**/.DS_Store",
            "**/Thumbs.db"
        ]
        
        files_to_remove = []
        for pattern in patterns_to_remove:
            for path in self.base_path.glob(pattern):
                if path.exists():
                    files_to_remove.append(str(path.relative_to(self.base_path)))
        
        return files_to_remove
    
    def create_backup(self) -> str:
        """Create a backup before cleanup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.base_path / f"backup_before_cleanup_{timestamp}"
        
        print(f"📦 Creating backup at: {backup_dir}")
        
        files_to_backup = []
        for category, plan in self.consolidation_plan.items():
            if plan.get('remove'):
                files_to_backup.extend(plan.get('remove', []))
        
        # Create backup directory
        backup_dir.mkdir(exist_ok=True)
        
        # Backup files that will be removed
        backed_up = 0
        for file_path in files_to_backup:
            source = self.base_path / file_path
            if source.exists():
                dest = backup_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if source.is_file():
                        shutil.copy2(source, dest)
                        backed_up += 1
                    elif source.is_dir():
                        shutil.copytree(source, dest)
                        backed_up += 1
                    print(f"  ✓ Backed up: {file_path}")
                except Exception as e:
                    print(f"  ❌ Failed to backup {file_path}: {e}")
        
        print(f"  ✓ Total items backed up: {backed_up}")
        return str(backup_dir)
    
    def execute_cleanup(self, create_backup: bool = True) -> Dict:
        """Execute the cleanup plan"""
        if create_backup:
            backup_path = self.create_backup()
            print(f"✅ Backup created at: {backup_path}")
        
        cleanup_results = {
            "files_removed": 0,
            "dirs_removed": 0,
            "files_kept": 0,
            "categories_processed": 0,
            "errors": []
        }
        
        print("\n🧹 Executing cleanup plan...")
        
        # Process each category
        for category, plan in self.consolidation_plan.items():
            print(f"\n📂 Processing: {category}")
            if plan['keep']:
                print(f"   Keep: {plan['keep']}")
            print(f"   Reason: {plan['reason']}")
            
            # Check if file to keep exists (if specified)
            if plan['keep']:
                keep_path = self.base_path / plan['keep']
                if keep_path.exists():
                    cleanup_results["files_kept"] += 1
                else:
                    print(f"   ⚠️  File/directory to keep doesn't exist: {plan['keep']}")
            
            # Remove duplicate files
            for item_to_remove in plan.get('remove', []):
                item_path = self.base_path / item_to_remove
                if item_path.exists():
                    try:
                        if item_path.is_file():
                            item_path.unlink()
                            print(f"   🗑️  Removed file: {item_to_remove}")
                            cleanup_results["files_removed"] += 1
                        elif item_path.is_dir():
                            shutil.rmtree(item_path)
                            print(f"   🗑️  Removed directory: {item_to_remove}")
                            cleanup_results["dirs_removed"] += 1
                    except Exception as e:
                        error_msg = f"Error removing {item_to_remove}: {str(e)}"
                        print(f"   ❌ {error_msg}")
                        cleanup_results["errors"].append(error_msg)
                else:
                    print(f"   ⚠️  Already removed: {item_to_remove}")
            
            cleanup_results["categories_processed"] += 1
        
        # Remove cache and temporary files
        print("\n🧹 Removing cache and temporary files...")
        cache_files = self.identify_cache_and_temp_files()
        for file_path in cache_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    if full_path.is_file():
                        full_path.unlink()
                        print(f"   🗑️  Removed: {file_path}")
                        cleanup_results["files_removed"] += 1
                    elif full_path.is_dir():
                        shutil.rmtree(full_path)
                        print(f"   🗑️  Removed directory: {file_path}")
                        cleanup_results["dirs_removed"] += 1
                except Exception as e:
                    error_msg = f"Error removing {file_path}: {str(e)}"
                    print(f"   ❌ {error_msg}")
                    cleanup_results["errors"].append(error_msg)
        
        return cleanup_results
    
    def generate_report(self, results: Dict) -> str:
        """Generate a cleanup report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# Enhanced Duplicate Script Cleanup Report
Generated: {timestamp}

## Summary
- Categories processed: {results['categories_processed']}
- Files removed: {results['files_removed']}
- Directories removed: {results['dirs_removed']}
- Files kept: {results['files_kept']}
- Errors encountered: {len(results['errors'])}

## Consolidation Plan Executed
"""
        
        for category, plan in self.consolidation_plan.items():
            report += f"""
### {category}
- **Keep:** `{plan['keep'] if plan['keep'] else 'N/A'}`
- **Reason:** {plan['reason']}
- **Removed:** {len(plan.get('remove', []))} items
"""
            for removed_item in plan.get('remove', []):
                report += f"  - `{removed_item}`\n"
        
        if results['errors']:
            report += "\n## Errors\n"
            for error in results['errors']:
                report += f"- {error}\n"
        
        report += """
## Final Project Structure

### Core MCP Servers:
1. **Copilot MCP Server:** `core/working_enhanced_copilot_mcp_server.py`
2. **Foundry MCP Server:** `foundry-mcp-server/working_enhanced_foundry_mcp_server.py`
3. **Unified MCP Server:** `mcp/working_unified_flash_loan_mcp_server.py`
4. **Production Server:** `enhanced_production_mcp_server_v2.py`

### Key Entry Points:
1. **Main Launcher:** `FINAL_LAUNCHER.py`
2. **Dashboard:** `enhanced_mcp_dashboard_with_chat.py`
3. **Test Suite:** `test_enhanced_mcp_integration.py`

### Configuration:
- **Config Directory:** `config/`
- **Environment Example:** `.env.example`

### Project Organization:
- **Core Logic:** `core/`
- **MCP Servers:** `mcp/`, `foundry-mcp-server/`
- **Monitoring:** `monitoring/`
- **Dashboard:** `dashboard/`
- **Templates:** `templates/`
- **Data:** `data/`
- **Utilities:** `utils/`

### Next Steps:
1. Run `test_enhanced_mcp_integration.py` to verify all systems work
2. Use `FINAL_LAUNCHER.py` to start the system
3. Access dashboard via `enhanced_mcp_dashboard_with_chat.py`
4. Monitor system health in `monitoring/` directory
"""
        
        return report

def main():
    """Main execution function"""
    print("🚀 Starting Enhanced Duplicate Script Cleanup")
    print("=" * 50)
    
    cleanup = EnhancedDuplicateCleanup()
    
    # Analyze duplicates
    plan = cleanup.analyze_duplicates()
    print(f"📊 Found {len(plan)} categories to process")
    
    # Show plan summary
    print("\n📋 Cleanup Plan Summary:")
    total_to_remove = 0
    for category, details in plan.items():
        count = len(details.get('remove', []))
        total_to_remove += count
        print(f"  {category}: Remove {count} items")
    
    print(f"\n📊 Total items to remove: {total_to_remove}")
    
    # Ask for confirmation
    response = input("\n❓ Proceed with cleanup? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cleanup cancelled")
        return
    
    # Execute cleanup
    results = cleanup.execute_cleanup(create_backup=True)
    
    # Generate report
    report = cleanup.generate_report(results)
    
    # Save report
    report_file = Path("enhanced_cleanup_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Cleanup completed!")
    print(f"📄 Report saved to: {report_file}")
    print(f"📊 Summary: {results['files_removed']} files and {results['dirs_removed']} directories removed")
    
    if results['errors']:
        print(f"⚠️  {len(results['errors'])} errors occurred - check the report for details")

if __name__ == "__main__":
    main()
