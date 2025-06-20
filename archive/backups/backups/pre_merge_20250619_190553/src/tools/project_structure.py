#!/usr/bin/env python3
"""
Project Structure Organizer
Removes duplicates and organizes the flash loan arbitrage project
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Set

class ProjectOrganizer:
    """Organize and clean up the project structure"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.duplicates: Dict[str, List[Path]] = {}
        self.project_structure = {
            'contracts': ['FlashLoanArbitrage.sol', 'contract_abi.json'],
            'scripts': [
                'blockchain_transaction_fixer.py',
                'flash_loan_arbitrage_bot.py',
                'deploy_contract.py',
                'monitor_opportunities.py'
            ],
            'config': [
                'production_config.json',
                'deployed_contract_config.json',
                'network_config.json'
            ],
            'mcp_servers': [
                'mcp-coinbase-price-feed',
                'mcp-newsapi',
                'mcp-twitter',
                'mcp-taskmanager'
            ],
            'utils': [
                'gas_optimizer.py',
                'dex_interfaces.py',
                'token_manager.py'
            ],
            'tests': [
                'test_arbitrage.py',
                'test_transaction_fixer.py'
            ],
            'logs': [],
            'data': ['opportunities.json', 'transactions.json']
        }
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def find_duplicates(self) -> Dict[str, List[Path]]:
        """Find duplicate files in the project"""
        file_hashes = {}
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash in file_hashes:
                        if file_hash not in self.duplicates:
                            self.duplicates[file_hash] = [file_hashes[file_hash]]
                        self.duplicates[file_hash].append(file_path)
                    else:
                        file_hashes[file_hash] = file_path
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        return self.duplicates
    
    def remove_duplicates(self, keep_pattern: str = None):
        """Remove duplicate files, keeping one based on pattern"""
        removed_files = []
        
        for file_hash, file_list in self.duplicates.items():
            # Sort by path depth (keep files in root or main directories)
            file_list.sort(key=lambda x: Any: Any: len(x.parts))
            
            # Keep the first file (shortest path) or one matching pattern
            keep_file = file_list[0]
            if keep_pattern:
                for f in file_list:
                    if keep_pattern in str(f):
                        keep_file = f
                        break
            
            # Remove others
            for f in file_list:
                if f != keep_file:
                    try:
                        f.unlink()
                        removed_files.append(str(f))
                        print(f"Removed duplicate: {f}")
                    except Exception as e:
                        print(f"Error removing {f}: {e}")
        
        return removed_files
    
    def create_organized_structure(self):
        """Create organized directory structure"""
        for directory in self.project_structure.keys():
            dir_path = self.base_path / directory
            dir_path.mkdir(exist_ok=True)
            print(f"Created/verified directory: {directory}")
    
    def move_files_to_structure(self):
        """Move files to their appropriate directories"""
        moved_files = []
        
        # Define file mappings
        file_mappings = {
            '.sol': 'contracts',
            '_abi.json': 'contracts',
            'config.json': 'config',
            'deploy': 'scripts',
            'monitor': 'scripts',
            'bot.py': 'scripts',
            'fixer.py': 'scripts',
            'test_': 'tests',
            '.log': 'logs',
            'mcp-': 'mcp_servers'
        }
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and file_path.parent == self.base_path:
                moved = False
                for pattern, directory in file_mappings.items():
                    if pattern in file_path.name:
                        new_path = self.base_path / directory / file_path.name
                        try:
                            shutil.move(str(file_path), str(new_path))
                            moved_files.append((str(file_path), str(new_path)))
                            moved = True
                            break
                        except Exception as e:
                            print(f"Error moving {file_path}: {e}")
                
                if not moved and file_path.suffix == '.py':
                    # Move other Python files to utils
                    new_path = self.base_path / 'utils' / file_path.name
                    try:
                        shutil.move(str(file_path), str(new_path))
                        moved_files.append((str(file_path), str(new_path)))
                    except Exception as e:
                        print(f"Error moving {file_path}: {e}")
        
        return moved_files
    
    def create_main_entry_point(self):
        """Create main.py as the primary entry point"""
        main_content = '''#!/usr/bin/env python3
"""
Flash Loan Arbitrage Bot - Main Entry Point
Integrates all components with MCP servers for real-time operation
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

# Add project directories to path
project_root = Path(__file__).parent
sys.path.extend([
    str(project_root / 'scripts'),
    str(project_root / 'utils')
])

from blockchain_transaction_fixer import UnifiedTransactionFixer
from flash_loan_arbitrage_bot import FlashLoanArbitrageBot
from monitor_opportunities import OpportunityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MainApplication:
    """Main application orchestrator"""
    
    def __init__(self):
        self.config = self.load_config()
        self.bot = None
        self.monitor = None
        self.fixer = None
    
    def load_config(self) -> dict:
        """Load all configuration files"""
        config = {}
        config_dir = project_root / 'config'
        
        for config_file in config_dir.glob('*.json'):
            try:
                with open(config_file, 'r') as f:
                    config[config_file.stem] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading {config_file}: {e}")
        
        return config
    
    async def initialize_components(self):
        """Initialize all components"""
        try:
            # Initialize bot
            self.bot = FlashLoanArbitrageBot(
                self.config.get('production_config', {}),
                self.config.get('deployed_contract_config', {})
            )
            
            # Initialize monitor
            self.monitor = OpportunityMonitor(
                self.config.get('network_config', {})
            )
            
            # Initialize fixer
            self.fixer = UnifiedTransactionFixer(
                self.bot.web3,
                self.bot.account,
                self.config.get('production_config', {})
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    async def run(self):
        """Run the main application"""
        try:
            await self.initialize_components()
            
            # Start monitoring in background
            monitor_task = asyncio.create_task(self.monitor.start())
            
            # Start bot
            bot_task = asyncio.create_task(self.bot.run())
            
            # Wait for tasks
            await asyncio.gather(monitor_task, bot_task)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.bot:
            await self.bot.cleanup()
        if self.monitor:
            await self.monitor.cleanup()
        if self.fixer and hasattr(self.fixer, 'session'):
            await self.fixer.session.close()

if __name__ == "__main__":
    app = MainApplication()
    asyncio.run(app.run())
'''
        
        main_path = self.base_path / 'main.py'
        with open(main_path, 'w') as f:
            f.write(main_content)
        
        print(f"Created main entry point: {main_path}")
    
    def create_readme(self):
        """Create comprehensive README"""
        readme_content = '''# Flash Loan Arbitrage Bot

A sophisticated cryptocurrency arbitrage bot that leverages flash loans and integrates multiple MCP (Model Context Protocol) servers for real-time market data and decision making.

## Features

- **Flash Loan Integration**: Execute arbitrage without capital requirements
- **Multi-DEX Support**: QuickSwap, SushiSwap, and other Polygon DEXs
- **Real-Time Data**: Integration with MCP servers for:
  - Live price feeds (Coinbase)
  - News sentiment analysis
  - Social media monitoring (Twitter)
  - Task management and workflow
- **Transaction Optimization**: Automatic gas optimization and failure recovery
- **Risk Management**: Market condition analysis and timing optimization

## Project Structure

```
flash-loan-arbitrage/
├── main.py                 # Main entry point
├── contracts/              # Smart contracts and ABIs
├── scripts/                # Core bot scripts
├── config/                 # Configuration files
├── mcp_servers/           # MCP server integrations
├── utils/                 # Utility modules
├── tests/                 # Test files
├── logs/                  # Application logs
└── data/                  # Data storage
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   - Copy `.env.example` to `.env`
   - Add your private key and RPC endpoints

3. Deploy smart contract:
   ```bash
   python scripts/deploy_contract.py
   ```

4. Start MCP servers:
   ```bash
   # Start each MCP server in separate terminals
   cd mcp_servers/mcp-coinbase-price-feed && npm start
   cd mcp_servers/mcp-newsapi && npm start
   cd mcp_servers/mcp-twitter && npm start
   cd mcp_servers/mcp-taskmanager && npm start
   ```

5. Run the bot:
   ```bash
   python main.py
   ```

## Configuration

Edit configuration files in the `config/` directory:
- `production_config.json`: Main bot configuration
- `network_config.json`: Network and DEX settings
- `deployed_contract_config.json`: Contract addresses

## Safety Features

- Automatic gas estimation and optimization
- Transaction failure recovery
- Market condition monitoring
- Risk level assessment
- Slippage protection

## License

MIT License - see LICENSE file for details
'''
        
        readme_path = self.base_path / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print(f"Created README: {readme_path}")
    
    def organize_project(self):
        """Execute full project organization"""
        print("Starting project organization...")
        
        # Find and remove duplicates
        print("\n1. Finding duplicates...")
        duplicates = self.find_duplicates()
        print(f"Found {len(duplicates)} sets of duplicates")
        
        if duplicates:
            print("\n2. Removing duplicates...")
            removed = self.remove_duplicates()
            print(f"Removed {len(removed)} duplicate files")
        
        # Create organized structure
        print("\n3. Creating directory structure...")
        self.create_organized_structure()
        
        # Move files
        print("\n4. Moving files to appropriate directories...")
        moved = self.move_files_to_structure()
        print(f"Moved {len(moved)} files")
        
        # Create main entry point
        print("\n5. Creating main entry point...")
        self.create_main_entry_point()
        
        # Create README
        print("\n6. Creating README...")
        self.create_readme()
        
        print("\nProject organization complete!")

if __name__ == "__main__":
    organizer = ProjectOrganizer(r"c:\Users\Ratanshila\Documents\flash loan")
    organizer.organize_project()
