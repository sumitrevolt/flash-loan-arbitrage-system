#!/usr/bin/env python3
"""
GitHub Copilot Tool Limit Fix
Resolves the "more than 128 tools" error by optimizing MCP server configuration
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, TypedDict

class SummaryResult(TypedDict):
    optimization_timestamp: str
    tool_limit: int
    optimization_strategy: str
    essential_servers: List[str]
    disabled_servers: List[str]
    recommendations: List[str]

class AnalysisResult(TypedDict):
    local_mcp_servers: int
    vscode_mcp_servers: int
    estimated_tools_per_server: int
    total_estimated_tools: int
    exceeds_limit: bool
    recommendations: List[str]

class GitHubCopilotToolLimitFixer:
    def __init__(self):
        self.max_tools = 128
        self.config_file = "unified_mcp_config.json"
        self.vscode_settings = Path.home() / "AppData/Roaming/Code/User/settings.json"
        self.backup_dir = Path("backups/mcp_configs")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self):
        """Create backup of current configurations"""
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup unified config
        if os.path.exists(self.config_file):
            backup_unified = self.backup_dir / f"unified_mcp_config_backup_{timestamp}.json"
            shutil.copy2(self.config_file, backup_unified)
            print(f"✅ Backed up unified config to: {backup_unified}")
        
        # Backup VSCode settings
        if self.vscode_settings.exists():
            backup_vscode = self.backup_dir / f"vscode_settings_backup_{timestamp}.json"
            shutil.copy2(self.vscode_settings, backup_vscode)
            print(f"✅ Backed up VSCode settings to: {backup_vscode}")
    
    def analyze_tool_count(self) -> AnalysisResult:
        """Analyze current tool configuration and count potential tools"""
        analysis: AnalysisResult = {
            "local_mcp_servers": 0,
            "vscode_mcp_servers": 0,
            "estimated_tools_per_server": 5,  # Conservative estimate
            "total_estimated_tools": 0,
            "exceeds_limit": False,
            "recommendations": []
        }
        
        # Count local MCP servers
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config: Dict[str, Any] = json.load(f)
                enabled_servers = sum(1 for server in config.get("servers", {}).values() 
                                    if server.get("enabled", True))
                analysis["local_mcp_servers"] = enabled_servers
        
        # Count VSCode MCP servers
        if self.vscode_settings.exists():
            with open(self.vscode_settings, 'r', encoding='utf-8') as f:
                vscode_config: Dict[str, Any] = json.load(f)
                mcp_servers = vscode_config.get("mcp", {}).get("servers", {})
                analysis["vscode_mcp_servers"] = len(mcp_servers)
          # Calculate estimated total tools
        total_servers = analysis["local_mcp_servers"] + analysis["vscode_mcp_servers"]
        analysis["total_estimated_tools"] = total_servers * analysis["estimated_tools_per_server"]
        analysis["exceeds_limit"] = analysis["total_estimated_tools"] > self.max_tools
        
        return analysis
    
    def get_essential_servers(self) -> List[str]:
        """Define essential MCP servers to keep enabled"""
        return [
            "mcp_github_copilot_server",
            "unified_mcp_coordinator", 
            "mcp_arbitrage_server",
            "mcp_flash_loan_server",
            "mcp_price_feed_server",
            "mcp_risk_manager_server"
        ]
    
    def get_redundant_servers(self) -> List[str]:
        """Identify redundant or duplicate MCP servers"""
        return [
            # Status check duplicates
            "check-mcp-status",
            "check_mcp_status", 
            "mcp_status_check",
            "quick_mcp_check",
            "mcp-health-check",
            "mcp-stability-report",
            
            # Coordinator duplicates
            "mcp_coordinator_server",
            "mcp_enhanced_coordinator",
            "online_mcp_coordinator",
            "simple_mcp_orchestrator",
            "simplified_mcp_coordinator_fixed",
            "unified_mcp_coordinator_20250617_143120",
            
            # Manager duplicates
            "mcp_server_manager",
            "enhanced_mcp_server_manager",
            "unified_mcp_manager",
            "unified_mcp_integration_manager",
            "unified_mcp_orchestration_manager",
            
            # Template/test duplicates
            "mcp_server_template",
            "working_mcp_server_template",
            "minimal-mcp-server",
            "simple_mcp_server",
            "mcp_connection_test",
            "mcp_dependency_test",
            
            # Dashboard duplicates
            "mcp_dashboard",
            "enhanced_mcp_dashboard_with_chat",
            "dashboard_enhanced_mcp_dashboard_with_chat",
            
            # Flash loan duplicates  
            "flash_loan_mcp_mcp_server",
            "working_flash_loan_mcp",
            "aave_flash_loan_mcp_server",
            
            # Project organizer duplicates
            "mcp_project_organizer",
            "mcp_project_organizer_fixed",
            "organize_mcp_servers",
            
            # Utility duplicates
            "fix_all_local_mcp_servers",
            "start_mcp_servers",
            "mcp_simple_startup",
            "autodiscover_mcp_agents",
            "identify_mcp_servers"
        ]
    
    def optimize_local_config(self):
        """Optimize local MCP server configuration"""
        if not os.path.exists(self.config_file):
            print("❌ Unified MCP config not found")
            return
        
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        essential_servers = self.get_essential_servers()
        redundant_servers = self.get_redundant_servers()
        
        disabled_count = 0
        kept_count = 0
        
        for server_name, server_config in config.get("servers", {}).items():
            if server_name in essential_servers:
                server_config["enabled"] = True
                kept_count += 1
                print(f"✅ Keeping essential server: {server_name}")
            elif server_name in redundant_servers:
                server_config["enabled"] = False
                disabled_count += 1
                print(f"🔴 Disabling redundant server: {server_name}")
            else:
                # Disable all other servers to stay within limit
                server_config["enabled"] = False
                disabled_count += 1
                print(f"🟡 Disabling additional server: {server_name}")
        
        # Write optimized config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n📊 Local MCP Optimization Results:")
        print(f"   Essential servers kept: {kept_count}")
        print(f"   Redundant servers disabled: {disabled_count}")
    
    def optimize_vscode_config(self):
        """Optimize VSCode MCP server configuration"""
        if not self.vscode_settings.exists():
            print("❌ VSCode settings not found")
            return
        
        with open(self.vscode_settings, 'r', encoding='utf-8') as f:
            vscode_config = json.load(f)
        
        mcp_servers = vscode_config.get("mcp", {}).get("servers", {})
        
        # Keep only essential VSCode MCP servers
        essential_vscode_servers = {
            "github": mcp_servers.get("github"),
            "context7": mcp_servers.get("context7"),
            "filesystem": mcp_servers.get("filesystem")
        }
        
        # Remove None values
        essential_vscode_servers = {k: v for k, v in essential_vscode_servers.items() if v is not None}
        
        # Update VSCode config
        if "mcp" not in vscode_config:
            vscode_config["mcp"] = {}
        
        original_count = len(mcp_servers)
        vscode_config["mcp"]["servers"] = essential_vscode_servers
          # Write optimized VSCode config
        with open(self.vscode_settings, 'w', encoding='utf-8') as f:
            json.dump(vscode_config, f, indent=4)
        
        print(f"\n📊 VSCode MCP Optimization Results:")
        print(f"   Original servers: {original_count}")
        print(f"   Essential servers kept: {len(essential_vscode_servers)}")
        print(f"   Servers removed: {original_count - len(essential_vscode_servers)}")
    
    def create_optimized_config_summary(self):
        """Create summary of optimized configuration"""
        summary: SummaryResult = {
            "optimization_timestamp": __import__('datetime').datetime.now().isoformat(),
            "tool_limit": self.max_tools,
            "optimization_strategy": "Keep essential servers, disable redundant ones",
            "essential_servers": self.get_essential_servers(),
            "disabled_servers": self.get_redundant_servers(),
            "recommendations": [
                "Restart VSCode after optimization",
                "Test GitHub Copilot functionality",
                "Monitor for any missing functionality",
                "Re-enable specific servers if needed"
            ]
        }
        
        with open("github_copilot_optimization_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📋 Optimization summary saved to: github_copilot_optimization_summary.json")
    
    def fix_tool_limit_issue(self):
        """Main method to fix GitHub Copilot tool limit issue"""
        print("🔧 GitHub Copilot Tool Limit Fix")
        print("=" * 50)
        
        # Step 1: Create backups
        print("\n1️⃣ Creating configuration backups...")
        self.create_backup()
        
        # Step 2: Analyze current configuration
        print("\n2️⃣ Analyzing current tool configuration...")
        analysis = self.analyze_tool_count()
        
        print(f"   Local MCP servers: {analysis['local_mcp_servers']}")
        print(f"   VSCode MCP servers: {analysis['vscode_mcp_servers']}")
        print(f"   Estimated total tools: {analysis['total_estimated_tools']}")
        print(f"   Exceeds limit ({self.max_tools}): {'❌ YES' if analysis['exceeds_limit'] else '✅ NO'}")
        
        if not analysis['exceeds_limit']:
            print("\n✅ Current configuration is within limits!")
            return
        
        # Step 3: Optimize local MCP configuration
        print("\n3️⃣ Optimizing local MCP server configuration...")
        self.optimize_local_config()
        
        # Step 4: Optimize VSCode MCP configuration  
        print("\n4️⃣ Optimizing VSCode MCP server configuration...")
        self.optimize_vscode_config()
        
        # Step 5: Create summary
        print("\n5️⃣ Creating optimization summary...")
        self.create_optimized_config_summary()
        
        print("\n🎉 GitHub Copilot Tool Limit Fix Complete!")
        print("\n📝 Next Steps:")
        print("   1. Restart VSCode completely")
        print("   2. Test GitHub Copilot functionality")
        print("   3. Check if the '128 tools' error is resolved")
        print("   4. Re-enable specific servers if needed functionality is missing")
        
        # Final analysis
        print("\n📊 Final Analysis:")
        final_analysis = self.analyze_tool_count()
        print(f"   Estimated tools after optimization: {final_analysis['total_estimated_tools']}")
        print(f"   Within limits: {'✅ YES' if not final_analysis['exceeds_limit'] else '❌ NO'}")

def main():
    """Main execution function"""
    try:
        fixer = GitHubCopilotToolLimitFixer()
        fixer.fix_tool_limit_issue()
        
    except Exception as e:
        print(f"❌ Error during optimization: {str(e)}")
        print("📋 Please check the backup files and restore if needed")
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
