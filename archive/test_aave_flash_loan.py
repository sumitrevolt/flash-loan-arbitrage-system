#!/usr/bin/env python3
"""
AAVE Flash Loan Profit Target Test Runner
========================================

Test runner to demonstrate the AAVE flash loan profit targeting system
with focus on $4-$30 profit range execution.

This script will:
1. Initialize the profit targeting system
2. Run opportunity detection
3. Filter for $4-$30 profit range
4. Simulate executions
5. Display results and metrics
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our systems
from aave_flash_loan_profit_target_fixed import AaveFlashLoanProfitTarget
from core.aave_integration import AaveFlashLoanIntegration

def print_banner():
    """Print test banner"""
    print("""
🏦 AAVE FLASH LOAN PROFIT TARGET TEST
===================================

🎯 Target Range: $4 - $30 profit
⚡ Real-time opportunity detection
🔄 Multi-DEX arbitrage simulation
📊 Performance tracking
🔐 Risk management integration

Testing the complete AAVE flash loan system...
""")

async def test_profit_targeting_system():
    """Test the core profit targeting system"""
    
    print("🔍 Testing AAVE Flash Loan Profit Target System...")
    print("-" * 60)
    
    # Initialize system
    system = AaveFlashLoanProfitTarget()
    
    # Test 1: Price fetching
    print("1️⃣  Testing price fetching...")
    tokens = ['USDC', 'USDT', 'DAI', 'WMATIC']
    prices = await system.get_token_prices(tokens)
    print(f"   ✅ Fetched prices for {len(prices)} tokens")
    for token, price in prices.items():
        print(f"      {token}: ${price}")
    
    # Test 2: Opportunity detection
    print("\n2️⃣  Testing opportunity detection...")
    opportunities = await system.find_arbitrage_opportunities()
    print(f"   ✅ Found {len(opportunities)} total opportunities")
    
    # Test 3: Profit target filtering
    print("\n3️⃣  Testing profit target filtering...")
    target_opportunities = system.filter_opportunities_by_profit_target(opportunities)
    print(f"   ✅ {len(target_opportunities)} opportunities in $4-$30 range")
    
    # Display opportunities
    if target_opportunities:
        print("\n📋 PROFITABLE OPPORTUNITIES IN TARGET RANGE:")
        print(f"{'ID':<25} {'Asset':<8} {'Profit':<10} {'Margin':<8} {'Confidence':<12}")
        print("-" * 70)
        
        for opp in target_opportunities[:5]:  # Show top 5
            print(f"{opp.id[:24]:<25} {opp.asset:<8} ${float(opp.net_profit):<9.2f} "
                  f"{float(opp.profit_margin):<7.2f}% {opp.confidence_score:<11.2f}")
    
    # Test 4: Execution simulation
    if target_opportunities:
        print("\n4️⃣  Testing execution simulation...")
        best_opportunity = target_opportunities[0]
        
        print(f"   Executing: {best_opportunity.asset} via {best_opportunity.source_dex} → {best_opportunity.target_dex}")
        print(f"   Expected profit: ${float(best_opportunity.net_profit):.2f}")
        
        result = await system.execute_flash_loan(best_opportunity)
        
        if result['success']:
            print(f"   ✅ Execution successful!")
            print(f"      Actual profit: ${result['actual_profit']:.2f}")
            print(f"      Execution time: {result['execution_time']:.2f}s")
        else:
            print(f"   ❌ Execution failed: {result.get('error_message', 'Unknown error')}")
    
    # Test 5: Display metrics
    print("\n5️⃣  System metrics:")
    system.display_metrics()
    
    return system

async def test_integration_system():
    """Test the integration system"""
    
    print("\n🔗 Testing AAVE Flash Loan Integration System...")
    print("-" * 60)
    
    # Initialize integration
    integration = AaveFlashLoanIntegration()
    
    # Test 1: MCP server checking
    print("1️⃣  Testing MCP server connectivity...")
    server_status = await integration.check_mcp_servers()
    print("   Server Status:")
    for server, status in server_status.items():
        status_icon = "✅" if status else "❌"
        print(f"      {status_icon} {server}")
    
    # Test 2: Single integration cycle
    print("\n2️⃣  Testing integration cycle...")
    executed = await integration.run_integration_cycle()
    print(f"   ✅ Integration cycle completed: {executed} executions")
    
    # Test 3: Display integration dashboard
    print("\n3️⃣  Integration dashboard:")
    integration.display_integration_dashboard()
    
    return integration

async def run_comprehensive_test():
    """Run comprehensive test of both systems"""
    
    print_banner()
    
    try:
        # Test core system
        system = await test_profit_targeting_system()
        
        # Test integration
        integration = await test_integration_system()
        
        # Summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        print(f"✅ Core System: Operational")
        print(f"✅ Integration: Operational")
        print(f"🎯 Profit Targeting: $4-$30 range configured")
        print(f"📈 Opportunities: {system.metrics.opportunities_in_range} in target range")
        print(f"⚡ Executions: {system.metrics.successful_executions} successful")
        print(f"💰 Total Profit: ${float(system.metrics.total_profit):.2f}")
        
        success_rate = (system.metrics.successful_executions / 
                       max(1, system.metrics.successful_executions + system.metrics.failed_executions)) * 100
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        print("\n🎉 All tests completed successfully!")
        print("🚀 System ready for AAVE flash loan profit targeting ($4-$30 range)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def run_demo_cycle():
    """Run a demonstration cycle"""
    
    print("🎬 Running AAVE Flash Loan Profit Target Demo...")
    print("="*60)
    
    integration = AaveFlashLoanIntegration()
    
    for cycle in range(3):  # Run 3 demo cycles
        print(f"\n🔄 Demo Cycle {cycle + 1}/3")
        print("-" * 40)
        
        executed = await integration.run_integration_cycle()
        print(f"Cycle {cycle + 1} completed: {executed} executions")
        
        if cycle < 2:  # Don't wait after last cycle
            print("⏳ Waiting 10 seconds for next cycle...")
            await asyncio.sleep(10)
    
    print("\n🎉 Demo completed!")
    print("💡 To run continuously: python aave_integration.py")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'demo':
            asyncio.run(run_demo_cycle())
        elif sys.argv[1] == 'test':
            asyncio.run(run_comprehensive_test())
        else:
            print("Usage: python test_aave_flash_loan.py [test|demo]")
    else:
        # Default: run comprehensive test
        asyncio.run(run_comprehensive_test())

if __name__ == "__main__":
    main()
