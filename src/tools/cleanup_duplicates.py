#!/usr/bin/env python3
"""
Cleanup Duplicates Script
========================

Remove duplicate files and directories after consolidation.
"""

import shutil
import logging
import sys
from pathlib import Path
from datetime import datetime

# Set up logging with proper encoding handling
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Ensure stdout uses UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    try:
        # Use getattr to avoid type checking issues
        reconfigure = getattr(sys.stdout, 'reconfigure', None)
        if reconfigure:
            reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fallback for systems that don't support reconfigure

logger = logging.getLogger("CleanupDuplicates")

class DuplicateCleanup:
    """Clean up duplicate files and directories"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
        # Directories to remove (duplicates)
        self.dirs_to_remove = [
            "mcp_servers_organized",
            "mcp_server",
            "infrastructure/mcp_servers",
            "backups/comprehensive_merge_20250613_093523",
            "backups/pre_organization_20250613_093725",
            "backups/final_merge_20250613_094444",
            "archive/deprecated/old_mcp_servers",
            "archive/backup_20250603_122623"
        ]
        
        # Files to remove (duplicates in root)
        self.files_to_remove = [
            "simple_mcp_server.py",
            "minimal-mcp-server.py"
        ]

    def cleanup_directories(self) -> None:
        """Remove duplicate directories"""
        logger.info("🧹 Cleaning up duplicate directories...")
        
        for dir_path in self.dirs_to_remove:
            full_path = self.project_root / dir_path
            if full_path.exists():
                try:
                    shutil.rmtree(full_path)
                    logger.info(f"   ✅ Removed: {dir_path}")
                except Exception as e:
                    logger.error(f"   ❌ Failed to remove {dir_path}: {e}")

    def cleanup_files(self) -> None:
        """Remove duplicate files"""
        logger.info("🧹 Cleaning up duplicate files...")
        
        for file_path in self.files_to_remove:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    full_path.unlink()
                    logger.info(f"   ✅ Removed: {file_path}")
                except Exception as e:
                    logger.error(f"   ❌ Failed to remove {file_path}: {e}")

    def create_summary_report(self) -> None:
        """Create a summary of cleanup actions"""
        report_path = self.project_root / "CLEANUP_SUMMARY.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Duplicate Cleanup Summary\n\n")
            f.write(f"Date: {datetime.now().isoformat()}\n\n")
            f.write("## Consolidation Actions\n\n")
            f.write("### Merged Files\n")
            f.write("- Multiple MCP servers → `working_flash_loan_mcp.py`\n")
            f.write("- Multiple launchers → `scripts/unified_project_launcher.py`\n")
            f.write("- Multiple health checks → `utils/unified_health_check.py`\n\n")
            f.write("### Removed Directories\n")
            for dir_path in self.dirs_to_remove:
                f.write(f"- {dir_path}\n")
            f.write("\n### Removed Files\n")
            for file_path in self.files_to_remove:
                f.write(f"- {file_path}\n")
            f.write("\n## Result\n")
            f.write("- Reduced project complexity\n")
            f.write("- Eliminated duplicate functionality\n")
            f.write("- Centralized configuration\n")
            f.write("- Improved maintainability\n")

def main():
    """Main cleanup function"""
    cleanup = DuplicateCleanup()
    
    logger.info("🚀 Starting duplicate cleanup process...")
    
    try:
        cleanup.cleanup_directories()
        cleanup.cleanup_files()
        cleanup.create_summary_report()
        
        logger.info("✅ Cleanup completed successfully!")
        logger.info("📄 Summary report created: CLEANUP_SUMMARY.md")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    sys.exit(main())
if __name__ == "__main__":
    sys.exit(main())
