#!/usr/bin/env python3
"""
Project Organization Verification
================================
Verifies that all consolidated files exist and are accessible.
"""

import os
from pathlib import Path

def verify_organization():
    """Verify that the project organization is complete"""
    
    print("🔍 Verifying Project Organization...")
    print("=" * 50)
    
    project_root = Path.cwd()
    
    # Check consolidated files
    consolidated_files = {
        "AI System": "core/ai_agents/enhanced_ai_system.py",
        "System Coordinator": "core/coordinators/complete_ai_system.py", 
        "Web Dashboard": "interfaces/web/mcp_dashboard.py",
        "Docker Generator": "infrastructure/docker/compose_generator.py",
        "System Repair": "utilities/tools/system_repair.py",
        "DEX Monitor": "integrations/dex/dex_monitor.py"
    }
    
    print("📋 Checking Consolidated Files:")
    all_exist = True
    
    for name, file_path in consolidated_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {name}: {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {name}: {file_path} (MISSING)")
            all_exist = False
    
    print("\n📁 Checking Directory Structure:")
    
    # Check directory structure
    required_dirs = [
        "core/ai_agents",
        "core/coordinators", 
        "core/flash_loan",
        "core/trading",
        "infrastructure/docker",
        "infrastructure/mcp_servers",
        "infrastructure/monitoring",
        "infrastructure/deployment",
        "integrations/dex",
        "integrations/blockchain",
        "integrations/price_feeds",
        "integrations/notifications",
        "interfaces/web",
        "interfaces/api",
        "interfaces/cli",
        "interfaces/bots",
        "utilities/tools",
        "utilities/scripts",
        "utilities/config",
        "utilities/data",
        "tests",
        "docs"
    ]
    
    dirs_exist = True
    for dir_path in required_dirs:
        full_dir = project_root / dir_path
        if full_dir.exists():
            file_count = len(list(full_dir.glob("*")))
            print(f"  ✅ {dir_path}/ ({file_count} items)")
        else:
            print(f"  ❌ {dir_path}/ (MISSING)")
            dirs_exist = False
    
    print("\n🧹 Checking Cleanup Status:")
    
    # Check that duplicate files are gone
    duplicate_files = [
        "enhanced_ai_agents.py",
        "enhanced_ai_agents_v2.py",
        "advanced_ai_agents.py",
        "complete_ai_enhanced_system.py",
        "complete_ai_enhanced_system_fixed.py",
        "complete_ai_enhanced_system_type_safe.py",
        "enhanced_mcp_dashboard_with_chat.py",
        "generate_full_docker_compose.py",
        "generate_full_docker_compose_fixed.py",
        "fix_all_servers.py",
        "fix_all_local_mcp_servers.py",
        "fix_health_check.py",
        "advanced_mcp_server_repair.py",
        "enhanced_dex_arbitrage_monitor_11_tokens.py",
        "enhanced_dex_monitor_final.py",
        "enhanced_dex_calculations_dashboard.py",
        "enhanced_dex_price_calculator.py"
    ]
    
    cleanup_complete = True
    for file_name in duplicate_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"  ⚠️ {file_name} still exists (should be in backup)")
            cleanup_complete = False
        else:
            print(f"  ✅ {file_name} cleaned up")
    
    print("\n" + "=" * 50)
    
    if all_exist and dirs_exist and cleanup_complete:
        print("🎉 Project Organization: COMPLETE ✅")
        print("✅ All consolidated files exist")
        print("✅ Directory structure is correct") 
        print("✅ Duplicate files cleaned up")
    else:
        print("⚠️ Project Organization: INCOMPLETE")
        if not all_exist:
            print("❌ Some consolidated files missing")
        if not dirs_exist:
            print("❌ Some directories missing")
        if not cleanup_complete:
            print("❌ Some duplicate files still present")
    
    print("\n📊 Organization Statistics:")
    
    # Count Python files
    py_files = list(project_root.glob("**/*.py"))
    py_files = [f for f in py_files if not any(part.startswith('.') for part in f.parts)]
    print(f"  📄 Total Python files: {len(py_files)}")
    
    # Count directories
    all_dirs = [d for d in project_root.rglob("*") if d.is_dir()]
    all_dirs = [d for d in all_dirs if not any(part.startswith('.') for part in d.parts)]
    print(f"  📁 Total directories: {len(all_dirs)}")
    
    # Check for backup directories
    backup_dirs = list(project_root.glob("backups/*"))
    print(f"  🛡️ Backup directories: {len(backup_dirs)}")

if __name__ == "__main__":
    verify_organization()
