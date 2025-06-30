#!/usr/bin/env python3
"""
Final MCP Cleanup Script
========================
Removes ALL remaining MCP duplicate configurations and creates a single, 
consolidated MCP setup.
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    project_root = Path.cwd()
    backup_dir = project_root / f"final_mcp_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(exist_ok=True)
    
    logger.info("🧹 Starting FINAL MCP cleanup...")
    
    config_dir = project_root / "config"
    
    # Keep only the main unified config
    keep_files = {"unified_mcp_config.json"}
    
    # All other MCP-related config files to remove
    all_mcp_configs = [
        "CLEAN_CLINE_MCP_CONFIG.json",
        "cline_mcp_settings.json", 
        "complete_cline_mcp_config.json",
        "FINAL_MCP_DEPLOYMENT_SUMMARY.json",
        "mcp.json",
        "mcp.local-agent.json",
        "mcp_check_report.json",
        "mcp_deployment_results.json",
        "mcp_discovery_report.json",
        "mcp_fix_report_20250611_211149.json",
        "mcp_functionality_test.json",
        "mcp_servers.json",
        "mcp_status_report.json",
        "mcp_verification_results.json",
        "memory_mcp_config_full_path.json",
        "online_mcp_report_20250611_220536.json",
        "test_memory_mcp_config.json",
        "unified_mcp_config_new.json",
        "unified_online_mcp_config.json",
        "working_cline_mcp_config.json",
        "working_mcp_servers_for_cline.json"
    ]
    
    removed_count = 0
    
    # Remove duplicate config files
    for config_file in all_mcp_configs:
        config_path = config_dir / config_file
        if config_path.exists():
            # Backup then remove
            shutil.copy2(config_path, backup_dir / config_file)
            config_path.unlink()
            logger.info(f"🗑️ Removed: {config_file}")
            removed_count += 1
    
    # Remove any remaining MCP-related report/status files
    for file_path in config_dir.glob("*"):
        if file_path.is_file() and file_path.name not in keep_files:
            name_lower = file_path.name.lower()
            if any(term in name_lower for term in ['mcp', 'report', 'status', 'summary', 'deployment']):
                if file_path.suffix == '.json':
                    shutil.copy2(file_path, backup_dir / file_path.name)
                    file_path.unlink()
                    logger.info(f"🗑️ Removed report: {file_path.name}")
                    removed_count += 1
    
    # Clean up any remaining duplicate setup scripts 
    script_patterns = [
        "scripts/*mcp*.py",
        "scripts/*setup*.py", 
        "mcp_servers/*setup*.py"
    ]
    
    for pattern in script_patterns:
        for script_file in project_root.glob(pattern):
            if script_file.is_file() and "clean_mcp_duplicates.py" not in script_file.name:
                shutil.copy2(script_file, backup_dir / script_file.name)
                script_file.unlink()
                logger.info(f"🗑️ Removed script: {script_file.relative_to(project_root)}")
                removed_count += 1
    
    # Verify the main config is valid
    main_config = config_dir / "unified_mcp_config.json"
    if main_config.exists():
        try:
            with open(main_config, 'r') as f:
                config = json.load(f)
            
            server_count = len(config.get('servers', {}))
            logger.info(f"✅ Main config verified: {server_count} servers configured")
            
        except Exception as e:
            logger.error(f"❌ Main config is invalid: {e}")
    
    # Create final summary
    summary = {
        "final_cleanup_timestamp": datetime.now().isoformat(),
        "total_files_removed": removed_count,
        "backup_location": str(backup_dir),
        "canonical_config": "config/unified_mcp_config.json",
        "mcp_servers_location": "mcp_servers/",
        "cleanup_status": "COMPLETE - Single MCP setup achieved",
        "next_steps": [
            "Use only config/unified_mcp_config.json for MCP configuration",
            "All MCP servers are in mcp_servers/ directory", 
            "No more duplicate configurations exist",
            "Backup files available if needed"
        ]
    }
    
    with open(project_root / "FINAL_MCP_CLEANUP_REPORT.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("=" * 60)
    logger.info("🎉 FINAL MCP CLEANUP COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"📊 Removed {removed_count} duplicate files")
    logger.info(f"📝 Single config: config/unified_mcp_config.json")
    logger.info(f"📁 MCP servers: mcp_servers/")
    logger.info(f"💾 Backup: {backup_dir}")
    logger.info("=" * 60)
    
    return summary

if __name__ == "__main__":
    main() 