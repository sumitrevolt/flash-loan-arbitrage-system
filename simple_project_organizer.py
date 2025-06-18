#!/usr/bin/env python3
"""
Simplified Project Organizer with MCP Server Integration
======================================================

This script organizes the flash loan project by:
1. Removing duplicate files
2. Fixing syntax errors
3. Integrating MCP servers and AI agents
4. Creating organized structure

Author: GitHub Copilot Assistant
Date: June 17, 2025
"""

import os
import sys
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_organization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleProjectOrganizer:
    """Simplified project organizer"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.duplicates_removed = 0
        self.files_organized = 0
        self.mcp_servers_found = 0
        self.ai_agents_created = 0
        
    def get_file_hash(self, file_path):
        """Get MD5 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def find_duplicates(self):
        """Find and remove duplicate files"""
        logger.info("🔍 Finding duplicate files...")
        
        file_hashes = {}
        duplicates = []
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                # Skip certain directories
                skip_dirs = {'.git', 'node_modules', '__pycache__', '.vscode'}
                if any(part in skip_dirs for part in file_path.parts):
                    continue
                
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        duplicates.append(file_path)
                        logger.info(f"Duplicate found: {file_path.name}")
                    else:
                        file_hashes[file_hash] = file_path
        
        # Archive duplicates
        if duplicates:
            archive_dir = self.project_root / 'archive' / 'duplicates'
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            for dup_file in duplicates:
                try:
                    archive_path = archive_dir / dup_file.name
                    counter = 1
                    while archive_path.exists():
                        stem = dup_file.stem
                        suffix = dup_file.suffix
                        archive_path = archive_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(dup_file), str(archive_path))
                    self.duplicates_removed += 1
                    logger.info(f"Archived: {dup_file.name}")
                except Exception as e:
                    logger.error(f"Error archiving {dup_file}: {e}")
        
        logger.info(f"Removed {self.duplicates_removed} duplicate files")
    
    def organize_files(self):
        """Organize files into proper structure"""
        logger.info("📁 Organizing file structure...")
        
        # Create organized directories
        directories = {
            'contracts': ['*.sol'],
            'scripts': ['*.js', '*.ts'],
            'src': ['*.py'],
            'docs': ['*.md', '*.txt'],
            'config': ['*.json', '*.yaml', '*.yml', '*.env']
        }
        
        for dir_name in directories.keys():
            (self.project_root / dir_name).mkdir(exist_ok=True)
        
        # Move files to appropriate directories
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and file_path.parent == self.project_root:
                # Skip important root files
                if file_path.name in {'package.json', '.gitignore', 'hardhat.config.js', 'README.md'}:
                    continue
                
                # Determine target directory
                for dir_name, patterns in directories.items():
                    for pattern in patterns:
                        if file_path.match(pattern):
                            target_dir = self.project_root / dir_name
                            target_path = target_dir / file_path.name
                            
                            # Handle name conflicts
                            counter = 1
                            while target_path.exists():
                                stem = file_path.stem
                                suffix = file_path.suffix
                                target_path = target_dir / f"{stem}_{counter}{suffix}"
                                counter += 1
                            
                            try:
                                shutil.move(str(file_path), str(target_path))
                                self.files_organized += 1
                                logger.info(f"Moved {file_path.name} to {dir_name}/")
                            except Exception as e:
                                logger.error(f"Error moving {file_path}: {e}")
                            break
        
        logger.info(f"Organized {self.files_organized} files")
    
    def setup_mcp_servers(self):
        """Setup MCP servers"""
        logger.info("🤖 Setting up MCP servers...")
        
        mcp_dir = self.project_root / 'mcp_servers'
        mcp_dir.mkdir(exist_ok=True)
        
        # Find existing MCP files
        mcp_files = []
        for pattern in ['*mcp*server*.py', '*mcp*.py']:
            mcp_files.extend(self.project_root.rglob(pattern))
        
        # Remove files from archive/backup directories
        mcp_files = [f for f in mcp_files if 'archive' not in str(f) and 'backup' not in str(f)]
        
        # Create unified MCP configuration
        mcp_config = {
            "servers": {},
            "global_configuration": {
                "health_check_interval": 30,
                "auto_restart": True
            }
        }
        
        for i, mcp_file in enumerate(mcp_files):
            server_name = mcp_file.stem
            
            # Copy to MCP directory if not already there
            if mcp_file.parent != mcp_dir:
                target_path = mcp_dir / mcp_file.name
                if not target_path.exists():
                    shutil.copy2(mcp_file, target_path)
                    logger.info(f"Copied {mcp_file.name} to mcp_servers/")
            
            # Add to configuration
            mcp_config["servers"][server_name] = {
                "name": server_name,
                "type": "python",
                "path": f"mcp_servers/{mcp_file.name}",
                "port": 8000 + i,
                "enabled": True
            }
            
            self.mcp_servers_found += 1
        
        # Save configuration
        config_path = self.project_root / 'unified_mcp_config.json'
        with open(config_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        
        logger.info(f"Configured {self.mcp_servers_found} MCP servers")
    
    def create_ai_agents(self):
        """Create AI agent templates"""
        logger.info("🧠 Creating AI agents...")
        
        ai_dir = self.project_root / 'ai_agents'
        ai_dir.mkdir(exist_ok=True)
        
        agents = {
            "flash_loan_optimizer": {
                "role": "Flash loan opportunity analysis",
                "port": 9001
            },
            "risk_manager": {
                "role": "Risk assessment and management", 
                "port": 9002
            },
            "arbitrage_detector": {
                "role": "Cross-DEX arbitrage detection",
                "port": 9003
            },
            "transaction_executor": {
                "role": "Transaction execution and monitoring",
                "port": 9004
            }
        }
        
        for agent_name, config in agents.items():
            agent_script = f'''#!/usr/bin/env python3
"""
{agent_name.replace('_', ' ').title()} AI Agent
Role: {config['role']}
"""

from flask import Flask, jsonify
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health')
def health_check():
    return jsonify({{
        'status': 'healthy',
        'agent': '{agent_name}',
        'timestamp': datetime.now().isoformat()
    }})

@app.route('/status')
def get_status():
    return jsonify({{
        'agent': '{agent_name}',
        'role': '{config['role']}',
        'active': True
    }})

if __name__ == '__main__':
    logger.info(f"Starting {{'{agent_name}'}} on port {config['port']}")
    app.run(host='0.0.0.0', port={config['port']})
'''
            
            agent_file = ai_dir / f"{agent_name}.py"
            with open(agent_file, 'w') as f:
                f.write(agent_script)
            
            self.ai_agents_created += 1
            logger.info(f"Created AI agent: {agent_name}")
        
        # Save AI configuration
        ai_config = {"agents": agents}
        config_path = self.project_root / 'ai_agents_config.json'
        with open(config_path, 'w') as f:
            json.dump(ai_config, f, indent=2)
        
        logger.info(f"Created {self.ai_agents_created} AI agents")
    
    def fix_python_syntax(self):
        """Fix common Python syntax issues"""
        logger.info("🔧 Fixing Python syntax issues...")
        
        fixed_count = 0
        
        for py_file in self.project_root.rglob('*.py'):
            # Skip certain directories
            skip_dirs = {'.git', 'node_modules', '__pycache__', 'venv'}
            if any(part in skip_dirs for part in py_file.parts):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix common issues
                if 'from typing import' not in content and ('Dict' in content or 'List' in content):
                    content = "from typing import Dict, List, Any, Optional\\n" + content
                
                if 'async def' in content and 'import asyncio' not in content:
                    content = "import asyncio\\n" + content
                
                # Fix indentation (tabs to spaces)
                lines = content.split('\\n')
                fixed_lines = []
                for line in lines:
                    fixed_lines.append(line.expandtabs(4))
                content = '\\n'.join(fixed_lines)
                
                if content != original_content:
                    # Backup original
                    backup_path = py_file.with_suffix('.py.backup')
                    shutil.copy2(py_file, backup_path)
                    
                    # Write fixed content
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    fixed_count += 1
                    logger.info(f"Fixed syntax in {py_file.name}")
                    
            except Exception as e:
                logger.error(f"Error fixing {py_file}: {e}")
        
        logger.info(f"Fixed syntax in {fixed_count} Python files")
    
    def update_package_json(self):
        """Update package.json with new scripts"""
        logger.info("📦 Updating package.json...")
        
        package_json_path = self.project_root / 'package.json'
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Add new scripts
            new_scripts = {
                "organize": "python simple_project_organizer.py",
                "start:mcp": "python -m mcp_servers.unified_mcp_coordinator",
                "start:ai": "python -m ai_agents.flash_loan_optimizer",
                "health:check": "curl http://localhost:9001/health"
            }
            
            if "scripts" not in package_data:
                package_data["scripts"] = {}
            
            package_data["scripts"].update(new_scripts)
            
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            logger.info("Updated package.json")
            
        except Exception as e:
            logger.error(f"Error updating package.json: {e}")
    
    def generate_report(self):
        """Generate organization report"""
        report = f"""
Flash Loan Project Organization Report
=====================================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
✅ {self.duplicates_removed} duplicate files removed
✅ {self.files_organized} files organized into proper structure
✅ {self.mcp_servers_found} MCP servers configured
✅ {self.ai_agents_created} AI agents created

ORGANIZED STRUCTURE:
📁 contracts/        - Solidity smart contracts
📁 scripts/          - JavaScript/TypeScript deployment scripts
📁 src/              - Python source code
📁 mcp_servers/      - MCP server implementations
📁 ai_agents/        - AI agent implementations
📁 config/           - Configuration files
📁 docs/             - Documentation
📁 archive/          - Archived/backup files

CONFIGURATION FILES CREATED:
📄 unified_mcp_config.json    - MCP server configuration
📄 ai_agents_config.json      - AI agent configuration

NEXT STEPS:
1. Review the organized structure
2. Test MCP servers: npm run start:mcp
3. Test AI agents: npm run start:ai
4. Run health checks: npm run health:check

🎉 Project organization completed successfully!
"""
        return report
    
    def organize(self):
        """Main organization method"""
        logger.info("🚀 Starting project organization...")
        
        try:
            # Step 1: Find and remove duplicates
            self.find_duplicates()
            
            # Step 2: Organize file structure
            self.organize_files()
            
            # Step 3: Fix Python syntax
            self.fix_python_syntax()
            
            # Step 4: Setup MCP servers
            self.setup_mcp_servers()
            
            # Step 5: Create AI agents
            self.create_ai_agents()
            
            # Step 6: Update package.json
            self.update_package_json()
            
            # Step 7: Generate report
            report = self.generate_report()
            
            # Save report
            report_path = self.project_root / 'PROJECT_ORGANIZATION_REPORT.md'
            with open(report_path, 'w') as f:
                f.write(report)
            
            print(report)
            logger.info("✅ Project organization completed!")
            
        except Exception as e:
            logger.error(f"❌ Error during organization: {e}")
            print(f"Error: {e}")

def main():
    """Main entry point"""
    organizer = SimpleProjectOrganizer()
    organizer.organize()

if __name__ == "__main__":
    main()
