#!/usr/bin/env python3
"""
Master LangChain Integration System
===================================

Comprehensive system that integrates:
- Multi-Agent Terminal Coordinator
- GitHub Copilot Training System
- MCP Server Training and Management
- Advanced AI agent coordination for project development
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid
import signal
import argparse

# Import our custom modules
sys.path.append(str(Path(__file__).parent))

try:
    from multi_agent_terminal_coordinator import MultiAgentTerminalCoordinator, TaskRequest, AgentType
    from github_copilot_trainer import GitHubCopilotTrainer
    from mcp_server_trainer import MCPServerManager
except ImportError as e:
    logging.error(f"Failed to import modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('master_langchain_system.log')
    ]
)
logger = logging.getLogger(__name__)

class MasterLangChainSystem:
    """Master system integrating all LangChain components"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        
        # Initialize subsystems
        self.terminal_coordinator = MultiAgentTerminalCoordinator(str(self.project_root))
        self.copilot_trainer = GitHubCopilotTrainer(str(self.project_root))
        self.mcp_manager = MCPServerManager(str(self.project_root))
        
        # System state
        self.system_status = {
            "initialized": False,
            "subsystems_ready": 0,
            "total_subsystems": 3,
            "start_time": datetime.now(),
            "uptime": timedelta(),
            "tasks_completed": 0
        }
        
        # Background tasks
        self.background_tasks = []
        self.shutdown_requested = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the master system"""
        logger.info("🚀 Initializing Master LangChain System...")
        
        initialization_results = {
            "terminal_coordinator": {"success": False},
            "copilot_trainer": {"success": False},
            "mcp_manager": {"success": False}
        }
        
        try:
            # Initialize terminal coordinator
            logger.info("🤖 Initializing Terminal Coordinator...")
            if await self.terminal_coordinator.initialize():
                initialization_results["terminal_coordinator"]["success"] = True
                self.system_status["subsystems_ready"] += 1
                logger.info("✅ Terminal Coordinator initialized")
            else:
                logger.error("❌ Failed to initialize Terminal Coordinator")
            
            # Initialize copilot trainer (no async init needed)
            logger.info("💡 Initializing GitHub Copilot Trainer...")
            initialization_results["copilot_trainer"]["success"] = True
            self.system_status["subsystems_ready"] += 1
            logger.info("✅ GitHub Copilot Trainer initialized")
            
            # Initialize MCP manager (no async init needed)
            logger.info("🔧 Initializing MCP Server Manager...")
            initialization_results["mcp_manager"]["success"] = True
            self.system_status["subsystems_ready"] += 1
            logger.info("✅ MCP Server Manager initialized")
            
            # Mark system as initialized
            self.system_status["initialized"] = True
            
            logger.info(f"✅ Master System initialized with {self.system_status['subsystems_ready']}/{self.system_status['total_subsystems']} subsystems ready")
            
            return {
                "success": True,
                "subsystems_ready": self.system_status["subsystems_ready"],
                "total_subsystems": self.system_status["total_subsystems"],
                "results": initialization_results
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Master System: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": initialization_results
            }
    
    async def start_all_services(self) -> Dict[str, Any]:
        """Start all MCP servers and background services"""
        logger.info("🚀 Starting all services...")
        
        results = {
            "mcp_servers": {"success": False},
            "monitoring": {"success": False},
            "training": {"success": False}
        }
        
        try:
            # Start MCP servers
            logger.info("🔧 Starting MCP servers...")
            mcp_results = await self.mcp_manager.start_all_servers()
            results["mcp_servers"] = mcp_results
            
            # Start monitoring
            logger.info("🔍 Starting monitoring services...")
            monitoring_task = asyncio.create_task(self.mcp_manager.start_monitoring())
            self.background_tasks.append(monitoring_task)
            results["monitoring"]["success"] = True
            
            # Start background training
            logger.info("🎓 Starting training services...")
            training_task = asyncio.create_task(self._background_training())
            self.background_tasks.append(training_task)
            results["training"]["success"] = True
            
            logger.info("✅ All services started successfully")
            return {"success": True, "results": results}
            
        except Exception as e:
            logger.error(f"❌ Failed to start services: {e}")
            return {"success": False, "error": str(e), "results": results}
    
    async def _background_training(self):
        """Background training process"""
        logger.info("🎓 Starting background training process...")
        
        while not self.shutdown_requested:
            try:
                # Collect training data periodically
                training_data = await self.copilot_trainer.collect_training_data_from_project()
                
                if training_data:
                    # Train agents with collected data
                    session = await self.copilot_trainer.train_agent_with_copilot_data(training_data)
                    logger.info(f"📊 Completed training session: {session.session_id}")
                
                # Wait before next training cycle (1 hour)
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"❌ Error in background training: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def execute_terminal_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute terminal command through the coordinator"""
        return await self.terminal_coordinator.run_terminal_command(command, timeout)
    
    async def get_code_assistance(self, code_context: str, file_path: str = "") -> Dict[str, Any]:
        """Get code assistance through GitHub Copilot integration"""
        # Get suggestions from both systems
        copilot_result = await self.terminal_coordinator.get_code_assistance(code_context, file_path)
        training_result = await self.copilot_trainer.get_contextual_suggestions(code_context, "python")
        
        # Combine results
        combined_suggestions = []
        if copilot_result.get("success") and "result" in copilot_result:
            combined_suggestions.extend(copilot_result["result"].get("suggestions", []))
        
        if training_result.get("suggestions"):
            combined_suggestions.extend(training_result["suggestions"])
        
        # Remove duplicates
        unique_suggestions = list(set(combined_suggestions))
        
        return {
            "success": True,
            "suggestions": unique_suggestions[:20],  # Top 20 suggestions
            "sources": ["terminal_coordinator", "copilot_trainer"],
            "confidence": training_result.get("confidence", 0.5)
        }
    
    async def train_mcp_server(self, server_name: str, training_data: Dict = None) -> Dict[str, Any]:
        """Train MCP server"""
        return await self.terminal_coordinator.train_mcp_server(server_name, training_data)
    
    async def manage_project(self, action: str, project_path: str = "") -> Dict[str, Any]:
        """Manage project through coordinator"""
        return await self.terminal_coordinator.manage_project(action, project_path)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Update uptime
        self.system_status["uptime"] = datetime.now() - self.system_status["start_time"]
        
        # Get subsystem statuses
        terminal_status = self.terminal_coordinator.get_system_status()
        mcp_status = await self.mcp_manager.get_server_status()
        copilot_report = await self.copilot_trainer.generate_training_report()
        
        return {
            "master_system": self.system_status,
            "terminal_coordinator": terminal_status,
            "mcp_servers": mcp_status,
            "copilot_training": copilot_report,
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        logger.info("📊 Generating comprehensive system report...")
        
        system_status = await self.get_system_status()
        mcp_performance = await self.mcp_manager.generate_performance_report()
        code_analysis = await self.copilot_trainer.analyze_code_patterns()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "system_overview": {
                "uptime": str(system_status["master_system"]["uptime"]),
                "subsystems_ready": system_status["master_system"]["subsystems_ready"],
                "total_tasks_completed": system_status["terminal_coordinator"]["total_tasks_completed"],
                "agents_active": system_status["terminal_coordinator"]["agents_active"],
                "mcp_servers_healthy": mcp_performance["summary"]["healthy_servers"],
                "training_sessions": mcp_performance["summary"]["training_sessions"]
            },
            "detailed_status": system_status,
            "mcp_performance": mcp_performance,
            "code_analysis": code_analysis,
            "recommendations": self._generate_recommendations(system_status, mcp_performance, code_analysis)
        }
        
        return report
    
    def _generate_recommendations(self, system_status: Dict, mcp_performance: Dict, code_analysis: Dict) -> List[str]:
        """Generate system recommendations"""
        recommendations = []
        
        # System recommendations
        if system_status["master_system"]["subsystems_ready"] < system_status["master_system"]["total_subsystems"]:
            recommendations.append("Some subsystems failed to initialize - check logs for details")
        
        # MCP recommendations
        if mcp_performance["summary"]["health_percentage"] < 80:
            recommendations.append("MCP server health is below 80% - consider restarting unhealthy servers")
        
        if mcp_performance["summary"]["total_restarts"] > 10:
            recommendations.append("High number of server restarts detected - investigate stability issues")
        
        # Code analysis recommendations
        if code_analysis.get("languages", {}).get("python", {}).get("avg_quality", 0) < 0.6:
            recommendations.append("Python code quality is below average - consider code review and refactoring")
        
        # Training recommendations
        training_sessions = mcp_performance["summary"]["training_sessions"]
        if training_sessions == 0:
            recommendations.append("No training sessions detected - consider initiating agent training")
        elif training_sessions < 5:
            recommendations.append("Limited training data available - consider collecting more training samples")
        
        return recommendations
    
    async def start_interactive_mode(self):
        """Start interactive mode for user commands"""
        logger.info("🎮 Starting Master System Interactive Mode...")
        
        print("\n" + "="*60)
        print("🚀 MASTER LANGCHAIN SYSTEM - INTERACTIVE MODE")
        print("="*60)
        print("\nAvailable Commands:")
        print("  'terminal <command>'     - Execute terminal command")
        print("  'code <description>'     - Get code assistance")
        print("  'train <server_name>'    - Train MCP server")
        print("  'project <action>'       - Manage project")
        print("  'status'                 - Show system status")
        print("  'report'                 - Generate comprehensive report")
        print("  'mcp status'             - Show MCP server status")
        print("  'mcp start <name>'       - Start specific MCP server")
        print("  'mcp stop <name>'        - Stop specific MCP server")
        print("  'mcp restart <name>'     - Restart specific MCP server")
        print("  'help'                   - Show this help message")
        print("  'quit'                   - Exit interactive mode")
        print("\n" + "="*60 + "\n")
        
        while not self.shutdown_requested:
            try:
                user_input = input("🤖 Master System> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input.lower() == 'help':
                    print("\nCommands:")
                    print("  terminal <cmd> - Execute terminal command")
                    print("  code <desc>   - Get code assistance")
                    print("  train <name>  - Train MCP server")
                    print("  project <act> - Manage project")
                    print("  status        - System status")
                    print("  report        - Full report")
                    print("  mcp status    - MCP server status")
                    continue
                
                # Parse command
                parts = user_input.split(' ', 2)
                command = parts[0].lower()
                
                if command == 'status':
                    status = await self.get_system_status()
                    print(json.dumps({
                        "uptime": str(status["master_system"]["uptime"]),
                        "subsystems_ready": status["master_system"]["subsystems_ready"],
                        "agents_active": status["terminal_coordinator"]["agents_active"],
                        "tasks_completed": status["terminal_coordinator"]["total_tasks_completed"],
                        "mcp_servers": len(status["mcp_servers"]["servers"])
                    }, indent=2))
                    continue
                
                elif command == 'report':
                    print("📊 Generating comprehensive report...")
                    report = await self.generate_comprehensive_report()
                    
                    # Print summary
                    print("\n📋 SYSTEM REPORT SUMMARY")
                    print(f"Uptime: {report['system_overview']['uptime']}")
                    print(f"Tasks Completed: {report['system_overview']['total_tasks_completed']}")
                    print(f"Agents Active: {report['system_overview']['agents_active']}")
                    print(f"MCP Servers Healthy: {report['system_overview']['mcp_servers_healthy']}")
                    
                    if report.get('recommendations'):
                        print("\n💡 RECOMMENDATIONS:")
                        for rec in report['recommendations']:
                            print(f"  • {rec}")
                    
                    # Save full report
                    report_file = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(report_file, 'w') as f:
                        json.dump(report, f, indent=2, default=str)
                    print(f"\n💾 Full report saved to: {report_file}")
                    continue
                
                elif command == 'mcp':
                    if len(parts) < 2:
                        print("❌ Usage: mcp <status|start|stop|restart> [server_name]")
                        continue
                    
                    mcp_action = parts[1].lower()
                    
                    if mcp_action == 'status':
                        status = await self.mcp_manager.get_server_status()
                        print(f"\n📊 MCP SERVERS STATUS ({status['total_servers']} servers)")
                        for name, info in status['servers'].items():
                            print(f"  • {name}: {info['status']} (port {info['port']})")
                        continue
                    
                    elif mcp_action in ['start', 'stop', 'restart'] and len(parts) == 3:
                        server_name = parts[2]
                        if mcp_action == 'start':
                            result = await self.mcp_manager.start_server(server_name)
                        elif mcp_action == 'stop':
                            result = await self.mcp_manager.stop_server(server_name)
                        else:  # restart
                            result = await self.mcp_manager.restart_server(server_name)
                        
                        if result["success"]:
                            print(f"✅ {mcp_action.title()} successful for {server_name}")
                        else:
                            print(f"❌ {mcp_action.title()} failed for {server_name}: {result.get('error', 'Unknown error')}")
                        continue
                
                # Handle other commands
                if len(parts) < 2:
                    print("❌ Invalid command format")
                    continue
                
                args = ' '.join(parts[1:])
                
                if command == 'terminal':
                    print(f"🔧 Executing: {args}")
                    result = await self.execute_terminal_command(args)
                elif command == 'code':
                    print(f"💡 Getting code assistance for: {args}")
                    result = await self.get_code_assistance(args)
                elif command == 'train':
                    print(f"🎓 Training MCP server: {args}")
                    result = await self.train_mcp_server(args)
                elif command == 'project':
                    print(f"📁 Managing project: {args}")
                    result = await self.manage_project(args)
                else:
                    print(f"❌ Unknown command: {command}")
                    continue
                
                # Display result
                if result.get("success"):
                    print("✅ Success!")
                    if "suggestions" in result:
                        print("💡 Suggestions:")
                        for i, suggestion in enumerate(result["suggestions"][:5], 1):
                            print(f"  {i}. {suggestion}")
                    elif "result" in result:
                        print(f"📄 Result: {json.dumps(result['result'], indent=2, default=str)}")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
                self.system_status["tasks_completed"] += 1
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                logger.error(f"❌ Error in interactive mode: {e}")
                print(f"❌ Error: {e}")
        
        print("\n👋 Exiting interactive mode...")
    
    async def shutdown(self):
        """Shutdown the master system"""
        logger.info("🛑 Shutting down Master LangChain System...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Shutdown subsystems
        await self.terminal_coordinator.shutdown()
        await self.mcp_manager.stop_all_servers()
        
        logger.info("✅ Master System shutdown completed")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Master LangChain Integration System")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--mode", choices=["interactive", "daemon"], default="interactive",
                       help="Run mode: interactive or daemon")
    parser.add_argument("--start-services", action="store_true", 
                       help="Start all MCP servers and services")
    
    args = parser.parse_args()
    
    # Create master system
    system = MasterLangChainSystem(args.project_root)
    
    try:
        # Initialize system
        logger.info("🚀 Starting Master LangChain System...")
        init_result = await system.initialize()
        
        if not init_result["success"]:
            logger.error("❌ Failed to initialize system")
            return 1
        
        # Start services if requested
        if args.start_services:
            services_result = await system.start_all_services()
            if services_result["success"]:
                logger.info("✅ All services started successfully")
            else:
                logger.warning("⚠️ Some services failed to start")
        
        # Run in selected mode
        if args.mode == "interactive":
            await system.start_interactive_mode()
        else:  # daemon mode
            logger.info("🔄 Running in daemon mode...")
            while not system.shutdown_requested:
                await asyncio.sleep(10)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
        return 0
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        return 1
    finally:
        await system.shutdown()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
