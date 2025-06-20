#!/usr/bin/env python3
"""
Flash Loan Project - Complete Setup with MaxKB Integration
Includes MaxKB knowledge base setup for project documentation and AI assistance
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"   ✅ Docker found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ Docker not found. Please install Docker first.")
        return False

def setup_maxkb():
    """Setup MaxKB knowledge base container"""
    print("\n🧠 Setting up MaxKB Knowledge Base:")
    
    if not check_docker():
        return False
    
    # Check if MaxKB container already exists
    try:
        result = subprocess.run(["docker", "ps", "-a", "--filter", "name=maxkb"], 
                              capture_output=True, text=True)
        if "maxkb" in result.stdout:
            print("   ⚠️  MaxKB container already exists")
            choice = input("   Remove existing container and recreate? (y/N): ").lower()
            if choice == 'y':
                print("   🗑️  Removing existing MaxKB container...")
                subprocess.run(["docker", "rm", "-f", "maxkb"], check=True)
            else:
                print("   ✅ Using existing MaxKB container")
                return True
    except subprocess.CalledProcessError:
        pass
    
    print("   🚀 Starting MaxKB container...")
    
    # Create MaxKB data directories
    maxkb_data_dir = Path.home() / ".maxkb"
    python_packages_dir = Path.home() / ".python-packages"
    
    maxkb_data_dir.mkdir(exist_ok=True)
    python_packages_dir.mkdir(exist_ok=True)
    
    print(f"   📁 Data directory: {maxkb_data_dir}")
    print(f"   📁 Python packages: {python_packages_dir}")
    
    # Run MaxKB container
    docker_cmd = [
        "docker", "run", "-d",
        "--name=maxkb",
        "--restart=always",
        "-p", "8080:8080",
        "-v", f"{maxkb_data_dir}:/var/lib/postgresql/data",
        "-v", f"{python_packages_dir}:/opt/maxkb/app/sandbox/python-packages",
        "1panel/maxkb"
    ]
    
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, check=True)
        print(f"   ✅ MaxKB container started: {result.stdout.strip()}")
        
        print("   ⏳ Waiting for MaxKB to initialize...")
        time.sleep(10)
        
        print("\n   🌐 MaxKB Access Information:")
        print("   URL: http://localhost:8080")
        print("   Username: admin")
        print("   Password: MaxKB@123..")
        print("   📝 Note: It may take a few minutes to fully initialize")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to start MaxKB: {e.stderr}")
        return False

def setup_flash_loan_project():
    """Setup the organized flash loan project"""
    
    # Set project root
    project_root = Path(__file__).parent.parent
    print(f"🚀 Setting up organized Flash Loan project at: {project_root}")
    
    # Check if we're in the right directory
    if not (project_root / "src").exists():
        print("❌ Error: Not in organized project directory")
        print("   Please run this script from organized_project/scripts/")
        return False
    
    print("\n📁 Project Structure Verification:")
    
    # Verify key directories exist
    key_dirs = [
        "src/core",
        "src/mcp_servers", 
        "src/coordination",
        "src/agents",
        "src/integrations",
        "config/environments",
        "config/docker",
        "scripts",
        "docs",
        "tests"
    ]
    
    for dir_path in key_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            file_count = len(list(full_path.glob("*")))
            print(f"   ✅ {dir_path}/ ({file_count} files)")
        else:
            print(f"   ❌ {dir_path}/ (missing)")
    
    # Check for requirements file
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        print(f"   ✅ requirements.txt ({req_file.stat().st_size} bytes)")
    else:
        print("   ❌ requirements.txt (missing)")
    
    return True

def create_maxkb_integration_guide():
    """Create integration guide for MaxKB with Flash Loan project"""
    
    project_root = Path(__file__).parent.parent
    guide_path = project_root / "docs" / "MAXKB_INTEGRATION_GUIDE.md"
    
    guide_content = '''# MaxKB Integration with Flash Loan Project

## Overview
MaxKB is integrated as a knowledge base system to enhance the AI capabilities of the flash loan arbitrage system.

## Access Information
- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: MaxKB@123..

## Integration Benefits

### 1. Enhanced Documentation Management
- Centralized storage of project documentation
- AI-powered search and retrieval
- Version-controlled knowledge base

### 2. AI Agent Enhancement
- Improved context for MCP servers
- Better decision-making for arbitrage strategies
- Historical data analysis and learning

### 3. System Monitoring
- Knowledge base for system logs and performance data
- AI-assisted troubleshooting
- Pattern recognition for optimization

## Setup Commands

### Start MaxKB
```bash
docker run -d --name=maxkb --restart=always -p 8080:8080 \
  -v ~/.maxkb:/var/lib/postgresql/data \
  -v ~/.python-packages:/opt/maxkb/app/sandbox/python-packages \
  1panel/maxkb
```

### Stop MaxKB
```bash
docker stop maxkb
```

### Remove MaxKB
```bash
docker rm -f maxkb
```

## Integration with Flash Loan System

### 1. Document Upload
Upload the following to MaxKB:
- Project documentation from `docs/`
- Configuration guides
- API documentation
- Trading strategies

### 2. MCP Server Integration
Configure MCP servers to query MaxKB for:
- Historical arbitrage patterns
- Risk assessment data
- Market analysis insights

### 3. AI Agent Training
Use MaxKB as training data source for:
- Decision-making algorithms
- Risk management strategies
- Performance optimization

## Usage Workflow

1. **Access MaxKB Web Interface**
   - Navigate to http://localhost:8080
   - Login with admin credentials

2. **Upload Project Documentation**
   - Upload all markdown files from `docs/`
   - Create knowledge bases for different components

3. **Configure AI Agents**
   - Point MCP servers to MaxKB API
   - Set up automated knowledge retrieval

4. **Monitor and Optimize**
   - Use MaxKB analytics for system optimization
   - Continuously update knowledge base

## API Integration

MaxKB provides REST API endpoints that can be integrated with the flash loan system:

```python
import requests

# Example API usage
def query_maxkb(question):
    response = requests.post(
        "http://localhost:8080/api/chat",
        json={"question": question},
        headers={"Authorization": "Bearer YOUR_API_KEY"}
    )
    return response.json()
```

## Best Practices

1. **Regular Updates**: Keep knowledge base updated with latest strategies
2. **Version Control**: Track changes in knowledge base content
3. **Security**: Secure MaxKB with proper authentication
4. **Backup**: Regular backups of MaxKB data directory
5. **Monitoring**: Monitor MaxKB performance and resource usage

## Troubleshooting

### Common Issues
- **Port conflicts**: Ensure port 8080 is available
- **Docker issues**: Check Docker service status
- **Memory**: MaxKB requires adequate system memory

### Logs
```bash
docker logs maxkb
```

## Next Steps

1. Access MaxKB web interface
2. Upload project documentation
3. Configure knowledge bases
4. Integrate with MCP servers
5. Test AI-enhanced arbitrage strategies
'''
    
    try:
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print(f"   ✅ Created MaxKB integration guide: {guide_path}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to create integration guide: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 80)
    print("🏗️  FLASH LOAN PROJECT + MAXKB - COMPLETE SETUP")  
    print("=" * 80)
    
    try:
        # Setup flash loan project
        flash_loan_success = setup_flash_loan_project()
        
        # Setup MaxKB
        maxkb_success = setup_maxkb()
        
        # Create integration guide
        guide_success = create_maxkb_integration_guide()
        
        print("\n" + "=" * 80)
        print("📋 SETUP SUMMARY")
        print("=" * 80)
        
        print(f"Flash Loan Project: {'✅ Ready' if flash_loan_success else '❌ Failed'}")
        print(f"MaxKB Knowledge Base: {'✅ Running' if maxkb_success else '❌ Failed'}")
        print(f"Integration Guide: {'✅ Created' if guide_success else '❌ Failed'}")
        
        if flash_loan_success and maxkb_success:
            print("\n🎉 COMPLETE SETUP SUCCESSFUL!")
            print("\n🔧 Next Steps:")
            print("   1. Install Python dependencies:")
            print("      pip install -r requirements.txt")
            print()
            print("   2. Access MaxKB Knowledge Base:")
            print("      URL: http://localhost:8080")
            print("      Username: admin")
            print("      Password: MaxKB@123..")
            print()
            print("   3. Upload project documentation to MaxKB")
            print()
            print("   4. Launch Flash Loan system:")
            print("      python scripts/enhanced_system_launcher.py")
            print()
            print("   5. Review integration guide:")
            print("      docs/MAXKB_INTEGRATION_GUIDE.md")
            
        else:
            print("\n⚠️  PARTIAL SETUP - Some components failed")
            print("   Check error messages above and retry failed components")
            
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
