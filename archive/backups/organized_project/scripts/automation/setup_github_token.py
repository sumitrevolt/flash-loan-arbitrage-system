#!/usr/bin/env python3
"""
GitHub Token Setup Helper
Interactive guide to set up GitHub token for Models API
"""

import os
import webbrowser
from pathlib import Path

def create_env_file():
    """Create a .env file for the GitHub token"""
    env_file = Path(".env")
    
    print("📝 Creating .env file...")
    
    token = input("\nEnter your GitHub token (starts with 'ghp_' or 'github_pat_'): ").strip()
    
    if not token:
        print("❌ No token provided")
        return False
    
    if not (token.startswith('ghp_') or token.startswith('github_pat_')):
        print("⚠️  Warning: Token doesn't look like a valid GitHub token")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
    
    # Write to .env file
    with open(env_file, 'w') as f:
        f.write(f"GITHUB_TOKEN={token}\n")
    
    print(f"✅ Token saved to {env_file}")
    
    # Also set in current session
    os.environ['GITHUB_TOKEN'] = token
    print("✅ Token set in current session")
    
    return True

def open_github_token_page():
    """Open GitHub token creation page"""
    print("🌐 Opening GitHub token creation page...")
    webbrowser.open("https://github.com/settings/personal-access-tokens/tokens")
    print("   The page should open in your browser")

def show_detailed_instructions():
    """Show detailed step-by-step instructions"""
    print("""
🔧 DETAILED GITHUB TOKEN SETUP
================================

Step 1: Create the Token
1. Go to: https://github.com/settings/personal-access-tokens/tokens
2. Click "Generate new token" (blue button)
3. Choose "Fine-grained personal access token" (recommended)
4. Fill in the form:
   - Token name: "GitHub Models API" (or any name you prefer)
   - Expiration: 90 days (or your preference)
   - Resource owner: Select your account
   - Repository access: Select "All repositories" or specific repos

Step 2: Set Permissions
5. Under "Account permissions", find and enable:
   ✅ Models: "Read" access (REQUIRED for GitHub Models API)
   ✅ Metadata: "Read" access (basic access)
   
Step 3: Generate and Copy
6. Click "Generate token" at the bottom
7. COPY THE TOKEN IMMEDIATELY (you won't see it again!)
   - Token will start with 'github_pat_' or 'ghp_'
   - Example: github_pat_11ABCDEFG123456789...

Step 4: Set the Token
8. Run this script and paste your token when prompted
   OR
9. Set it manually in PowerShell:
   $env:GITHUB_TOKEN='your_actual_token_here'

⚠️  IMPORTANT NOTES:
• You need a GitHub Copilot subscription for Models API
• Keep your token secure - treat it like a password
• If you lose the token, you'll need to generate a new one
• Some organizations may restrict GitHub Models access
""")

def main():
    """Main setup function"""
    print("🏦 GitHub Token Setup Helper")
    print("=" * 30)
    
    # Check current token
    current_token = os.getenv('GITHUB_TOKEN')
    if current_token and current_token != 'your_actual_token_here':
        print(f"✅ Current token found: {current_token[:12]}...")
        replace = input("Replace current token? (y/n): ").strip().lower()
        if replace != 'y':
            print("✅ Keeping current token")
            return
    
    print("\nChoose an option:")
    print("1. Show detailed instructions")
    print("2. Open GitHub token page in browser")
    print("3. Enter token directly")
    print("4. Exit")
    
    choice = input("\nYour choice (1-4): ").strip()
    
    if choice == '1':
        show_detailed_instructions()
        input("\nPress Enter when you have your token ready...")
        if create_env_file():
            print("\n🎉 Token setup complete!")
            print("Run the diagnostic script again to verify:")
            print("python diagnose_github_token.py")
    
    elif choice == '2':
        open_github_token_page()
        input("\nPress Enter when you have your token ready...")
        if create_env_file():
            print("\n🎉 Token setup complete!")
            print("Run the diagnostic script again to verify:")
            print("python diagnose_github_token.py")
    
    elif choice == '3':
        if create_env_file():
            print("\n🎉 Token setup complete!")
            print("Run the diagnostic script again to verify:")
            print("python diagnose_github_token.py")
    
    elif choice == '4':
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
