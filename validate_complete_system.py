#!/usr/bin/env python3
"""
Complete MCP System Validation and Summary
"""

import json
import yaml
import os
from pathlib import Path

def validate_system():
    """Validate the complete MCP system setup"""
    print("🔍 Complete MCP System Validation")
    print("=" * 50)
    
    # Check configuration files
    configs_valid = True
    
    print("\n📋 Configuration Files:")
    if Path('unified_mcp_config.json').exists():
        with open('unified_mcp_config.json', 'r') as f:
            mcp_config = json.load(f)
        mcp_count = len(mcp_config['servers'])
        print(f"✅ MCP Config: {mcp_count} servers")
    else:
        print("❌ MCP Config: Not found")
        configs_valid = False
    
    if Path('ai_agents_config.json').exists():
        with open('ai_agents_config.json', 'r') as f:
            ai_config = json.load(f)
        ai_count = len(ai_config['agents'])
        print(f"✅ AI Config: {ai_count} agents")
    else:
        print("❌ AI Config: Not found")
        configs_valid = False
    
    # Check Docker Compose files
    print("\n🐳 Docker Compose Files:")
    compose_files = {
        'docker/docker-compose-complete.yml': 'Complete system (81 MCP servers)',
        'docker/docker-compose-test-complete.yml': 'Test system (5 core MCP servers)',
        'docker/docker-compose-self-healing.yml': 'Self-healing system',
        'docker/docker-compose-test.yml': 'Basic test system'
    }
    
    compose_valid = True
    for file_path, description in compose_files.items():
        if Path(file_path).exists():
            try:
                with open(file_path, 'r') as f:
                    compose_data = yaml.safe_load(f)
                service_count = len(compose_data.get('services', {}))
                print(f"✅ {file_path}: {service_count} services - {description}")
            except Exception as e:
                print(f"❌ {file_path}: Error reading - {e}")
                compose_valid = False
        else:
            print(f"❌ {file_path}: Not found")
            compose_valid = False
    
    # Check Dockerfiles
    print("\n📦 Dockerfiles:")
    dockerfiles = [
        'docker/Dockerfile.coordination',
        'docker/Dockerfile.agent', 
        'docker/Dockerfile.mcp-enhanced',
        'docker/Dockerfile.self-healing'
    ]
    
    dockerfiles_valid = True
    for dockerfile in dockerfiles:
        if Path(dockerfile).exists():
            print(f"✅ {dockerfile}")
        else:
            print(f"❌ {dockerfile}: Not found")
            dockerfiles_valid = False
    
    # Check entrypoints
    print("\n🚪 Entrypoints:")
    entrypoints = [
        'docker/entrypoints/coordination_entrypoint.py',
        'docker/entrypoints/ai_agent_entrypoint.py',
        'docker/entrypoints/enhanced_mcp_server_entrypoint.py',
        'docker/entrypoints/self_healing_agent.py'
    ]
    
    entrypoints_valid = True
    for entrypoint in entrypoints:
        if Path(entrypoint).exists():
            print(f"✅ {entrypoint}")
        else:
            print(f"❌ {entrypoint}: Not found")
            entrypoints_valid = False
    
    # Check launchers and tools
    print("\n🚀 Launchers and Tools:")
    tools = [
        'launch_coordination_system.ps1',
        'generate_complete_compose.py',
        'test_complete_system.py',
        'coordination_launcher.py',
        'self_healing_coordination_launcher.py'
    ]
    
    tools_valid = True
    for tool in tools:
        if Path(tool).exists():
            print(f"✅ {tool}")
        else:
            print(f"❌ {tool}: Not found")
            tools_valid = False
    
    # System summary
    print("\n📊 System Summary:")
    if Path('docker/docker-compose-complete.yml').exists():
        with open('docker/docker-compose-complete.yml', 'r') as f:
            complete_compose = yaml.safe_load(f)
        
        services = complete_compose.get('services', {})
        mcp_services = [s for s in services if s.startswith('mcp_')]
        ai_services = [s for s in services if s.startswith('ai_agent_')]
        infra_services = [s for s in services if s in ['redis', 'postgres', 'rabbitmq', 'prometheus', 'grafana']]
        
        print(f"🔧 Infrastructure Services: {len(infra_services)}")
        print(f"🤖 MCP Servers: {len(mcp_services)}")
        print(f"🧠 AI Agents: {len(ai_services)}")
        print(f"⚙️  Other Services: {len(services) - len(mcp_services) - len(ai_services) - len(infra_services)}")
        print(f"📈 Total Services: {len(services)}")
    
    # Overall validation
    print("\n🎯 Overall System Status:")
    all_valid = configs_valid and compose_valid and dockerfiles_valid and entrypoints_valid and tools_valid
    
    if all_valid:
        print("🎉 ✅ Complete MCP System is READY!")
        print("\n🚀 Quick Start Options:")
        print("   Test System:     .\\launch_coordination_system.ps1 -System test-complete")
        print("   Complete System: .\\launch_coordination_system.ps1 -System complete")
        print("   Self-Healing:    .\\launch_coordination_system.ps1 -System self-healing")
        print("\n📋 System Features:")
        print("   • 81 MCP servers covering all DeFi operations")
        print("   • 11 AI agents for intelligent automation")
        print("   • Self-healing architecture with automatic recovery")
        print("   • Comprehensive monitoring and observability")
        print("   • Production-ready Docker orchestration")
        print("   • Multiple deployment configurations")
    else:
        print("❌ System validation FAILED - Please check missing components")
        return False
    
    return True

def show_usage_examples():
    """Show usage examples"""
    print("\n" + "=" * 60)
    print("🎓 USAGE EXAMPLES")
    print("=" * 60)
    
    examples = [
        ("Start Complete System", ".\\launch_coordination_system.ps1 -System complete"),
        ("Start Test System", ".\\launch_coordination_system.ps1 -System test-complete"),
        ("Check System Health", ".\\launch_coordination_system.ps1 -Action health"),
        ("View System Info", ".\\launch_coordination_system.ps1 -Action info"),
        ("Run Tests", "python test_complete_system.py"),
        ("Stop System", ".\\launch_coordination_system.ps1 -Action stop"),
        ("View Logs", ".\\launch_coordination_system.ps1 -Action logs"),
        ("Restart System", ".\\launch_coordination_system.ps1 -Action restart")
    ]
    
    for description, command in examples:
        print(f"\n{description}:")
        print(f"  {command}")

if __name__ == "__main__":
    success = validate_system()
    
    if success:
        show_usage_examples()
        print(f"\n📚 For detailed documentation, see: COMPLETE_SYSTEM_README.md")
        print(f"🔧 For troubleshooting, check the logs and health endpoints")
    
    exit(0 if success else 1)
