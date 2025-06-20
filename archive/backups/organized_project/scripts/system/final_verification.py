#!/usr/bin/env python3
"""
Flash Loan Arbitrage System - Final Setup and Verification
Verifies system integration and guides through final setup
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import platform

class SystemVerifier:
    """Verifies and sets up the complete flash loan arbitrage system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.errors = []
        self.warnings = []
        self.success_items = []
        
    def run_complete_verification(self):
        """Run complete system verification and setup"""
        print("🔍 Flash Loan Arbitrage System - Final Verification")
        print("=" * 70)
        
        # Step 1: Check prerequisites
        self.check_prerequisites()
        
        # Step 2: Verify project structure
        self.verify_project_structure()
        
        # Step 3: Check configuration files
        self.check_configuration_files()
        
        # Step 4: Verify dependencies
        self.verify_dependencies()
        
        # Step 5: Test database schema
        self.test_database_setup()
        
        # Step 6: Check smart contracts
        self.verify_smart_contracts()
        
        # Step 7: Test MCP servers
        self.test_mcp_servers()
        
        # Step 8: Verify frontend
        self.verify_frontend()
        
        # Step 9: Create final setup guide
        self.create_setup_guide()
        
        # Print final report
        self.print_final_report()
        
        return len(self.errors) == 0
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        print("\n📋 Checking Prerequisites...")
        
        # Check Python
        try:
            python_version = sys.version_info
            if python_version >= (3, 9):
                self.success_items.append(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            else:
                self.errors.append("❌ Python 3.9+ required")
        except Exception as e:
            self.errors.append(f"❌ Python check failed: {e}")
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                self.success_items.append(f"✅ Node.js {node_version}")
            else:
                self.errors.append("❌ Node.js not found")
        except Exception:
            self.errors.append("❌ Node.js not found")
        
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                npm_version = result.stdout.strip()
                self.success_items.append(f"✅ npm {npm_version}")
            else:
                self.warnings.append("⚠️ npm not found")
        except Exception:
            self.warnings.append("⚠️ npm not found")
        
        # Check Git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                git_version = result.stdout.strip()
                self.success_items.append(f"✅ {git_version}")
            else:
                self.warnings.append("⚠️ Git not found")
        except Exception:
            self.warnings.append("⚠️ Git not found")
    
    def verify_project_structure(self):
        """Verify project directory structure"""
        print("\n📁 Verifying Project Structure...")
        
        required_dirs = [
            "contracts",
            "src/core",
            "src/mcp_servers", 
            "frontend",
            "scripts/deployment",
            "scripts/setup",
            "tests",
            "database",
            "docs"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                self.success_items.append(f"✅ {dir_path}/")
            else:
                self.errors.append(f"❌ Missing directory: {dir_path}/")
        
        # Check required files
        required_files = [
            "contracts/FlashLoanArbitrageFixed.sol",
            "src/core/database.py",
            "frontend/dashboard.py",
            "hardhat.config.js",
            "package.json",
            "requirements.txt",
            "README.md",
            ".env.example"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.success_items.append(f"✅ {file_path}")
            else:
                self.errors.append(f"❌ Missing file: {file_path}")
    
    def check_configuration_files(self):
        """Check configuration files"""
        print("\n⚙️ Checking Configuration Files...")
        
        # Check .env.example
        env_example = self.project_root / ".env.example"
        if env_example.exists():
            with open(env_example, 'r') as f:
                env_content = f.read()
                
            required_vars = [
                "POLYGON_RPC_URL",
                "PRIVATE_KEY", 
                "DB_HOST",
                "DB_NAME",
                "MIN_PROFIT_THRESHOLD_USD",
                "TRADING_MODE"
            ]
            
            for var in required_vars:
                if var in env_content:
                    self.success_items.append(f"✅ Environment variable: {var}")
                else:
                    self.warnings.append(f"⚠️ Missing env var: {var}")
        else:
            self.errors.append("❌ .env.example not found")
        
        # Check package.json
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                required_scripts = ["build", "test", "deploy", "start"]
                for script in required_scripts:
                    if script in package_data.get("scripts", {}):
                        self.success_items.append(f"✅ npm script: {script}")
                    else:
                        self.warnings.append(f"⚠️ Missing npm script: {script}")
            except Exception as e:
                self.errors.append(f"❌ Invalid package.json: {e}")
    
    def verify_dependencies(self):
        """Verify project dependencies"""
        print("\n📦 Verifying Dependencies...")
        
        # Check Python requirements
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            self.success_items.append("✅ requirements.txt found")
            
            # Try to check if packages are installed
            try:
                import web3
                self.success_items.append("✅ web3.py installed")
            except ImportError:
                self.warnings.append("⚠️ web3.py not installed - run: pip install -r requirements.txt")
            
            try:
                import fastapi
                self.success_items.append("✅ FastAPI installed")
            except ImportError:
                self.warnings.append("⚠️ FastAPI not installed - run: pip install -r requirements.txt")
        else:
            self.errors.append("❌ requirements.txt not found")
        
        # Check Node.js dependencies
        package_json = self.project_root / "package.json"
        node_modules = self.project_root / "node_modules"
        
        if package_json.exists():
            if node_modules.exists():
                self.success_items.append("✅ Node.js dependencies installed")
            else:
                self.warnings.append("⚠️ Node.js dependencies not installed - run: npm install")
    
    def test_database_setup(self):
        """Test database setup"""
        print("\n🗄️ Testing Database Setup...")
        
        schema_file = self.project_root / "database" / "schema.sql"
        if schema_file.exists():
            self.success_items.append("✅ Database schema found")
            
            # Check schema content
            with open(schema_file, 'r') as f:
                schema_content = f.read()
            
            required_tables = [
                "CREATE TABLE IF NOT EXISTS tokens",
                "CREATE TABLE IF NOT EXISTS dexes",
                "CREATE TABLE IF NOT EXISTS trades",
                "CREATE TABLE IF NOT EXISTS arbitrage_opportunities"
            ]
            
            for table in required_tables:
                if table in schema_content:
                    self.success_items.append(f"✅ {table.split()[-1]} table defined")
                else:
                    self.errors.append(f"❌ Missing table: {table.split()[-1]}")
        else:
            self.errors.append("❌ Database schema not found")
    
    def verify_smart_contracts(self):
        """Verify smart contracts"""
        print("\n📜 Verifying Smart Contracts...")
        
        contract_file = self.project_root / "contracts" / "FlashLoanArbitrageFixed.sol"
        if contract_file.exists():
            self.success_items.append("✅ FlashLoanArbitrageFixed.sol found")
            
            with open(contract_file, 'r') as f:
                contract_content = f.read()
            
            required_features = [
                "contract FlashLoanArbitrageFixed",
                "function executeArbitrage",
                "function executeOperation",
                "nonReentrant",
                "whenNotPaused"
            ]
            
            for feature in required_features:
                if feature in contract_content:
                    self.success_items.append(f"✅ Contract feature: {feature}")
                else:
                    self.errors.append(f"❌ Missing contract feature: {feature}")
        else:
            self.errors.append("❌ Main contract file not found")
        
        # Check hardhat config
        hardhat_config = self.project_root / "hardhat.config.js"
        if hardhat_config.exists():
            self.success_items.append("✅ Hardhat configuration found")
        else:
            self.errors.append("❌ Hardhat configuration missing")
    
    def test_mcp_servers(self):
        """Test MCP server setup"""
        print("\n🔧 Testing MCP Servers...")
        
        mcp_dir = self.project_root / "src" / "mcp_servers"
        if mcp_dir.exists():
            self.success_items.append("✅ MCP servers directory found")
            
            # Check for coordinator
            if (mcp_dir / "coordinator.py").exists():
                self.success_items.append("✅ MCP coordinator found")
            else:
                self.warnings.append("⚠️ MCP coordinator not found")
            
            # Check for price feed server
            if (mcp_dir / "price_feed_server.py").exists():
                self.success_items.append("✅ Price feed server found")
            else:
                self.warnings.append("⚠️ Price feed server not found")
        else:
            self.errors.append("❌ MCP servers directory missing")
    
    def verify_frontend(self):
        """Verify frontend setup"""
        print("\n🖥️ Verifying Frontend...")
        
        frontend_dir = self.project_root / "frontend"
        if frontend_dir.exists():
            self.success_items.append("✅ Frontend directory found")
            
            # Check dashboard
            if (frontend_dir / "dashboard.py").exists():
                self.success_items.append("✅ Dashboard backend found")
            else:
                self.errors.append("❌ Dashboard backend missing")
            
            # Check templates
            templates_dir = frontend_dir / "templates"
            if templates_dir.exists():
                if (templates_dir / "dashboard.html").exists():
                    self.success_items.append("✅ Dashboard template found")
                else:
                    self.errors.append("❌ Dashboard template missing")
            else:
                self.errors.append("❌ Templates directory missing")
        else:
            self.errors.append("❌ Frontend directory missing")
    
    def create_setup_guide(self):
        """Create final setup guide"""
        print("\n📋 Creating Setup Guide...")
        
        setup_guide = f"""# 🚀 Flash Loan Arbitrage System - Final Setup Guide

## Prerequisites ✅
{chr(10).join(self.success_items[:4])}

## Quick Start

### 1. Environment Setup
```bash
cd organized_project
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies  
npm install
```

### 3. Database Setup
```bash
# Setup PostgreSQL database
npm run db:setup
```

### 4. Smart Contract Deployment

**Testnet (Mumbai) - RECOMMENDED FIRST:**
```bash
npm run deploy:testnet
npm run verify
npm run setup
```

**Mainnet (Polygon) - PRODUCTION:**
```bash
npm run deploy
npm run verify
npm run setup
```

### 5. Start the System

**Development Mode:**
```bash
./scripts/system/start_system.sh development
```

**Production Mode:**
```bash
./scripts/system/start_system.sh production
```

### 6. Access the Dashboard
Open your browser to: http://localhost:8000

## Configuration Guide

### Essential Environment Variables

```bash
# Trading Configuration
TRADING_MODE=simulation          # Use 'simulation' for testing
MIN_PROFIT_THRESHOLD_USD=5.0
MAX_TRADE_AMOUNT_USD=1000.0     # Start small!

# Network Settings
POLYGON_RPC_URL=https://polygon-rpc.com
PRIVATE_KEY=your_private_key_here

# Database
DB_HOST=localhost
DB_NAME=flash_loan_arbitrage
DB_USER=postgres
DB_PASSWORD=your_secure_password
```

### Security Checklist

- [ ] Use a dedicated wallet for arbitrage
- [ ] Test thoroughly on Mumbai testnet first
- [ ] Start with small trade amounts
- [ ] Monitor gas costs carefully
- [ ] Never commit private keys to git
- [ ] Use strong database passwords
- [ ] Enable circuit breakers

## System Architecture

```
Flash Loan Arbitrage System
├── Smart Contract (Polygon)
│   └── FlashLoanArbitrageFixed.sol
├── Price Monitoring
│   └── MCP Price Feed Servers
├── Arbitrage Engine
│   └── Opportunity Detection & Execution
├── Web Dashboard
│   └── Real-time Monitoring
└── Database
    └── Trade History & Analytics
```

## Monitoring & Maintenance

### Health Checks
```bash
# System health
npm run health

# View logs
npm run logs

# Monitor performance
npm run monitor
```

### Backup & Recovery
```bash
# Backup system
npm run backup

# Database backup
pg_dump flash_loan_arbitrage > backup.sql
```

## Troubleshooting

### Common Issues

1. **"Transaction failed" errors:**
   - Check gas price settings
   - Verify token balances
   - Check DEX liquidity

2. **"Circuit breaker triggered":**
   - Reset with: npm run reset-circuit-breaker
   - Review failed transactions

3. **Database connection errors:**
   - Verify PostgreSQL is running
   - Check connection settings in .env

4. **RPC errors:**
   - Try different RPC endpoint
   - Check network connectivity

### Support Resources

- Documentation: `docs/`
- Database Schema: `database/schema.sql`
- API Reference: http://localhost:8000/docs
- Logs: `logs/flash_loan_arbitrage.log`

## Performance Optimization

### Recommended Settings

```bash
# High-performance RPC endpoints
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY

# Optimal trading parameters
MIN_PROFIT_THRESHOLD_USD=10.0
MAX_GAS_PRICE_GWEI=50
SLIPPAGE_TOLERANCE_PERCENT=2.0
```

### Scaling Considerations

- Use multiple RPC endpoints for redundancy
- Implement Redis caching for price feeds
- Consider dedicated database server
- Monitor and optimize gas usage

---

**⚠️ Risk Disclaimer:**
Flash loan arbitrage involves significant risks. Only use funds you can afford to lose. This software is provided as-is for educational purposes.

**🎯 Ready to Start?**
Begin with testnet deployment and simulation mode to familiarize yourself with the system before going live.
"""
        
        setup_file = self.project_root / "FINAL_SETUP_GUIDE.md"
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(setup_guide)
        
        self.success_items.append("✅ Final setup guide created")
    
    def print_final_report(self):
        """Print final verification report"""
        print("\n" + "=" * 70)
        print("📊 FINAL VERIFICATION REPORT")
        print("=" * 70)
        
        # Success items
        if self.success_items:
            print(f"\n✅ SUCCESS ({len(self.success_items)} items):")
            for item in self.success_items:
                print(f"  {item}")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)} items):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        # Errors
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)} items):")
            for error in self.errors:
                print(f"  {error}")
        
        # Overall status
        print("\n" + "=" * 70)
        if len(self.errors) == 0:
            print("🎉 SYSTEM VERIFICATION PASSED!")
            print("\n🚀 Your Flash Loan Arbitrage System is ready!")
            print("\n📋 Next Steps:")
            print("1. Review FINAL_SETUP_GUIDE.md")
            print("2. Configure your .env file")
            print("3. Deploy to Mumbai testnet first")
            print("4. Start with simulation mode")
            print("5. Monitor performance carefully")
        else:
            print("❌ SYSTEM VERIFICATION FAILED!")
            print(f"\n🔧 Please fix {len(self.errors)} error(s) before proceeding.")
        
        print("=" * 70)

def main():
    """Main verification function"""
    verifier = SystemVerifier()
    success = verifier.run_complete_verification()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
