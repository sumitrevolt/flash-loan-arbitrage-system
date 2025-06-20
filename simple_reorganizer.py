#!/usr/bin/env python3
"""
Simple Project Reorganizer
Organizes the flash loan arbitrage project files into logical groups
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_directories():
    """Create the new directory structure"""
    directories = [
        "01_core_system",
        "02_configuration", 
        "03_scripts_automation",
        "04_documentation",
        "05_data_logs",
        "06_deployment",
        "07_archive_backup"
    ]
    
    for dir_name in directories:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ Created directory: {dir_name}")

def organize_files():
    """Organize files into appropriate directories"""
    moves = []
    
    # Core system files (Python files related to core functionality)
    core_files = [
        "*arbitrage*.py", "*coordination*.py", "*mcp*.py", "*bridge*.py", 
        "*agent*.py", "*orchestrat*.py", "*launcher*.py", "*monitoring*.py",
        "*dashboard*.py", "*health*.py", "*revenue*.py", "*task*.py"
    ]
    
    # Configuration files
    config_files = [
        ".env*", "*.json", "requirements*.txt", "hardhat.config.js", 
        "docker-compose*.yml", "*.yml"
    ]
    
    # Scripts and automation
    script_files = [
        "*.ps1", "launch_*.py", "start_*.py", "setup_*.py", "run_*.py",
        "*clean*.py", "*organiz*.py", "*fix*.py", "test_*.py", "validate_*.py", 
        "verify_*.py", "show_*.py", "how_to_*.py"
    ]
    
    # Documentation
    doc_files = [
        "*.md", "*.txt"
    ]
    
    # Data and logs
    data_files = [
        "*.log", "*.db", "*report*.json"
    ]
    
    # Archive files
    archive_files = [
        "*.bak", "-y"
    ]
    
    # Move files based on patterns
    move_by_pattern("01_core_system", core_files, moves)
    move_by_pattern("02_configuration", config_files, moves)
    move_by_pattern("03_scripts_automation", script_files, moves)
    move_by_pattern("04_documentation", doc_files, moves)
    move_by_pattern("05_data_logs", data_files, moves)
    move_by_pattern("07_archive_backup", archive_files, moves)
    
    return moves

def move_by_pattern(target_dir, patterns, moves):
    """Move files matching patterns to target directory"""
    import fnmatch
    
    for file_path in Path(".").iterdir():
        if file_path.is_file():
            for pattern in patterns:
                if fnmatch.fnmatch(file_path.name.lower(), pattern.lower()):
                    try:
                        target_path = Path(target_dir) / file_path.name
                        if not target_path.exists():
                            shutil.move(str(file_path), str(target_path))
                            moves.append(f"{file_path.name} -> {target_dir}")
                            print(f"  Moved: {file_path.name} -> {target_dir}")
                            break
                    except Exception as e:
                        print(f"  Error moving {file_path.name}: {e}")

def move_directories():
    """Move specific directories to appropriate locations"""
    dir_moves = [
        ("mcp_servers", "01_core_system"),
        ("ai_agent", "01_core_system"),
        ("ai_agents", "01_core_system"),
        ("config", "02_configuration"),
        ("configs", "02_configuration"),
        ("docker-configs", "02_configuration"),
        ("scripts", "03_scripts_automation"),
        ("docs", "04_documentation"),
        ("logs", "05_data_logs"),
        ("cache", "05_data_logs"),
        ("training_data", "05_data_logs"),
        ("training_logs", "05_data_logs"),
        ("docker", "06_deployment"),
        ("containers", "06_deployment"),
        ("deployment", "06_deployment"),
        ("archive", "07_archive_backup"),
        ("backups", "07_archive_backup"),
        ("backup_duplicates", "07_archive_backup"),
        ("cleanup_backup", "07_archive_backup"),
        ("organized", "07_archive_backup"),
        ("organized_project", "07_archive_backup")
    ]
    
    moved_dirs = []
    for source_dir, target_dir in dir_moves:
        source_path = Path(source_dir)
        if source_path.exists() and source_path.is_dir():
            target_path = Path(target_dir) / source_dir
            try:
                if not target_path.exists():
                    shutil.move(str(source_path), str(target_path))
                    moved_dirs.append(f"{source_dir}/ -> {target_dir}")
                    print(f"  Moved directory: {source_dir} -> {target_dir}")
            except Exception as e:
                print(f"  Error moving directory {source_dir}: {e}")
    
    return moved_dirs

def create_readme_files():
    """Create README files for each organized directory"""
    readmes = {
        "01_core_system/README.md": """# Core System

This directory contains the main application source code:

- Flash loan arbitrage logic and strategies
- System coordination and orchestration  
- Model Context Protocol implementations
- AI agent implementations
- Monitoring and health checks
- Revenue and task management systems
""",
        
        "02_configuration/README.md": """# Configuration

This directory contains all configuration files:

- Environment variables (.env files)
- JSON configuration files
- Python package requirements
- Docker and container configurations
- Hardware configuration (hardhat.config.js)
""",
        
        "03_scripts_automation/README.md": """# Scripts and Automation

Automation and utility scripts:

- System launcher scripts (launch_*.py, start_*.py)
- PowerShell automation scripts (*.ps1)
- Setup and installation scripts
- Testing and validation scripts
- Maintenance and cleanup tools
""",
        
        "04_documentation/README.md": """# Documentation

Complete project documentation:

- User guides and tutorials
- System status and completion reports
- Implementation details and fixes
- README files and project documentation
""",
        
        "05_data_logs/README.md": """# Data and Logs

Runtime data, logs, and training materials:

- Application logs (*.log)
- Local databases (*.db)
- Training data and logs
- Cache directories
- System reports and analytics
""",
        
        "06_deployment/README.md": """# Deployment

Deployment configurations and containers:

- Docker containers and configurations
- Production deployment files
- Infrastructure as code
- Container orchestration
""",
        
        "07_archive_backup/README.md": """# Archive and Backups

Archived files, backups, and legacy code:

- System backups and cleanup backups
- Legacy files and old versions (*.bak)
- Previous organization attempts
- Historical data and reports
"""
    }
    
    for file_path, content in readmes.items():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Created: {file_path}")

def create_main_readme():
    """Create the main project README"""
    content = f"""# Flash Loan Arbitrage System

A comprehensive flash loan arbitrage system with AI agents, monitoring, and automated coordination.

## Project Structure

```
flash-loan/
├── 01_core_system/           # Core application code
├── 02_configuration/         # Configuration files
├── 03_scripts_automation/    # Scripts and automation
├── 04_documentation/         # Project documentation  
├── 05_data_logs/            # Data, logs, and training
├── 06_deployment/           # Deployment configurations
└── 07_archive_backup/       # Archive and backups
```

## Quick Start

1. Check `02_configuration/` for environment setup
2. Review `04_documentation/` for guides and status
3. Use scripts in `03_scripts_automation/` to launch systems
4. Monitor logs in `05_data_logs/`

## Reorganization

This project was reorganized on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for better structure and maintainability.

For detailed information about each component, see the README.md file in each directory.
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("✓ Created main README.md")

def main():
    print("🏗️  Simple Project Reorganizer")
    print("=" * 50)
    
    # Create directory structure
    print("\n📁 Creating directory structure...")
    create_directories()
    
    # Move files
    print("\n📄 Moving files...")
    file_moves = organize_files()
    
    # Move directories  
    print("\n📂 Moving directories...")
    dir_moves = move_directories()
    
    # Create documentation
    print("\n📋 Creating documentation...")
    create_readme_files()
    create_main_readme()
    
    # Summary
    total_moves = len(file_moves) + len(dir_moves)
    print(f"\n✅ Reorganization complete!")
    print(f"📁 Items moved: {total_moves}")
    print(f"📄 Files: {len(file_moves)}")
    print(f"📂 Directories: {len(dir_moves)}")
    
    # Create a simple report
    with open(f"reorganization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w") as f:
        f.write("Project Reorganization Summary\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total items moved: {total_moves}\n\n")
        f.write("File Moves:\n")
        for move in file_moves:
            f.write(f"  {move}\n")
        f.write("\nDirectory Moves:\n")
        for move in dir_moves:
            f.write(f"  {move}\n")
    
    print("📋 Summary saved to reorganization_summary_*.txt")

if __name__ == "__main__":
    main()
