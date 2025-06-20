#!/usr/bin/env python3
"""
MCP Server Discovery and Analysis Tool
Identifies all functional MCP servers in the project for containerization
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Set

class MCPServerDiscovery:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.mcp_servers_path = self.base_path / "mcp_servers"
        self.discovered_servers = []
        
    def find_mcp_servers(self) -> List[Dict]:
        """Discover all MCP servers in the project"""
        print("🔍 Scanning for MCP servers...")
        
        # Define MCP server patterns
        server_patterns = [
            r"class.*MCPServer",
            r"@mcp\.server\(",
            r"mcp\.Server\(",
            r"from mcp import",
            r"import mcp",
            r"def main.*mcp",
            r"stdio_server\(",
            r"Server\(.*name.*\)"
        ]
        
        # Scan all directories
        for category_dir in self.mcp_servers_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                self._scan_directory(category_dir, category_dir.name)
        
        return self.discovered_servers
    
    def _scan_directory(self, directory: Path, category: str):
        """Scan a directory for MCP servers"""
        for file_path in directory.rglob("*.py"):
            if self._is_mcp_server(file_path):
                server_info = self._analyze_server(file_path, category)
                if server_info:
                    self.discovered_servers.append(server_info)
    
    def _is_mcp_server(self, file_path: Path) -> bool:
        """Check if a Python file is an MCP server"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Look for MCP patterns
            mcp_indicators = [
                'from mcp import',
                'import mcp',
                'mcp.Server',
                'MCPServer',
                'stdio_server',
                '@mcp.server',
                'class.*Server',
                'def main.*mcp'
            ]
            
            for pattern in mcp_indicators:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
                    
            return False
        except:
            return False
    
    def _analyze_server(self, file_path: Path, category: str) -> Dict:
        """Analyze an MCP server file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract server metadata
            server_name = self._extract_server_name(content, file_path.stem)
            server_port = self._extract_port(content)
            dependencies = self._extract_dependencies(file_path)
            tools = self._extract_tools(content)
            
            return {
                'name': server_name,
                'file_path': str(file_path.relative_to(self.base_path)),
                'category': category,
                'port': server_port,
                'dependencies': dependencies,
                'tools': tools,
                'working': self._check_if_working(file_path),
                'docker_ready': self._check_docker_ready(file_path)
            }
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            return None
    
    def _extract_server_name(self, content: str, fallback: str) -> str:
        """Extract server name from content"""
        patterns = [
            r'server_name\s*=\s*["\']([^"\']+)["\']',
            r'name\s*=\s*["\']([^"\']+)["\']',
            r'SERVER_NAME\s*=\s*["\']([^"\']+)["\']',
            r'class\s+(\w+Server)',
            r'def\s+(\w+_mcp_server)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Clean up fallback name
        name = fallback.replace('_mcp_server', '').replace('_server', '')
        return name.replace('_', '-')
    
    def _extract_port(self, content: str) -> int:
        """Extract port from content"""
        patterns = [
            r'port\s*=\s*(\d+)',
            r'PORT\s*=\s*(\d+)',
            r'listen.*:(\d+)',
            r'host.*:(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract Python dependencies"""
        deps = []
        
        # Check for requirements.txt in same directory
        req_file = file_path.parent / "requirements.txt"
        if req_file.exists():
            try:
                deps.extend(req_file.read_text().strip().split('\n'))
            except:
                pass
        
        # Extract from imports
        try:
            content = file_path.read_text()
            import_matches = re.findall(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
            
            # Filter to external packages
            external_packages = [
                pkg for pkg in set(import_matches) 
                if pkg not in ['os', 'sys', 'json', 'asyncio', 'logging', 'pathlib', 'typing']
                and not pkg.startswith('mcp_')
            ]
            deps.extend(external_packages)
        except:
            pass
        
        return list(set(deps))
    
    def _extract_tools(self, content: str) -> List[str]:
        """Extract MCP tools from content"""
        tools = []
        
        # Look for tool definitions
        tool_patterns = [
            r'@server\.tool\(\s*["\']([^"\']+)["\']',
            r'server\.add_tool\(\s*["\']([^"\']+)["\']',
            r'def\s+(\w+_tool)',
            r'Tool\(\s*name\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, content)
            tools.extend(matches)
        
        return list(set(tools))
    
    def _check_if_working(self, file_path: Path) -> bool:
        """Check if server is in working condition"""
        # Check filename indicators
        filename = file_path.name.lower()
        if 'working' in filename or 'enhanced' in filename or 'clean' in filename:
            return True
        
        # Check for common issues
        try:
            content = file_path.read_text()
            
            # Look for error indicators
            error_indicators = [
                'TODO', 'FIXME', 'BROKEN', 'NotImplemented',
                'raise NotImplementedError', 'pass  # TODO'
            ]
            
            for indicator in error_indicators:
                if indicator in content:
                    return False
            
            # Look for completion indicators
            if 'if __name__ == "__main__"' in content:
                return True
                
        except:
            pass
        
        return True  # Assume working unless proven otherwise
    
    def _check_docker_ready(self, file_path: Path) -> bool:
        """Check if server is ready for Docker containerization"""
        # Check for Dockerfile or docker configs
        docker_files = [
            file_path.parent / "Dockerfile",
            file_path.parent / "docker-compose.yml",
            file_path.parent / ".dockerignore"
        ]
        
        return any(f.exists() for f in docker_files)
    
    def generate_report(self) -> Dict:
        """Generate comprehensive discovery report"""
        servers = self.find_mcp_servers()
        
        # Categorize servers
        categories = {}
        working_servers = []
        total_tools = []
        
        for server in servers:
            category = server['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(server)
            
            if server['working']:
                working_servers.append(server)
            
            total_tools.extend(server['tools'])
        
        report = {
            'total_servers': len(servers),
            'working_servers': len(working_servers),
            'categories': categories,
            'servers': servers,
            'total_tools': len(set(total_tools)),
            'unique_tools': list(set(total_tools)),
            'docker_ready_count': sum(1 for s in servers if s['docker_ready'])
        }
        
        return report
    
    def print_summary(self, report: Dict):
        """Print discovery summary"""
        print("\n" + "="*60)
        print("🔍 MCP SERVER DISCOVERY REPORT")
        print("="*60)
        
        print(f"📊 Total Servers Found: {report['total_servers']}")
        print(f"✅ Working Servers: {report['working_servers']}")
        print(f"🐳 Docker Ready: {report['docker_ready_count']}")
        print(f"🛠️  Total Tools: {report['total_tools']}")
        
        print("\n📁 SERVERS BY CATEGORY:")
        for category, servers in report['categories'].items():
            print(f"  {category}: {len(servers)} servers")
            for server in servers:
                status = "✅" if server['working'] else "⚠️"
                docker = "🐳" if server['docker_ready'] else "📦"
                print(f"    {status}{docker} {server['name']} ({len(server['tools'])} tools)")
        
        print(f"\n🔧 AVAILABLE TOOLS ({len(report['unique_tools'])}):")
        for tool in sorted(report['unique_tools'])[:10]:  # Show first 10
            print(f"  • {tool}")
        if len(report['unique_tools']) > 10:
            print(f"  ... and {len(report['unique_tools']) - 10} more")

def main():
    discovery = MCPServerDiscovery()
    report = discovery.generate_report()
    discovery.print_summary(report)
    
    # Save detailed report
    output_file = Path("docker/mcp_discovery_report.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {output_file}")
    
    # Generate list of exactly 21 servers for containerization
    working_servers = [s for s in report['servers'] if s['working']]
    
    if len(working_servers) >= 21:
        selected_servers = working_servers[:21]
    else:
        # Fill with best available servers
        selected_servers = working_servers + [s for s in report['servers'] if not s['working']][:21-len(working_servers)]
    
    print(f"\n🎯 SELECTED 21 SERVERS FOR CONTAINERIZATION:")
    for i, server in enumerate(selected_servers[:21], 1):
        print(f"  {i:2d}. {server['name']} ({server['category']})")
    
    # Save selected servers list
    selected_file = Path("docker/selected_21_servers.json")
    with open(selected_file, 'w') as f:
        json.dump(selected_servers[:21], f, indent=2)
    
    print(f"\n💾 Selected servers saved to: {selected_file}")

if __name__ == "__main__":
    main()
