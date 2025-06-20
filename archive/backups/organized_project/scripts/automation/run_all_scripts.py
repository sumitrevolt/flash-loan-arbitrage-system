#!/usr/bin/env python3
"""
LangChain Master Script Runner
=============================

This script runs all project scripts sequentially using LangChain coordination
to complete the flash loan arbitrage project.

Author: GitHub Copilot Assistant
Date: December 2024
"""

import asyncio
import logging
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('master_script_runner.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class MasterScriptRunner:
    """Coordinates execution of all project scripts using LangChain"""
    
    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.execution_report: Dict[str, Any] = {
            'start_time': datetime.now().isoformat(),
            'scripts_executed': [],
            'successful_executions': 0,
            'failed_executions': 0,
            'total_execution_time': 0
        }
        
        # Define script execution sequence with explicit typing
        self.script_sequence: list[Dict[str, Any]] = [
            # 1. Project Organization & Cleanup
            {
                'name': 'Project Organizer',
                'script': 'project_organizer_langchain.py',
                'description': 'Organize project structure and remove duplicates',
                'timeout': 300
            },
            
            # 2. Automated Project Fixer
            {
                'name': 'Automated Fixer',
                'script': 'automated_langchain_project_fixer.py',
                'description': 'Fix code issues and dependencies',
                'timeout': 600
            },
            
            # 3. Start Enhanced LangChain System
            {
                'name': 'Enhanced System Launcher',
                'script': 'start_enhanced_system.ps1',
                'shell': True,
                'description': 'Launch enhanced LangChain system',
                'timeout': 180
            },
            
            # 4. MCP Training
            {
                'name': 'MCP Training',
                'script': 'scripts/start_training.py',
                'description': 'Train MCP servers and AI models',
                'timeout': 900
            },
            
            # 5. Docker Deployment
            {
                'name': 'Docker Deployment',
                'script': 'scripts/automation/automated_langchain_deployer.py',
                'description': 'Deploy all MCP servers and AI agents',
                'timeout': 1200
            },
            
            # 6. System Health Check
            {
                'name': 'Health Check',
                'script': 'src/tools/working_health_check.py',
                'description': 'Verify system health and functionality',
                'timeout': 120
            },
            
            # 7. Start Main System
            {
                'name': 'Main System',
                'script': 'src/tools/unified_system_launcher.py',
                'description': 'Launch the main arbitrage system',
                'timeout': 300
            }
        ]
    
    async def run_all_scripts(self) -> Dict[str, Any]:
        """Execute all scripts in sequence"""
        logger.info("🚀 Starting Master Script Runner...")
        logger.info(f"📁 Project root: {self.project_root}")
        logger.info(f"📋 Total scripts to execute: {len(self.script_sequence)}")
        
        start_time = time.time()
        
        for i, script_config in enumerate(self.script_sequence, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"📜 Step {i}/{len(self.script_sequence)}: {script_config['name']}")
            logger.info(f"📄 Script: {script_config['script']}")
            logger.info(f"📝 Description: {script_config['description']}")
            logger.info(f"{'='*60}")
            
            success = await self._execute_script(script_config)
            
            if success:
                self.execution_report['successful_executions'] += 1
                logger.info(f"✅ {script_config['name']} completed successfully")
            else:
                self.execution_report['failed_executions'] += 1
                logger.error(f"❌ {script_config['name']} failed")
                
                # Ask user whether to continue
                if not await self._should_continue_on_failure(script_config):
                    logger.info("🛑 Execution stopped by user")
                    break
            
            # Brief pause between scripts
            await asyncio.sleep(2)
        
        total_time = time.time() - start_time
        self.execution_report['total_execution_time'] = total_time
        self.execution_report['end_time'] = datetime.now().isoformat()
        
        await self._generate_final_report()
        
        return self.execution_report
    
    async def _execute_script(self, script_config: Dict[str, Any]) -> bool:
        """Execute a single script"""
        script_path = self.project_root / script_config['script']
        
        if not script_path.exists():
            logger.error(f"❌ Script not found: {script_path}")
            self.execution_report['scripts_executed'].append({
                'name': script_config['name'],
                'script': script_config['script'],
                'status': 'not_found',
                'error': f"Script file not found: {script_path}"
            })
            return False
        
        try:
            # Determine execution method
            if script_path.suffix == '.py':
                cmd = [sys.executable, str(script_path)]
            elif script_path.suffix == '.ps1':
                cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]
            elif script_path.suffix == '.bat':
                cmd = [str(script_path)]
            else:
                cmd = [sys.executable, str(script_path)]
            
            # Execute script
            logger.info(f"🔄 Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=script_config.get('timeout', 300)
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.error(f"⏰ Script timed out after {script_config.get('timeout', 300)} seconds")
                
                self.execution_report['scripts_executed'].append({
                    'name': script_config['name'],
                    'script': script_config['script'],
                    'status': 'timeout',
                    'error': 'Script execution timed out'
                })
                return False
            
            # Log output
            if stdout:
                logger.info(f"📤 Output:\n{stdout.decode('utf-8', errors='ignore')}")
            if stderr:
                logger.warning(f"⚠️ Errors:\n{stderr.decode('utf-8', errors='ignore')}")
            
            success = process.returncode == 0
            
            self.execution_report['scripts_executed'].append({
                'name': script_config['name'],
                'script': script_config['script'],
                'status': 'success' if success else 'failed',
                'return_code': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore') if stdout else '',
                'stderr': stderr.decode('utf-8', errors='ignore') if stderr else ''
            })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error executing script: {e}")
            self.execution_report['scripts_executed'].append({
                'name': script_config['name'],
                'script': script_config['script'],
                'status': 'error',
                'error': str(e)
            })
            return False
    
    async def _should_continue_on_failure(self, script_config: Dict[str, Any]) -> bool:
        """Ask user whether to continue after a script failure"""
        # In an automated environment, we might want to continue
        # For now, let's continue with non-critical failures
        critical_scripts = ['Project Organizer', 'Automated Fixer']
        
        if script_config['name'] in critical_scripts:
            logger.warning("⚠️ Critical script failed - stopping execution")
            return False
        else:
            logger.info("ℹ️ Non-critical script failed - continuing with next script")
            return True
    
    async def _generate_final_report(self):
        """Generate comprehensive execution report"""
        logger.info("\n" + "="*80)
        logger.info("📊 MASTER SCRIPT RUNNER - FINAL REPORT")
        logger.info("="*80)
        
        logger.info(f"⏰ Start Time: {self.execution_report['start_time']}")
        logger.info(f"⏰ End Time: {self.execution_report['end_time']}")
        logger.info(f"⌚ Total Execution Time: {self.execution_report['total_execution_time']:.2f} seconds")
        logger.info(f"📈 Scripts Executed: {len(self.execution_report['scripts_executed'])}")
        logger.info(f"✅ Successful: {self.execution_report['successful_executions']}")
        logger.info(f"❌ Failed: {self.execution_report['failed_executions']}")
        
        logger.info("\n📋 Detailed Results:")
        for script_result in self.execution_report['scripts_executed']:
            status_emoji = "✅" if script_result['status'] == 'success' else "❌"
            logger.info(f"   {status_emoji} {script_result['name']}: {script_result['status']}")
        
        # Save detailed report
        report_path = self.project_root / f"execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.execution_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Detailed report saved to: {report_path}")
        
        # Generate next steps
        if self.execution_report['failed_executions'] == 0:
            logger.info("\n🎉 ALL SCRIPTS COMPLETED SUCCESSFULLY!")
            logger.info("🚀 Your flash loan arbitrage system should now be fully operational!")
            logger.info("\n📝 Next Steps:")
            logger.info("   1. Check system health: python src/tools/working_health_check.py")
            logger.info("   2. Access web dashboard: http://localhost:8080")
            logger.info("   3. Monitor system: python src/tools/system_monitor.py")
            logger.info("   4. Start trading: python src/tools/real_trading_executor.py")
        else:
            logger.warning("\n⚠️ SOME SCRIPTS FAILED")
            logger.info("📝 Recommended Actions:")
            logger.info("   1. Review the execution report above")
            logger.info("   2. Fix any critical issues")
            logger.info("   3. Re-run failed scripts individually")
            logger.info("   4. Check logs for detailed error information")


async def main():
    """Main entry point"""
    print("🌟 LangChain Flash Loan Arbitrage Project - Master Runner")
    print("="*60)
    
    try:
        runner = MasterScriptRunner()
        report = await runner.run_all_scripts()
        
        # Print final summary
        scripts_executed = report.get('scripts_executed', [])
        if scripts_executed:
            success_rate = (report['successful_executions'] / len(scripts_executed)) * 100
            print(f"\n🎯 EXECUTION SUMMARY:")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Total Time: {report['total_execution_time']:.2f} seconds")
            
            if success_rate >= 90:
                print("\n🚀 PROJECT SETUP COMPLETE! Your system is ready to use.")
            elif success_rate >= 70:
                print("\n✅ PROJECT MOSTLY COMPLETE! Check failed scripts and retry if needed.")
            else:
                print("\n⚠️ PROJECT NEEDS ATTENTION! Multiple scripts failed - review and fix issues.")
        else:
            print("\n⚠️ No scripts were executed.")
            
    except KeyboardInterrupt:
        print("\n🛑 Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
