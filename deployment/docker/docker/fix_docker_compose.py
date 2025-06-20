#!/usr/bin/env python3
"""
Script to fix Docker Compose file issues:
1. Remove duplicate service definitions
2. Standardize network names to mcp-network
3. Ensure consistent entrypoint paths
4. Fix environment variable inconsistencies
"""

import re
import sys

def fix_docker_compose():
    """Fix the Docker Compose file by removing duplicates and standardizing configuration"""
    
    # Read the current file
    with open('docker-compose.mcp-servers.yml', 'r') as f:
        content = f.read()
    
    # Split into lines for processing
    lines = content.split('\n')
    
    # Track seen service names to avoid duplicates
    seen_services = set()
    fixed_lines = []
    skip_until_next_service = False
    current_service = None
    
    for i, line in enumerate(lines):
        # Check if this is a service definition
        if re.match(r'^  [a-zA-Z0-9-]+:', line):
            service_name = line.split(':')[0].strip()
            
            # Skip duplicate services
            if service_name in seen_services:
                print(f"Removing duplicate service: {service_name}")
                skip_until_next_service = True
                continue
            else:
                seen_services.add(service_name)
                current_service = service_name
                skip_until_next_service = False
        
        # Check for next service or section to stop skipping
        elif skip_until_next_service and (
            re.match(r'^  [a-zA-Z0-9-]+:', line) or 
            re.match(r'^[a-zA-Z]', line) or 
            line.strip() == ''
        ):
            skip_until_next_service = False
        
        # Skip lines that are part of duplicate services
        if skip_until_next_service:
            continue
        
        # Fix network references: change mcpnet to mcp-network
        if 'mcpnet' in line and 'mcp-network' not in line:
            line: str = line.replace('mcpnet', 'mcp-network')
            print(f"Fixed network reference in line: {line.strip()}")
        
        # Fix entrypoint paths: standardize to /app/docker/entrypoint.sh
        if 'entrypoints/mcp_server_entrypoint.sh' in line:
            line: str = line.replace('/app/docker/entrypoints/mcp_server_entrypoint.sh', '/app/docker/entrypoint.sh')
            print(f"Fixed entrypoint path in line: {line.strip()}")
        
        # Fix PostgreSQL connection strings to use consistent credentials
        if 'postgresql://postgres:password@' in line:
            line: str = line.replace('postgresql://postgres:password@', 'postgresql://mcp_admin:mcp_secure_2025@')
            print(f"Fixed PostgreSQL connection string")
        
        fixed_lines.append(line)
    
    # Write the fixed content
    fixed_content = '\n'.join(fixed_lines)
    
    # Remove any duplicate volume or network definitions at the end
    fixed_content = re.sub(r'\n(volumes|networks):\s*\n(.*?\n)*?(?=\n(volumes|networks):|$)', '', fixed_content, flags=re.MULTILINE)
    
    with open('docker-compose.mcp-servers.yml', 'w') as f:
        f.write(fixed_content)
    
    print("Docker Compose file has been fixed!")
    print(f"Total services found: {len(seen_services)}")
    print("Services:", sorted(seen_services))

if __name__ == "__main__":
    fix_docker_compose()
