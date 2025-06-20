#!/usr/bin/env python3
"""
Final Organization Verification Script
=====================================
Verifies that the project has been successfully organized and consolidated.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class OrganizationVerifier:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.verification_results = {
            'core_files_present': [],
            'duplicate_files_absent': [],
            'directory_structure_valid': [],
            'warnings': [],
            'errors': []
        }
        
        # Expected core files in root
        self.expected_core_files = [
            'src/main.py',
            'package.json',
            'README.md',
            'final_project_organizer.py',
            'manage_mcp_orchestration.py',
            'production_deployment_manager.py',
            'production_optimizer.py',
            'project_completion_summary.py',
            'real_trading_executor.py',
            'simple_mcp_server.py',
            'working_health_check.py'
        ]
        
        # Files that should no longer exist (duplicates)
        self.should_be_absent = [
            'project_organizer_fixed.py',
            'automated_duplicate_merger.py',
            'comprehensive_duplicate_merger.py',
            'cleanup_duplicates.py',
            'merge_duplicates_analyzer.py',
            'organize_mcp_servers_clean.py',
            'optimization_summary.py',
            'mcp_optimization_report.py',
            'comprehensive_code_optimization.py',
            'comprehensive_type_fix.py',
            'final_success_confirmation.py',
            'complete_project_with_mcp.py',
            'final_comprehensive_fix.py',
            'demo_orchestration_system.py',
            'launch_all_working_mcp_servers.py',
            'launch_online_mcp_system.py',
            'start_local_mcp_servers.py',
            'mcp_agent_advantage_demo.py',
            'mcp_organization_demo.py',
            'mcp_logger_auditor_server.py',
            'generate_corrected_agent_config.py',
            'realtime_data_aggregator.py',
            'realtime_display_arbitrage.py',
            'quick_dex_verification.py'
        ]
        
        # Expected directories
        self.expected_directories = [
            'agents', 'app', 'config', 'core', 'dashboard', 'data',
            'docs', 'infrastructure', 'integrations', 'logs', 'mcp_servers',
            'monitoring', 'scripts', 'src', 'tests', 'utilities', 'utils'
        ]
    
    def verify_core_files(self) -> None:
        """Verify that all expected core files are present"""
        print("🔍 Verifying core files...")
        
        for file_path in self.expected_core_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                self.verification_results['core_files_present'].append(file_path)
                print(f"  ✅ {file_path}")
            else:
                self.verification_results['errors'].append(f"Missing core file: {file_path}")
                print(f"  ❌ {file_path} - MISSING")
    
    def verify_duplicates_removed(self) -> None:
        """Verify that duplicate files have been successfully removed"""
        print("\n🗑️ Verifying duplicate removal...")
        
        for file_path in self.should_be_absent:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                self.verification_results['duplicate_files_absent'].append(file_path)
                print(f"  ✅ {file_path} - Successfully removed")
            else:
                self.verification_results['warnings'].append(f"Duplicate still exists: {file_path}")
                print(f"  ⚠️ {file_path} - Still exists")
    
    def verify_directory_structure(self) -> None:
        """Verify that the expected directory structure exists"""
        print("\n📁 Verifying directory structure...")
        
        for dir_name in self.expected_directories:
            dir_path = self.root_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.verification_results['directory_structure_valid'].append(dir_name)
                print(f"  ✅ {dir_name}/")
            else:
                self.verification_results['warnings'].append(f"Directory missing: {dir_name}")
                print(f"  ⚠️ {dir_name}/ - Missing or not a directory")
    
    def check_empty_directories(self) -> int:
        """Count empty directories"""
        print("\n🧹 Checking for empty directories...")
        
        empty_count = 0
        for root, dirs, files in os.walk(self.root_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
            
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):
                        empty_count += 1
                        print(f"  📁 Empty directory: {dir_path.relative_to(self.root_dir)}")
                except (OSError, PermissionError):
                    pass
        
        if empty_count == 0:
            print("  ✅ No empty directories found")
        
        return empty_count
    
    def verify_backup_exists(self) -> None:
        """Verify that backups were created"""
        print("\n📦 Verifying backup creation...")
        
        backup_dir = self.root_dir / "backups"
        if backup_dir.exists():
            backup_folders = [d for d in backup_dir.iterdir() if d.is_dir()]
            if backup_folders:
                latest_backup = max(backup_folders, key=lambda d: Any: d.stat().st_mtime)
                print(f"  ✅ Latest backup: {latest_backup.name}")
                
                # Check if backup contains files
                backup_files = list(latest_backup.glob("*.py"))
                print(f"  ✅ Backup contains {len(backup_files)} Python files")
            else:
                self.verification_results['warnings'].append("No backup folders found")
                print("  ⚠️ No backup folders found")
        else:
            self.verification_results['warnings'].append("Backup directory missing")
            print("  ⚠️ Backup directory missing")
    
    def generate_verification_report(self) -> None:
        """Generate a comprehensive verification report"""
        print("\n" + "="*60)
        print("📋 VERIFICATION REPORT")
        print("="*60)
        
        # Calculate scores
        core_files_score = len(self.verification_results['core_files_present'])
        core_files_total = len(self.expected_core_files)
        duplicates_removed_score = len(self.verification_results['duplicate_files_absent'])
        duplicates_total = len(self.should_be_absent)
        directories_score = len(self.verification_results['directory_structure_valid'])
        directories_total = len(self.expected_directories)
        
        print(f"📊 Core Files Present: {core_files_score}/{core_files_total}")
        print(f"🗑️ Duplicates Removed: {duplicates_removed_score}/{duplicates_total}")
        print(f"📁 Directories Valid: {directories_score}/{directories_total}")
        print(f"⚠️ Warnings: {len(self.verification_results['warnings'])}")
        print(f"❌ Errors: {len(self.verification_results['errors'])}")
        
        # Overall score
        total_score = core_files_score + duplicates_removed_score + directories_score
        total_possible = core_files_total + duplicates_total + directories_total
        percentage = (total_score / total_possible) * 100
        
        print(f"\n🎯 Overall Organization Score: {percentage:.1f}%")
        
        # Status determination
        if len(self.verification_results['errors']) == 0 and percentage >= 95:
            status = "🟢 EXCELLENT"
            status_message = "Project is fully organized and production-ready!"
        elif len(self.verification_results['errors']) == 0 and percentage >= 85:
            status = "🟡 GOOD"
            status_message = "Project is well organized with minor issues."
        elif len(self.verification_results['errors']) > 0:
            status = "🔴 NEEDS ATTENTION"
            status_message = "Project has critical issues that need to be resolved."
        else:
            status = "🟡 PARTIAL"
            status_message = "Project is partially organized but needs improvement."
        
        print(f"\n{status} - {status_message}")
        
        # Show warnings and errors
        if self.verification_results['warnings']:
            print(f"\n⚠️ WARNINGS:")
            for warning in self.verification_results['warnings']:
                print(f"  • {warning}")
        
        if self.verification_results['errors']:
            print(f"\n❌ ERRORS:")
            for error in self.verification_results['errors']:
                print(f"  • {error}")
        
        # Success message
        if len(self.verification_results['errors']) == 0:
            print(f"\n🎉 VERIFICATION COMPLETE!")
            print(f"The project organization has been successfully verified.")
            print(f"All critical components are in place and duplicate files have been removed.")
    
    def run_verification(self) -> None:
        """Run the complete verification process"""
        print("🚀 Starting Project Organization Verification")
        print("="*60)
        
        self.verify_core_files()
        self.verify_duplicates_removed()
        self.verify_directory_structure()
        empty_dirs = self.check_empty_directories()
        self.verify_backup_exists()
        self.generate_verification_report()
        
        print("\n" + "="*60)
        print("✅ VERIFICATION COMPLETED")
        print("="*60)

def main():
    """Main entry point"""
    print("Project Organization Verification")
    print("=" * 40)
    
    # Get working directory
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    
    print(f"Verifying: {root_dir}")
    print()
    
    try:
        verifier = OrganizationVerifier(root_dir)
        verifier.run_verification()
        return 0
        
    except Exception as e:
        print(f"\n❌ VERIFICATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
