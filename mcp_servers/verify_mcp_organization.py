#!/usr/bin/env python3
"""
MCP Server Organization Verification Script
Verifies that all MCP servers have been properly organized into the structured folder system.
"""

import os
from pathlib import Path
from typing import Dict, List

def verify_mcp_organization():
    """Verify the MCP server organization structure"""
    base_path = Path("C:/Users/Ratanshila/Documents/flash loan")
    mcp_servers_path = base_path / "mcp_servers"
    
    print("🔍 MCP Server Organization Verification")
    print("=" * 50)
    
    # Expected structure
    expected_structure = {
        "orchestration": [
            "mcp_master_coordinator_server.py"
        ],
        "market_analysis": [
            "mcp_token_scanner_server.py",
            "mcp_arbitrage_detector_server.py", 
            "mcp_sentiment_monitor_server.py"
        ],
        "execution": [
            "mcp_flash_loan_strategist_server.py",
            "mcp_contract_executor_server.py",
            "mcp_transaction_optimizer_server.py",
            "working_unified_flash_loan_mcp_server.py",
            "flash-loan-arbitrage-mcp/"
        ],
        "risk_management": [
            "mcp_risk_manager_server.py",
            "mcp_logger_auditor_server.py",
            "risk-management-mcp-server/"
        ],
        "ui": [
            "mcp_dashboard_server.py"
        ],
        "blockchain_integration": [
            "evm_mcp_server.py",
            "matic_mcp_server.py",
            "evm-mcp-server/",
            "matic-mcp-server/"
        ],
        "data_providers": [
            "price_oracle_mcp_server.py",
            "price-oracle-mcp-server/"
        ],
        "ai_integration": [
            "context7_mcp_server.py",
            "context7-mcp-server/"
        ],
        "task_management": [
            "mcp-taskmanager/"
        ]
    }
    
    # Check if base structure exists
    if not mcp_servers_path.exists():
        print("❌ ERROR: mcp_servers directory not found!")
        return False
    
    print(f"✅ Base directory found: {mcp_servers_path}")
    print()
    
    # Verify each category
    all_good = True
    total_files = 0
    found_files = 0
    
    for category, expected_files in expected_structure.items():
        category_path = mcp_servers_path / category
        print(f"📂 Checking {category}/")
        
        if not category_path.exists():
            print(f"   ❌ Directory missing: {category}")
            all_good = False
            continue
        
        # List actual files in directory
        actual_files = []
        for item in category_path.iterdir():
            actual_files.append(item.name)
        
        # Check each expected file
        for expected_file in expected_files:
            total_files += 1
            if expected_file in actual_files:
                print(f"   ✅ {expected_file}")
                found_files += 1
            else:
                print(f"   ❌ MISSING: {expected_file}")
                all_good = False
        
        # Show any unexpected files
        unexpected = set(actual_files) - set(expected_files)
        for unexpected_file in unexpected:
            print(f"   ℹ️  EXTRA: {unexpected_file}")
        
        print()
    
    # Check for shared infrastructure files
    print("🔧 Checking shared infrastructure:")
    shared_files = [
        "mcp_shared_utilities.py",
        "mcp_unified_config.py", 
        "mcp_enhanced_coordinator.py",
        "mcp_server_template.py"
    ]
    
    for shared_file in shared_files:
        if (base_path / shared_file).exists():
            print(f"   ✅ {shared_file}")
        else:
            print(f"   ❌ MISSING: {shared_file}")
            all_good = False
    
    print()
    
    # Summary
    print("📊 Summary:")
    print(f"   Total expected files: {total_files}")
    print(f"   Files found: {found_files}")
    print(f"   Success rate: {(found_files/total_files)*100:.1f}%")
    
    if all_good:
        print("\n🎉 SUCCESS: All MCP servers properly organized!")
    else:
        print("\n⚠️  WARNING: Some files missing or misplaced")
    
    return all_good

if __name__ == "__main__":
    verify_mcp_organization()
