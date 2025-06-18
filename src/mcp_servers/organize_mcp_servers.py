#!/usr/bin/env python3
"""
Organize and consolidate MCP servers in the project
"""

import shutil
import json
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MCPServerOrganizer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.mcp_servers_dir = project_root / "mcp_servers"
        self.backup_dir = project_root / "backups" / "mcp_reorganization"
        
    def organize(self):
        """Main organization process"""
        logger.info("Starting MCP server organization...")
        
        # Create backup
        self._create_backup()
        
        # Clean up old structure
        self._cleanup_old_structure()
        
        # Organize servers
        self._organize_servers()
        
        # Update configurations
        self._update_configurations()
        
        logger.info("MCP server organization completed!")
        
    def _create_backup(self):
        """Create backup of current structure"""
        if self.mcp_servers_dir.exists():
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(self.mcp_servers_dir, backup_path)
            logger.info(f"Backup created at: {backup_path}")
            
    def _cleanup_old_structure(self):
        """Remove duplicate and obsolete directories"""
        cleanup_paths = [
            "mcp_servers_organized",
            "mcp_server",
            "infrastructure/mcp_servers",
            "mcp_servers/task_management/mcp-taskmanager"  # Move contents up one level
        ]
        
        for path in cleanup_paths:
            full_path = self.project_root / path
            if full_path.exists():
                shutil.rmtree(full_path)
                logger.info(f"Removed: {path}")
                
    def _organize_servers(self):
        """Organize server directories"""
        servers = ["task_management", "github", "websearch", "filesystem"]
        
        for server in servers:
            server_dir = self.mcp_servers_dir / server
            src_dir = server_dir / "src"
            
            # Create src directory if it doesn't exist
            src_dir.mkdir(parents=True, exist_ok=True)
            
            # Move TypeScript files to src
            for ts_file in server_dir.glob("*.ts"):
                shutil.move(str(ts_file), str(src_dir / ts_file.name))
                logger.info(f"Moved {ts_file.name} to src/")
                
    def _update_configurations(self):
        """Update package.json and tsconfig.json files"""
        for server_dir in self.mcp_servers_dir.iterdir():
            if server_dir.is_dir():
                # Update package.json
                package_json_path = server_dir / "package.json"
                if package_json_path.exists():
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    # Update name to use consistent namespace
                    if package_data.get('name', '').startswith('@kazuph/'):
                        package_data['name'] = package_data['name'].replace('@kazuph/', '@flashloan/')
                    
                    with open(package_json_path, 'w') as f:
                        json.dump(package_data, f, indent=2)
                    
                    logger.info(f"Updated package.json for {server_dir.name}")

if __name__ == "__main__":
    import sys
    
    project_root = Path(__file__).parent.parent
    organizer = MCPServerOrganizer(project_root)
    
    try:
        organizer.organize()
    except Exception as e:
        logger.error(f"Organization failed: {e}")
        sys.exit(1)
        sys.exit(1)
