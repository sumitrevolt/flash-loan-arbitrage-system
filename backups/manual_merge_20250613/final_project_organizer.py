#!/usr/bin/env python3
"""
Final Project Organizer
Creates a clean, professional project structure for the Flash Loan Arbitrage Bot
Following the comprehensive duplicate merge
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class FinalProjectOrganizer:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.backup_dir = self.root_dir / "backups" / f"pre_organization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.organization_log = []
        self.moved_files = []
        
        # Define the target project structure
        self.target_structure = {
            "app/": {
                "description": "Main application entry points",
                "files": [
                    "optimized_arbitrage_bot_v2.py",
                    "dex_integrations.py",
                    "config.py"
                ]
            },
            "core/": {
                "description": "Core business logic",
                "subdirs": {
                    "arbitrage/": ["*arbitrage*.py"],
                    "dex/": ["*dex*.py"],
                    "flash_loan/": ["*flash*loan*.py"],
                    "pricing/": ["*price*.py", "*pricing*.py"],
                    "revenue/": ["*revenue*.py"],
                    "coordinators/": ["*coordinator*.py"]
                }
            },
            "infrastructure/": {
                "description": "Infrastructure and services",
                "subdirs": {
                    "mcp_servers/": ["existing structure"],
                    "docker/": ["existing structure"],
                    "monitoring/": ["*monitor*.py", "*status*.py", "*check*.py"]
                }
            },
            "integrations/": {
                "description": "External integrations",
                "subdirs": {
                    "dex/": ["*dex*.py"],
                    "blockchain/": ["*blockchain*.py", "*web3*.py"],
                    "apis/": ["*api*.py"]
                }
            },
            "interfaces/": {
                "description": "User interfaces",
                "subdirs": {
                    "web/": ["*dashboard*.py", "*web*.py", "*.html", "*.css", "*.js"],
                    "cli/": ["*cli*.py", "*console*.py"]
                }
            },
            "utilities/": {
                "description": "Utility functions and tools",
                "subdirs": {
                    "tools/": ["*tool*.py", "*utility*.py", "*util*.py"],
                    "helpers/": ["*helper*.py"],
                    "validators/": ["*valid*.py", "*verify*.py"]
                }
            },
            "config/": {
                "description": "Configuration files",
                "files": ["*.json", "*.ini", "*.env*", "*config*.py"]
            },
            "data/": {
                "description": "Data files and cache",
                "subdirs": {
                    "cache/": [],
                    "logs/": [],
                    "abi/": ["*.json"]
                }
            },
            "tests/": {
                "description": "Test files",
                "files": ["*test*.py", "test_*.py"]
            },
            "docs/": {
                "description": "Documentation",
                "files": ["*.md", "*.txt", "*.rst"]
            },
            "scripts/": {
                "description": "Standalone scripts",
                "files": ["*script*.py", "*launcher*.py", "*.sh", "*.bat", "*.ps1"]
            },
            "archive/": {
                "description": "Archived and backup files",
                "files": ["existing structure"]
            }
        }
    
    def create_backup(self):
        """Create backup before reorganization"""
        print(f"Creating backup in {self.backup_dir}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup key files that will be moved
        key_files = [
            "optimized_arbitrage_bot_v2.py",
            "dex_integrations.py", 
            "config.py",
            "*.json",
            "*.md"
        ]
        
        for pattern in key_files:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file():
                    backup_path = self.backup_dir / file_path.name
                    shutil.copy2(file_path, backup_path)
                    print(f"  Backed up: {file_path.name}")
    
    def create_directory_structure(self):
        """Create the target directory structure"""
        print("\nCreating directory structure...")
        
        for dir_name, config in self.target_structure.items():
            dir_path = self.root_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"  Created: {dir_name}")
            
            # Create subdirectories
            if "subdirs" in config:
                for subdir_name in config["subdirs"]:
                    subdir_path = dir_path / subdir_name
                    subdir_path.mkdir(exist_ok=True)
                    
                    # Create __init__.py for Python packages
                    if subdir_name.endswith("/"):
                        init_file = subdir_path / "__init__.py"
                        if not init_file.exists():
                            init_file.write_text("# Auto-generated __init__.py\n")
                    
                    print(f"    Created: {dir_name}{subdir_name}")
    
    def organize_files(self):
        """Organize files into the new structure"""
        print("\nOrganizing files...")
        
        # Core application files
        self._move_files_to_app()
        
        # Core business logic
        self._organize_core_files()
        
        # Configuration files
        self._organize_config_files()
        
        # Documentation
        self._organize_documentation()
        
        # Interface files
        self._organize_interfaces()
        
        # Utility files
        self._organize_utilities()
        
        # Scripts and launchers
        self._organize_scripts()
    
    def _move_files_to_app(self):
        """Move main application files to app/ directory"""
        app_files = [
            "optimized_arbitrage_bot_v2.py",
            "dex_integrations.py",
            "config.py"
        ]
        
        for filename in app_files:
            src_path = self.root_dir / filename
            if src_path.exists():
                dst_path = self.root_dir / "app" / filename
                shutil.move(str(src_path), str(dst_path))
                self.moved_files.append(f"{filename} -> app/{filename}")
                print(f"  Moved: {filename} -> app/")
    
    def _organize_core_files(self):
        """Organize core business logic files"""
        # Files already in core/ stay there, but organize better
        core_path = self.root_dir / "core"
        
        # Move any root-level core files
        core_patterns = [
            ("*revenue*.py", "revenue/"),
            ("*coordinator*.py", "coordinators/"),
            ("*flash*loan*.py", "flash_loan/"),
            ("*price*.py", "pricing/")
        ]
        
        for pattern, subdir in core_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    dst_dir = core_path / subdir
                    dst_dir.mkdir(exist_ok=True)
                    dst_path = dst_dir / file_path.name
                    shutil.move(str(file_path), str(dst_path))
                    self.moved_files.append(f"{file_path.name} -> core/{subdir}")
                    print(f"  Moved: {file_path.name} -> core/{subdir}")
    
    def _organize_config_files(self):
        """Organize configuration files"""
        config_patterns = ["*.json", "*.ini", ".env*"]
        config_dir = self.root_dir / "config"
        
        for pattern in config_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    # Skip some special files
                    if file_path.name in ["package.json", "package-lock.json"]:
                        continue
                    
                    dst_path = config_dir / file_path.name
                    shutil.move(str(file_path), str(dst_path))
                    self.moved_files.append(f"{file_path.name} -> config/")
                    print(f"  Moved: {file_path.name} -> config/")
    
    def _organize_documentation(self):
        """Organize documentation files"""
        doc_patterns = ["*.md", "*.txt", "*.rst"]
        docs_dir = self.root_dir / "docs"
        
        for pattern in doc_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    # Skip some special files
                    if file_path.name.lower() in ["readme.md", "license", "license.txt"]:
                        continue
                    
                    dst_path = docs_dir / file_path.name
                    shutil.move(str(file_path), str(dst_path))
                    self.moved_files.append(f"{file_path.name} -> docs/")
                    print(f"  Moved: {file_path.name} -> docs/")
    
    def _organize_interfaces(self):
        """Organize interface files"""
        interface_patterns = [
            ("*dashboard*.py", "web/"),
            ("*dashboard*.html", "web/"),
            ("*.html", "web/"),
            ("*.css", "web/"),
            ("*.js", "web/"),
            ("*cli*.py", "cli/"),
            ("*console*.py", "cli/")
        ]
        
        interfaces_dir = self.root_dir / "interfaces"
        
        for pattern, subdir in interface_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    dst_dir = interfaces_dir / subdir
                    dst_dir.mkdir(exist_ok=True)
                    dst_path = dst_dir / file_path.name
                    shutil.move(str(file_path), str(dst_path))
                    self.moved_files.append(f"{file_path.name} -> interfaces/{subdir}")
                    print(f"  Moved: {file_path.name} -> interfaces/{subdir}")
    
    def _organize_utilities(self):
        """Organize utility files"""
        utility_patterns = [
            ("*tool*.py", "tools/"),
            ("*utility*.py", "tools/"),
            ("*util*.py", "tools/"),
            ("*helper*.py", "helpers/"),
            ("*valid*.py", "validators/"),
            ("*verify*.py", "validators/"),
            ("*test*.py", "../tests/"),
            ("test_*.py", "../tests/")
        ]
        
        utilities_dir = self.root_dir / "utilities"
        
        for pattern, subdir in utility_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    if subdir.startswith("../"):
                        # Move to tests directory
                        dst_dir = self.root_dir / subdir[3:]
                        dst_dir.mkdir(exist_ok=True)
                        dst_path = dst_dir / file_path.name
                        move_location = subdir[3:]
                    else:
                        dst_dir = utilities_dir / subdir
                        dst_dir.mkdir(exist_ok=True)
                        dst_path = dst_dir / file_path.name
                        move_location = f"utilities/{subdir}"
                    
                    shutil.move(str(file_path), str(dst_path))
                    self.moved_files.append(f"{file_path.name} -> {move_location}")
                    print(f"  Moved: {file_path.name} -> {move_location}")
    
    def _organize_scripts(self):
        """Organize script files"""
        script_patterns = ["*.sh", "*.bat", "*.ps1", "*launcher*.py", "*script*.py"]
        scripts_dir = self.root_dir / "scripts"
        
        for pattern in script_patterns:
            matches = list(self.root_dir.glob(pattern))
            for file_path in matches:
                if file_path.is_file() and file_path.parent == self.root_dir:
                    dst_path = scripts_dir / file_path.name
                    shutil.move(str(file_path), str(dst_path))
                    self.moved_files.append(f"{file_path.name} -> scripts/")
                    print(f"  Moved: {file_path.name} -> scripts/")
    
    def create_main_readme(self):
        """Create a comprehensive README for the organized project"""
        readme_content = f"""# Flash Loan Arbitrage Bot

**Professional DeFi arbitrage system with comprehensive MCP integration**

## 🚀 Quick Start

```bash
# Run the main arbitrage bot
python app/optimized_arbitrage_bot_v2.py

# Configure the system
python app/config.py
```

## 📁 Project Structure

```
flash-loan-arbitrage-bot/
├── app/                    # Main application entry points
│   ├── optimized_arbitrage_bot_v2.py  # Main bot
│   ├── dex_integrations.py           # DEX connections
│   └── config.py                     # Configuration
├── core/                   # Core business logic
│   ├── arbitrage/         # Arbitrage strategies
│   ├── coordinators/      # System coordinators
│   ├── dex/              # DEX integrations
│   ├── flash_loan/       # Flash loan logic
│   ├── pricing/          # Price calculations
│   └── revenue/          # Revenue generation
├── infrastructure/        # Infrastructure services
│   ├── mcp_servers/      # MCP server implementations
│   ├── docker/           # Docker configurations
│   └── monitoring/       # System monitoring
├── integrations/          # External integrations
│   ├── dex/             # DEX API integrations
│   ├── blockchain/      # Blockchain connections
│   └── apis/            # External APIs
├── interfaces/            # User interfaces
│   ├── web/             # Web dashboard
│   └── cli/             # Command line tools
├── utilities/             # Utility functions
│   ├── tools/           # Development tools
│   ├── helpers/         # Helper functions
│   └── validators/      # Validation utilities
├── config/               # Configuration files
├── data/                 # Data and cache
├── tests/                # Test files
├── docs/                 # Documentation
├── scripts/              # Standalone scripts
└── archive/              # Archived files
```

## 🔧 Core Features

- **Real-time Arbitrage**: Automated arbitrage opportunity detection
- **Multi-DEX Support**: Integration with major DEXs
- **Flash Loan Integration**: Aave flash loan support
- **MCP Coordination**: Advanced MCP server orchestration
- **Risk Management**: Comprehensive risk assessment
- **Revenue Optimization**: Intelligent profit maximization

## 🛠 Technology Stack

- **Python 3.8+**: Core application
- **Web3.py**: Blockchain interaction
- **Asyncio**: Asynchronous processing
- **MCP Protocol**: Server coordination
- **Docker**: Containerization
- **Grafana**: Monitoring and analytics

## 📊 MCP Servers

The system includes specialized MCP servers for:

- **Blockchain Integration**: EVM, Matic, Foundry
- **AI Integration**: Context7, Copilot enhancement
- **Data Providers**: Price oracles, DEX data
- **Execution**: Contract execution, transaction optimization
- **Risk Management**: Risk assessment and mitigation
- **Monitoring**: System health and performance

## 🔐 Security Features

- Comprehensive input validation
- Transaction simulation before execution
- Risk-based position sizing
- Multi-layer security checks
- Automated error recovery

## 📈 Performance

- Real-time price monitoring
- Sub-second arbitrage detection
- Optimized gas usage
- Intelligent slippage protection

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start MCP Servers**:
   ```bash
   python infrastructure/mcp_servers/orchestration/unified_mcp_coordinator.py
   ```

4. **Run the Bot**:
   ```bash
   python app/optimized_arbitrage_bot_v2.py
   ```

## 📚 Documentation

- [Setup Guide](docs/SETUP.md)
- [Configuration](docs/CONFIGURATION.md)
- [MCP Integration](docs/MCP_INTEGRATION.md)
- [API Reference](docs/API.md)

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for contribution guidelines.

## 📄 License

See [LICENSE](LICENSE) for license information.

---

**Organization completed on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Files organized:** {len(self.moved_files)}
**Structure optimized for:** Professional development and deployment
"""
        
        readme_path = self.root_dir / "README.md"
        readme_path.write_text(readme_content)
        print(f"  Created: README.md")
    
    def generate_organization_report(self):
        """Generate detailed organization report"""
        report = {
            'organization_timestamp': datetime.now().isoformat(),
            'backup_location': str(self.backup_dir),
            'summary': {
                'directories_created': len(self.target_structure),
                'files_moved': len(self.moved_files),
                'structure_type': 'professional_modular'
            },
            'moved_files': self.moved_files,
            'target_structure': self.target_structure,
            'organization_log': self.organization_log
        }
        
        # Save detailed report
        with open('FINAL_ORGANIZATION_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create summary
        summary = f"""# FINAL PROJECT ORGANIZATION SUMMARY

**Organization completed at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Directories created:** {len(self.target_structure)}
- **Files moved:** {len(self.moved_files)}
- **Backup location:** {self.backup_dir}
- **Structure type:** Professional modular architecture

## Key Improvements
- ✅ Clean separation of concerns
- ✅ Logical directory hierarchy
- ✅ Professional project structure
- ✅ Easy navigation and maintenance
- ✅ Scalable architecture

## Directory Structure
"""
        
        for dir_name, config in self.target_structure.items():
            summary += f"- **{dir_name}**: {config['description']}\n"
        
        summary += f"""
## Moved Files
"""
        
        for move_info in self.moved_files[:20]:  # Show first 20
            summary += f"- {move_info}\n"
        
        if len(self.moved_files) > 20:
            summary += f"- ... and {len(self.moved_files) - 20} more files\n"
        
        summary += f"""
## Next Steps
1. Update import statements in moved files
2. Update configuration paths
3. Test all functionality
4. Update documentation

This organization creates a professional, maintainable project structure.
"""
        
        with open('FINAL_ORGANIZATION_SUMMARY.md', 'w') as f:
            f.write(summary)
        
        return report
    
    def run_organization(self):
        """Run the complete organization process"""
        print("Starting final project organization...")
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Create directory structure
            self.create_directory_structure()
            
            # Step 3: Organize files
            self.organize_files()
            
            # Step 4: Create main README
            self.create_main_readme()
            
            # Step 5: Generate report
            report = self.generate_organization_report()
            
            print(f"\n{'='*60}")
            print("PROJECT ORGANIZATION COMPLETED SUCCESSFULLY")
            print(f"{'='*60}")
            print(f"Directories created: {len(self.target_structure)}")
            print(f"Files organized: {len(self.moved_files)}")
            print(f"Backup location: {self.backup_dir}")
            print(f"Report: FINAL_ORGANIZATION_REPORT.json")
            print(f"Summary: FINAL_ORGANIZATION_SUMMARY.md")
            print(f"Updated README: README.md")
            
            return report
            
        except Exception as e:
            print(f"Error during organization: {e}")
            print(f"Check backup directory for safety: {self.backup_dir}")
            raise

def main():
    organizer = FinalProjectOrganizer()
    return organizer.run_organization()

if __name__ == "__main__":
    main()
