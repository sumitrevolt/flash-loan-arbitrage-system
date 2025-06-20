#!/usr/bin/env python3
"""
Wallet Setup and Security Guide
===============================

This guide helps you safely set up your wallet for AAVE flash loan live trading.

SECURITY WARNINGS:
- Never share your private key
- Use a dedicated wallet for trading (not your main wallet)
- Start with small amounts for testing
- Keep backups of your private key in a secure location
"""

def print_wallet_setup_guide():
    """Print comprehensive wallet setup instructions"""
    print("=" * 80)
    print("🔐 WALLET SETUP FOR LIVE TRADING")
    print("=" * 80)
    
    print("\n📋 STEP 1: CREATE OR USE EXISTING WALLET")
    print("-" * 50)
    print("Option A - MetaMask:")
    print("1. Install MetaMask browser extension")
    print("2. Create new wallet or import existing")
    print("3. Switch to Polygon network")
    print("4. Export private key: Settings → Security & Privacy → Reveal Private Key")
    print()
    
    print("Option B - Generate New Wallet (Python):")
    print("1. Run: python -c \"from web3 import Web3; acc = Web3().eth.account.create(); print(f'Address: {acc.address}\\nPrivate Key: {acc.key.hex()}')\"")
    print("2. Save both address and private key securely")
    print("3. Add network to MetaMask using the address")
    print()
    
    print("📋 STEP 2: FUND WALLET")
    print("-" * 50)
    print("Minimum Requirements:")
    print("• 0.5 MATIC - for gas fees and operations")
    print("• Optional: Small amounts of tokens for testing")
    print("  - 10-50 USDC")
    print("  - 10-50 USDT") 
    print("  - 0.01-0.1 WETH")
    print()
    
    print("Funding Options:")
    print("• Transfer from existing wallet")
    print("• Buy on exchange and withdraw to Polygon")
    print("• Use Polygon bridge from Ethereum")
    print("• Use a faucet (testnet only)")
    print()
    
    print("📋 STEP 3: ADD PRIVATE KEY TO .env FILE")
    print("-" * 50)
    print("1. Open .env file in text editor")
    print("2. Add line: PRIVATE_KEY=your_private_key_here")
    print("3. Example: PRIVATE_KEY=0x1234567890abcdef...")
    print("4. Save file")
    print()
    
    print("⚠️  SECURITY CHECKLIST:")
    print("-" * 50)
    print("✓ Never commit .env file to version control")
    print("✓ Use a dedicated trading wallet (not main wallet)")
    print("✓ Start with small amounts for testing")
    print("✓ Keep private key backup in secure location")
    print("✓ Monitor all transactions in block explorer")
    print("✓ Set reasonable gas price limits")
    print()
    
    print("📋 STEP 4: VERIFY SETUP")
    print("-" * 50)
    print("Run: python prepare_live_mode.py")
    print("This will verify:")
    print("• Private key is set")
    print("• Wallet is funded")
    print("• Network connection works")
    print("• All systems are ready")
    print()
    
    print("📋 STEP 5: EXECUTE TOKEN APPROVALS")
    print("-" * 50)
    print("1. Run: python execute_token_approvals.py")
    print("2. Review approval summary")
    print("3. Confirm with 'YES' when ready")
    print("4. Wait for all 20 approvals to complete")
    print("5. Verify all transactions succeeded")
    print()
    
    print("📋 STEP 6: START LIVE TRADING")
    print("-" * 50)
    print("1. Run: python demo_master_system.py")
    print("2. Monitor initial operations")
    print("3. Watch for profitable opportunities")
    print("4. Track performance and adjust settings")
    print()
    
    print("🚨 EMERGENCY PROCEDURES:")
    print("-" * 50)
    print("If something goes wrong:")
    print("• Stop all scripts (Ctrl+C)")
    print("• Check wallet balance and transactions")
    print("• Review logs for errors")
    print("• Disable live mode: ENABLE_REAL_EXECUTION=false")
    print("• Contact support with error details")

def generate_new_wallet():
    """Generate a new wallet for testing"""
    try:
        from web3 import Web3
        
        print("\n🔄 GENERATING NEW WALLET")
        print("-" * 50)
        
        w3 = Web3()
        account = w3.eth.account.create()
        
        print(f"✅ New wallet created!")
        print(f"📍 Address: {account.address}")
        print(f"🔐 Private Key: {account.key.hex()}")
        print()
        print("⚠️  IMPORTANT:")
        print("• Save both address and private key securely")
        print("• Never share the private key")
        print("• Add to .env file as: PRIVATE_KEY=" + account.key.hex())
        print("• Fund with MATIC before live trading")
        
    except Exception as e:
        print(f"❌ Error generating wallet: {e}")
        print("Install web3 with: pip install web3")

def main():
    """Main function"""
    print_wallet_setup_guide()
    
    print("\n🎯 QUICK ACTIONS:")
    print("1. Generate new wallet (g)")
    print("2. Just show guide (any other key)")
    
    choice = input("\nEnter choice: ").lower()
    
    if choice == 'g':
        generate_new_wallet()

if __name__ == "__main__":
    main()
