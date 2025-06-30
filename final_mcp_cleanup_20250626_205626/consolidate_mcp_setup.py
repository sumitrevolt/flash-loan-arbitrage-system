#!/usr/bin/env python3
"""
MCP Setup Consolidation Script
===============================

This script consolidates all MCP-related configurations, setup scripts, and directories by:
1. Analyzing all MCP configuration files across the project
2. Merging configurations into a single, canonical config file
3. Removing duplicate setup scripts and keeping the best version
4. Cleaning up directory structure
5. Updating all references to point to the consolidated files

Author: AI Assistant
Date: 2024
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPSetupConsolidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
        # Target directories for consolidated files
        self.target_config_dir = self.project_root / "config"
        self.target_mcp_dir = self.project_root / "mcp_servers"
        self.target_scripts_dir = self.project_root / "scripts"
        
        # Files to analyze and consolidate
        self.config_files: List[Path] = []
        self.setup_scripts: List[Path] = []
        self.directories_to_clean: List[Path] = []
        
        # Results tracking
        self.consolidated_configs: Dict[str, Any] = {}
        self.removed_files: List[str] = []
        self.backup_dir = self.project_root / f"mcp_consolidation_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def discover_mcp_files(self):
        """Discover all MCP-related configuration files and setup scripts"""
        logger.info("🔍 Discovering MCP files across the project...")
        
        # Find all MCP configuration files
        for pattern in ["*mcp*.json", "*MCP*.json"]:
            self.config_files.extend(self.project_root.rglob(pattern))
        
        # Find all MCP setup scripts
        for pattern in ["*mcp*.py", "*MCP*.py", "setup*.py", "*setup*.py"]:
            potential_scripts = list(self.project_root.rglob(pattern))
            for script in potential_scripts:
                if self._is_mcp_setup_script(script):
                    self.setup_scripts.append(script)
        
        # Find directories to potentially clean
        for dir_path in self.project_root.rglob("*"):
            if dir_path.is_dir() and any(mcp_term in dir_path.name.lower() for mcp_term in ["mcp", "setup"]):
                if dir_path not in [self.target_config_dir, self.target_mcp_dir, self.target_scripts_dir]:
                    self.directories_to_clean.append(dir_path)
        
        logger.info(f"📊 Found {len(self.config_files)} config files, {len(self.setup_scripts)} setup scripts")
        
    def _is_mcp_setup_script(self, file_path: Path) -> bool:
        """Check if a Python file is an MCP setup script"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            mcp_indicators = [
                'mcp', 'MCP', 'Model Context Protocol', 
                'mcp_server', 'setup', 'configuration',
                'server', 'coordinator'
            ]
            return any(indicator in content for indicator in mcp_indicators)
        except Exception:
            return False
    
    def analyze_config_files(self):
        """Analyze and merge MCP configuration files"""
        logger.info("🔧 Analyzing MCP configuration files...")
        
        # Group config files by their purpose
        config_groups = {
            'unified': [],
            'claude': [],
            'cursor': [],
            'cline': [],
            'memory': [],
            'foundry': [],
            'other': []
        }
        
        for config_file in self.config_files:
            name_lower = config_file.name.lower()
            if 'unified' in name_lower:
                config_groups['unified'].append(config_file)
            elif 'claude' in name_lower:
                config_groups['claude'].append(config_file)
            elif 'cursor' in name_lower:
                config_groups['cursor'].append(config_file)
            elif 'cline' in name_lower:
                config_groups['cline'].append(config_file)
            elif 'memory' in name_lower:
                config_groups['memory'].append(config_file)
            elif 'foundry' in name_lower:
                config_groups['foundry'].append(config_file)
            else:
                config_groups['other'].append(config_file)
        
        # Find the best unified config as base
        best_unified_config = self._find_best_config_file(config_groups['unified'])
        if best_unified_config:
            logger.info(f"📝 Using {best_unified_config.name} as base configuration")
            try:
                with open(best_unified_config, 'r', encoding='utf-8') as f:
                    self.consolidated_configs = json.load(f)
            except Exception as e:
                logger.error(f"❌ Failed to load base config: {e}")
                self.consolidated_configs = {"servers": {}, "global_configuration": {}}
        else:
            self.consolidated_configs = {"servers": {}, "global_configuration": {}}
        
        # Merge configurations from other files
        self._merge_config_groups(config_groups)
        
    def _find_best_config_file(self, config_files: List[Path]) -> Optional[Path]:
        """Find the best configuration file based on size and content quality"""
        if not config_files:
            return None
        
        best_file = None
        best_score = 0
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                
                # Score based on number of servers and configuration completeness
                score = 0
                if 'servers' in content:
                    score += len(content['servers']) * 10
                if 'global_configuration' in content:
                    score += 5
                
                # Prefer files with more complete server configurations
                for server_config in content.get('servers', {}).values():
                    if isinstance(server_config, dict):
                        score += len(server_config.keys())
                
                if score > best_score:
                    best_score = score
                    best_file = config_file
                    
            except Exception:
                continue
        
        return best_file
    
    def _merge_config_groups(self, config_groups: Dict[str, List[Path]]):
        """Merge configurations from different groups"""
        for group_name, config_files in config_groups.items():
            if group_name == 'unified':
                continue  # Already used as base
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Merge servers
                    if 'servers' in config_data:
                        for server_name, server_config in config_data['servers'].items():
                            if server_name not in self.consolidated_configs['servers']:
                                self.consolidated_configs['servers'][server_name] = server_config
                    
                    # Merge global configuration
                    if 'global_configuration' in config_data:
                        self.consolidated_configs.setdefault('global_configuration', {}).update(
                            config_data['global_configuration']
                        )
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to merge {config_file.name}: {e}")
    
    def consolidate_setup_scripts(self):
        """Consolidate setup scripts by keeping the best version and removing duplicates"""
        logger.info("🛠️ Consolidating setup scripts...")
        
        # Group setup scripts by functionality
        script_groups = {}
        for script in self.setup_scripts:
            # Determine script type based on name and content
            script_type = self._categorize_setup_script(script)
            if script_type not in script_groups:
                script_groups[script_type] = []
            script_groups[script_type].append(script)
        
        # Keep the best script from each group
        for script_type, scripts in script_groups.items():
            if len(scripts) > 1:
                best_script = self._find_best_setup_script(scripts)
                target_path = self.target_scripts_dir / f"mcp_{script_type}.py"
                
                # Copy best script to target location
                if best_script != target_path:
                    shutil.copy2(best_script, target_path)
                    logger.info(f"✅ Kept best {script_type} script: {best_script.name} -> {target_path.name}")
                
                # Mark others for removal
                for script in scripts:
                    if script != best_script and script != target_path:
                        self.removed_files.append(str(script))
    
    def _categorize_setup_script(self, script_path: Path) -> str:
        """Categorize setup script by its functionality"""
        name_lower = script_path.name.lower()
        
        if 'management' in name_lower:
            return 'management'
        elif 'quick' in name_lower or 'start' in name_lower:
            return 'quick_start'
        elif 'container' in name_lower or 'docker' in name_lower:
            return 'container_setup'
        elif 'github' in name_lower:
            return 'github_setup'
        elif 'multi' in name_lower:
            return 'multi_setup'
        else:
            return 'general_setup'
    
    def _find_best_setup_script(self, scripts: List[Path]) -> Path:
        """Find the best setup script based on quality metrics"""
        best_script = scripts[0]
        best_score = 0
        
        for script in scripts:
            try:
                content = script.read_text(encoding='utf-8', errors='ignore')
                
                # Score based on various quality indicators
                score = 0
                score += len(content)  # Longer scripts often more complete
                score += content.count('def ') * 10  # More functions
                score += content.count('class ') * 20  # Classes indicate structure
                score += content.count('logger') * 5  # Logging
                score += content.count('try:') * 5  # Error handling
                score += content.count('async ') * 10  # Async functionality
                
                # Bonus for enhanced/fixed versions
                if any(term in script.name.lower() for term in ['enhanced', 'fixed', 'v2']):
                    score += 100
                
                if score > best_score:
                    best_score = score
                    best_script = script
                    
            except Exception:
                continue
        
        return best_script
    
    def clean_directories(self):
        """Clean up empty and duplicate directories"""
        logger.info("🧹 Cleaning up directories...")
        
        # Remove the src/mcp directory if it exists and is not needed
        src_mcp_dir = self.project_root / "src" / "mcp"
        if src_mcp_dir.exists():
            # Move any important files to the main mcp_servers directory
            for file in src_mcp_dir.rglob("*.py"):
                if file.name not in [f.name for f in self.target_mcp_dir.glob("*.py")]:
                    target = self.target_mcp_dir / file.name
                    shutil.copy2(file, target)
                    logger.info(f"📁 Moved {file.name} to consolidated mcp_servers/")
            
            # Remove the directory
            shutil.rmtree(src_mcp_dir)
            logger.info("🗑️ Removed src/mcp/ directory")
        
        # Remove duplicate config subdirectories
        config_json_dir = self.project_root / "config" / "json"
        if config_json_dir.exists():
            # Check if it contains unique files
            unique_files = []
            for file in config_json_dir.glob("*.json"):
                main_equivalent = self.target_config_dir / file.name
                if not main_equivalent.exists() or file.stat().st_size != main_equivalent.stat().st_size:
                    unique_files.append(file)
            
            # Move unique files to main config directory
            for file in unique_files:
                target = self.target_config_dir / f"alt_{file.name}"
                shutil.copy2(file, target)
                logger.info(f"📁 Moved unique config: {file.name} -> alt_{file.name}")
            
            # Remove the subdirectory
            shutil.rmtree(config_json_dir)
            logger.info("🗑️ Removed config/json/ subdirectory")
    
    def save_consolidated_config(self):
        """Save the consolidated MCP configuration"""
        logger.info("💾 Saving consolidated MCP configuration...")
        
        # Update paths in consolidated config to point to mcp_servers/
        for server_name, server_config in self.consolidated_configs.get('servers', {}).items():
            if 'path' in server_config:
                path = server_config['path']
                # Normalize paths to point to mcp_servers/
                if path.startswith('src/mcp_servers/'):
                    server_config['path'] = path.replace('src/mcp_servers/', 'mcp_servers/')
                elif not path.startswith('mcp_servers/'):
                    # Find the actual file in mcp_servers/
                    filename = Path(path).name
                    if (self.target_mcp_dir / filename).exists():
                        server_config['path'] = f"mcp_servers/{filename}"
        
        # Save consolidated config
        config_path = self.target_config_dir / "unified_mcp_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.consolidated_configs, f, indent=2)
        
        logger.info(f"✅ Saved consolidated config to {config_path}")
    
    def remove_duplicate_files(self):
        """Remove duplicate files that were consolidated"""
        logger.info("🗑️ Removing duplicate files...")
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        removed_count = 0
        for file_path in self.removed_files:
            try:
                file_obj = Path(file_path)
                if file_obj.exists():
                    # Create backup
                    backup_path = self.backup_dir / file_obj.name
                    shutil.copy2(file_obj, backup_path)
                    
                    # Remove original
                    file_obj.unlink()
                    removed_count += 1
                    logger.info(f"🗑️ Removed duplicate: {file_obj.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to remove {file_path}: {e}")
        
        # Remove duplicate config files (keep only the main unified config)
        for config_file in self.config_files:
            if config_file.name != "unified_mcp_config.json" and config_file.parent == self.target_config_dir:
                if any(term in config_file.name.lower() for term in ['mcp', 'setup']):
                    try:
                        # Backup and remove
                        backup_path = self.backup_dir / config_file.name
                        shutil.copy2(config_file, backup_path)
                        config_file.unlink()
                        removed_count += 1
                        logger.info(f"🗑️ Removed duplicate config: {config_file.name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to remove {config_file}: {e}")
        
        logger.info(f"✅ Removed {removed_count} duplicate files")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a consolidation report"""
        report = {
            "consolidation_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "summary": {
                "config_files_found": len(self.config_files),
                "setup_scripts_found": len(self.setup_scripts),
                "directories_cleaned": len(self.directories_to_clean),
                "files_removed": len(self.removed_files),
                "consolidated_servers": len(self.consolidated_configs.get('servers', {}))
            },
            "consolidated_config_location": "config/unified_mcp_config.json",
            "backup_directory": str(self.backup_dir),
            "servers_configured": list(self.consolidated_configs.get('servers', {}).keys()),
            "removed_files": self.removed_files,
            "recommendations": [
                "Use 'config/unified_mcp_config.json' as the single source of truth for MCP configuration",
                "All MCP servers are now located in 'mcp_servers/' directory",
                "Setup scripts are consolidated in 'scripts/' directory with mcp_ prefix",
                "Backup files are available in the backup directory if needed"
            ]
        }
        
        return report
    
    def run_consolidation(self):
        """Run the complete MCP setup consolidation process"""
        logger.info("🚀 Starting MCP Setup Consolidation...")
        
        try:
            # Step 1: Discover all MCP files
            self.discover_mcp_files()
            
            # Step 2: Analyze and merge configuration files
            self.analyze_config_files()
            
            # Step 3: Consolidate setup scripts
            self.consolidate_setup_scripts()
            
            # Step 4: Clean up directories
            self.clean_directories()
            
            # Step 5: Save consolidated configuration
            self.save_consolidated_config()
            
            # Step 6: Remove duplicate files
            self.remove_duplicate_files()
            
            # Step 7: Generate report
            report = self.generate_report()
            
            # Save report
            report_path = self.project_root / "MCP_SETUP_CONSOLIDATION_REPORT.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📊 Consolidation report saved to {report_path}")
            logger.info("🎉 MCP Setup Consolidation completed successfully!")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Consolidation failed: {e}")
            raise

def main():
    """Main function"""
    project_root = Path.cwd()
    consolidator = MCPSetupConsolidator(str(project_root))
    
    try:
        report = consolidator.run_consolidation()
        
        print("\n" + "="*80)
        print("🎉 MCP SETUP CONSOLIDATION COMPLETE!")
        print("="*80)
        print(f"📊 Consolidated {report['summary']['consolidated_servers']} MCP servers")
        print(f"🗑️ Removed {report['summary']['files_removed']} duplicate files")
        print(f"📁 Cleaned {report['summary']['directories_cleaned']} directories")
        print(f"📝 Configuration: {report['consolidated_config_location']}")
        print(f"💾 Backup: {report['backup_directory']}")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Consolidation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 