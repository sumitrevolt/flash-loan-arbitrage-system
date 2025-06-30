# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
import json
import socket
"""
Quick connectivity test for deployed services
"""

def test_port(host='localhost', port=None, timeout=3):
    """Test if a port is accepting connections"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result: str = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def main():
    print("[SEARCH] Quick Connectivity Test")
    print("=" * 50)
    
    # Test infrastructure
    infra_services = []
        ("PostgreSQL", 5432),
        ("Redis", 6379),
        ("RabbitMQ", 5672),
        ("RabbitMQ Management", 15672)
    
    
    # Test MCP servers (sample)
    mcp_services = []
        ("Flash Loan MCP", 4001),
        ("Web3 Provider MCP", 4002),
        ("DEX Price Server", 4003),
        ("Arbitrage Detector", 4004),
        ("GitHub MCP", 4008)
    
    
    # Test AI agents (sample)
    agent_services = []
        ("Coordinator Agent", 5001),
        ("Arbitrage Agent", 5002),
        ("Monitoring Agent", 5003)
    
    
    results = {}
    
    print("\n[METRICS] Infrastructure Services:")
    for name, port in infra_services:
        status = "[OK] READY" if test_port(port=port) else "[ERROR] DOWN"
        print(f"  {name} (:{port}) - {status}")
        results[name] = test_port(port=port)
    
    print("\n[SETUP] MCP Servers (Sample):")
    for name, port in mcp_services:
        status = "[OK] READY" if test_port(port=port) else "[ERROR] DOWN"
        print(f"  {name} (:{port}) - {status}")
        results[name] = test_port(port=port)
    
    print("\n🤖 AI Agents (Sample):")
    for name, port in agent_services:
        status = "[OK] READY" if test_port(port=port) else "[ERROR] DOWN"
        print(f"  {name} (:{port}) - {status}")
        results[name] = test_port(port=port)
    
    # Summary
    total_tested = len(results)
    ready_count = sum(1 for v in results.values() if v)
    
    print(f"\n[METRICS] Summary:")
    print(f"  Total Tested: {total_tested}")
    print(f"  Ready: {ready_count}")
    print(f"  Connectivity: {ready_count/total_tested*100:.1f}%")
    
    if ready_count >= total_tested * 0.8:  # 80% or better
        print(f"\n[CELEBRATE] SYSTEM STATUS: OPERATIONAL")
    else:
        print(f"\n[WARN]  SYSTEM STATUS: NEEDS ATTENTION")

if __name__ == "__main__":
    main()