#!/usr/bin/env python3
import json

# Load the MCP configuration
with open('unified_mcp_config.json', 'r') as f:
    data = json.load(f)

servers = data['servers']
print(f'Total MCP servers: {len(servers)}')
print('\nAll MCP servers:')
for i, name in enumerate(sorted(servers.keys()), 1):
    enabled = servers[name].get('enabled', False)
    port = servers[name].get('port', 'N/A')
    print(f'  {i:2d}. {name:<50} (Port: {port}, Enabled: {enabled})')

# Count enabled servers
enabled_count = sum(1 for s in servers.values() if s.get('enabled', False))
print(f'\nEnabled servers: {enabled_count}')
print(f'Disabled servers: {len(servers) - enabled_count}')
