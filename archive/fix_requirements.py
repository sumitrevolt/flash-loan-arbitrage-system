#!/usr/bin/env python3
"""
Fix Requirements Script - Add missing python-multipart dependency
"""

import os
import glob

def fix_mcp_requirements():
    """Add python-multipart to all MCP container requirements files"""
    
    containers_dir = r"c:\Users\Ratanshila\Documents\flash loan\containers"
    mcp_dirs = glob.glob(os.path.join(containers_dir, "mcp-*"))
    
    print(f"Found {len(mcp_dirs)} MCP container directories")
    
    for mcp_dir in mcp_dirs:
        requirements_file = os.path.join(mcp_dir, "requirements.txt")
        
        if os.path.exists(requirements_file):
            # Read current requirements
            with open(requirements_file, 'r') as f:
                current_reqs = f.read().strip()
            
            # Check if python-multipart is already present
            if 'python-multipart' not in current_reqs:
                # Add python-multipart
                updated_reqs = current_reqs + '\npython-multipart==0.0.6\n'
                
                # Write updated requirements
                with open(requirements_file, 'w') as f:
                    f.write(updated_reqs)
                
                print(f"✅ Updated {os.path.basename(mcp_dir)}/requirements.txt")
            else:
                print(f"⏭️  {os.path.basename(mcp_dir)}/requirements.txt already has python-multipart")
        else:
            print(f"❌ No requirements.txt found in {os.path.basename(mcp_dir)}")

def fix_orchestrator_requirements():
    """Also fix orchestrator requirements if needed"""
    
    orchestrator_req = r"c:\Users\Ratanshila\Documents\flash loan\containers\orchestrator\requirements.txt"
    
    if os.path.exists(orchestrator_req):
        with open(orchestrator_req, 'r') as f:
            current_reqs = f.read().strip()
        
        if 'python-multipart' not in current_reqs:
            updated_reqs = current_reqs + '\npython-multipart==0.0.6\n'
            
            with open(orchestrator_req, 'w') as f:
                f.write(updated_reqs)
            
            print("✅ Updated orchestrator/requirements.txt")
        else:
            print("⏭️  orchestrator/requirements.txt already has python-multipart")

if __name__ == "__main__":
    print("🔧 Fixing MCP container requirements...")
    fix_mcp_requirements()
    
    print("\n🔧 Fixing orchestrator requirements...")
    fix_orchestrator_requirements()
    
    print("\n✅ Requirements fix complete!")
    print("\n🐳 Next steps:")
    print("1. Rebuild the affected containers")
    print("2. Restart the docker-compose services")
