#!/usr/bin/env python3
"""
Update Docker Compose files to use enhanced MCP Dockerfile
"""
import os
import re

def update_compose_file(filepath):
    """Update a Docker Compose file to use enhanced MCP Dockerfile"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace MCP Dockerfile references
        updated_content = content.replace(
            'dockerfile: docker/Dockerfile.mcp',
            'dockerfile: docker/Dockerfile.mcp-enhanced'
        )
        
        # Write back if changes were made
        if updated_content != content:
            with open(filepath, 'w') as f:
                f.write(updated_content)
            print(f"✅ Updated {filepath}")
            return True
        else:
            print(f"ℹ️  No changes needed for {filepath}")
            return True
            
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return False

def main():
    """Update all Docker Compose files"""
    compose_files = [
        'docker/docker-compose-complete.yml',
        'docker/docker-compose-test-complete.yml',
        'docker/docker-compose-self-healing.yml',
        'docker/docker-compose-test.yml'
    ]
    
    print("Updating Docker Compose files to use enhanced MCP Dockerfile...")
    
    success_count = 0
    for filepath in compose_files:
        if update_compose_file(filepath):
            success_count += 1
    
    print(f"\nUpdated {success_count}/{len(compose_files)} files successfully.")
    
    if success_count == len(compose_files):
        print("🎉 All Docker Compose files updated successfully!")
        return True
    else:
        print("⚠️  Some files could not be updated.")
        return False

if __name__ == "__main__":
    main()
