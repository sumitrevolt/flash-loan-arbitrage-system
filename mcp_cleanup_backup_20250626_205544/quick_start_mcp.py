#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start MCP Management System
Interactive interface for managing all MCP servers, Cursor integration, and SAMR agents
"""

from pathlib import Path
import subprocess
import sys

import yaml

class MCPQuickStart:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.mcp_dir = self.base_dir / "mcp_management"
        self.scripts_dir = self.mcp_dir / "scripts"
        self.config_dir = self.mcp_dir / "config"
        
    def show_menu(self):
        """Display the main menu"""
        print("\n" + "="*60)
        print("MCP MANAGEMENT SYSTEM - QUICK START")
        print("="*60)
        print("1. Start All Systems")
        print("2. Stop All Systems")
        print("3. Check System Status")
        print("4. Start Core MCP Servers Only")
        print("5. Start SAMR System Only")
        print("6. Start AI Agents Only")
        print("7. View System Configuration")
        print("8. View Available Servers")
        print("9. Organize/Reorganize Agents")
        print("10. Run Setup/Initialization")
        print("11. View Logs")
        print("12. Quick Health Check")
        print("0. Exit")
        print("-"*60)
        
    def run_status_check(self):
        """Run comprehensive status check"""
        print("\nRunning comprehensive status check...")
        try:
            result = subprocess.run([
                sys.executable, str(self.mcp_dir / "status_check.py")
            ], capture_output=True, text=True, timeout=30
            
            print("STATUS CHECK RESULTS:")
            print("-" * 40)
            print(result.stdout)
            if result.stderr:
                print("WARNINGS/ERRORS:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("Status check timed out")
        except Exception as e:
            print(f"Error running status check: {e}")
    
    def start_all_systems(self):
        """Start all MCP systems"""
        print("\nStarting all MCP systems...")
        try:
            subprocess.run([
                sys.executable, str(self.scripts_dir / "start_all.py")
            ], check=True
            print("All systems started successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error starting systems: {e}")
        except FileNotFoundError:
            print("Startup script not found. Running setup...")
            self.run_setup()
    
    def stop_all_systems(self):
        """Stop all MCP systems"""
        print("\nStopping all MCP systems...")
        
        # Try to find and stop running processes
        try:
            # This is a basic implementation - you might want to enhance it
            # based on how your servers are actually running
            result = subprocess.run([
                "taskkill", "/F", "/IM", "python.exe"
            ], capture_output=True, text=True, shell=True
            print("Stopped Python processes")
        except:
            print("Note: Manual process cleanup may be required")
        
        print("Systems stopped")
    
    def start_core_servers(self):
        """Start only core MCP servers"""
        print("\nStarting core MCP servers...")
        try:
            subprocess.run([
                sys.executable, str(self.scripts_dir / "start_core_servers.py")
            ], check=True
            print("Core servers started!")
        except Exception as e:
            print(f"Error starting core servers: {e}")
    
    def start_samr_system(self):
        """Start SAMR system"""
        print("\nStarting SAMR system...")
        try:
            subprocess.run([
                sys.executable, str(self.scripts_dir / "start_samr_system.py")
            ], check=True
            print("SAMR system started!")
        except Exception as e:
            print(f"Error starting SAMR system: {e}")
    
    def start_ai_agents(self):
        """Start AI agents"""
        print("\nStarting AI agents...")
        try:
            subprocess.run([
                sys.executable, str(self.scripts_dir / "start_ai_agents.py")
            ], check=True
            print("AI agents started!")
        except Exception as e:
            print(f"Error starting AI agents: {e}")
    
    def view_configuration(self):
        """View system configuration"""
        print("\nSystem Configuration:")
        print("-" * 40)
        
        config_file = self.config_dir / "master_config.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                print("Global Settings:")
                if 'global_settings' in config:
                    for key, value in config['global_settings'].items():
                        print(f"  {key}: {value}")
                
                print("\nServer Categories:")
                if 'server_categories' in config:
                    for category, settings in config['server_categories'].items():
                        enabled = settings.get('enabled', False)
                        priority = settings.get('priority', 'N/A')
                        print(f"  {category}: {'ENABLED' if enabled else 'DISABLED'} (Priority: {priority})")
                
                print("\nSAMR Configuration:")
                if 'samr_config' in config:
                    samr = config['samr_config']
                    print(f"  Enabled: {samr.get('enabled', False)}")
                    print(f"  Router Port: {samr.get('router_port', 'N/A')}")
                    print(f"  Management Port: {samr.get('management_port', 'N/A')}")
                        
            except Exception as e:
                print(f"Error reading configuration: {e}")
        else:
            print("Configuration file not found")
    
    def view_available_servers(self):
        """View available MCP servers and agents"""
        print("\nAvailable MCP Servers and Agents:")
        print("-" * 40)
        
        # Check MCP servers directory
        mcp_servers_dir = self.base_dir / "mcp_servers"
        if mcp_servers_dir.exists():
            servers = list(mcp_servers_dir.glob("*.py"))
            print(f"MCP Servers ({len(servers)}):")
            for server in sorted(servers)[:10]:  # Show first 10
                print(f"  - {server.name}")
            if len(servers) > 10:
                print(f"  ... and {len(servers) - 10} more")
        
        # Check unified AI agents
        ai_agents_dir = self.base_dir / "ai_agents_unified"
        if ai_agents_dir.exists():
            print("\nAI Agent Categories:")
            for category_dir in sorted(ai_agents_dir.iterdir()):
                if category_dir.is_dir():
                    agents = list(category_dir.glob("*.py"))
                    print(f"  {category_dir.name}: {len(agents)} agents")
    
    def organize_agents(self):
        """Run agent organization"""
        print("\nOrganizing/Reorganizing AI agents...")
        try:
            subprocess.run([
                sys.executable, str(self.mcp_dir / "organize_ai_agents.py")
            ], check=True
            print("Agent organization complete!")
        except Exception as e:
            print(f"Error organizing agents: {e}")
    
    def run_setup(self):
        """Run system setup/initialization"""
        print("\nRunning MCP management setup...")
        try:
            subprocess.run([
                sys.executable, str(self.base_dir / "setup_mcp_management.py")
            ], check=True
            print("Setup complete!")
        except Exception as e:
            print(f"Error running setup: {e}")
    
    def view_logs(self):
        """View recent log entries"""
        print("\nRecent Log Entries:")
        print("-" * 40)
        
        logs_dir = self.mcp_dir / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                # Show the most recent log file
                latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
                print(f"Latest log file: {latest_log.name}")
                try:
                    with open(latest_log, 'r') as f:
                        lines = f.readlines()
                        # Show last 20 lines
                        for line in lines[-20:]:
                            print(f"  {line.strip()}")
                except Exception as e:
                    print(f"Error reading log: {e}")
            else:
                print("No log files found")
        else:
            print("Logs directory not found")
    
    def quick_health_check(self):
        """Perform a quick health check"""
        print("\nQuick Health Check:")
        print("-" * 40)
        
        # Check if key directories exist
        checks = [
            ("MCP Management Directory", self.mcp_dir.exists()),
            ("Scripts Directory", self.scripts_dir.exists()),
            ("Config Directory", self.config_dir.exists()),
            ("AI Agents Unified", (self.base_dir / "ai_agents_unified").exists()),
            ("MCP Servers Directory", (self.base_dir / "mcp_servers").exists()),
            ("Master Config File", (self.config_dir / "master_config.yaml").exists()),

        
        all_good = True
        for check_name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {check_name}: {status}")
            if not result:
                all_good = False
        
        if all_good:
            print("\nALL CHECKS PASSED - System ready!")
        else:
            print("\nSOME CHECKS FAILED - Consider running setup")
    
    def run(self):
        """Main interactive loop"""
        while True:
            try:
                self.show_menu()
                choice = input("Enter your choice (0-12): ").strip()
                
                if choice == "0":
                    print("Goodbye!")
                    break
                elif choice == "1":
                    self.start_all_systems()
                elif choice == "2":
                    self.stop_all_systems()
                elif choice == "3":
                    self.run_status_check()
                elif choice == "4":
                    self.start_core_servers()
                elif choice == "5":
                    self.start_samr_system()
                elif choice == "6":
                    self.start_ai_agents()
                elif choice == "7":
                    self.view_configuration()
                elif choice == "8":
                    self.view_available_servers()
                elif choice == "9":
                    self.organize_agents()
                elif choice == "10":
                    self.run_setup()
                elif choice == "11":
                    self.view_logs()
                elif choice == "12":
                    self.quick_health_check()
                else:
                    print("Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")

if __name__ == "__main__":
    mcp_manager = MCPQuickStart()
    mcp_manager.run()
