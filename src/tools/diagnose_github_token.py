#!/usr/bin/env python3
"""
GitHub Token Diagnostic Tool
Helps diagnose GitHub token issues and permissions
"""

import os
import requests
import json
from datetime import datetime

def check_github_token():
    """Check GitHub token validity and permissions"""
    print("🔍 GitHub Token Diagnostic")
    print("=" * 30)
    
    # Check if token exists
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment variables")
        print("\n💡 To set your GitHub token:")
        print("   Windows PowerShell:")
        print("   $env:GITHUB_TOKEN='your_token_here'")
        print("   ")
        print("   Or create a .env file with:")
        print("   GITHUB_TOKEN=your_token_here")
        return False
    
    print(f"✅ GITHUB_TOKEN found: {github_token[:12]}...")
    
    # Test basic GitHub API access
    print("\n🔧 Testing Basic GitHub API Access...")
    try:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get("https://api.github.com/user", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub API Access: OK")
            print(f"   User: {user_data.get('login', 'Unknown')}")
            print(f"   Name: {user_data.get('name', 'Not set')}")
        else:
            print(f"❌ GitHub API Access Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ GitHub API test failed: {str(e)}")
        return False
    
    # Test GitHub Models API specifically
    print("\n🤖 Testing GitHub Models API Access...")
    try:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        # Test with a simple request
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user", 
                    "content": "Hello, can you respond with 'GitHub Models API is working'?"
                }
            ],
            "max_tokens": 20,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result: str = response.json()
            content = result["choices"][0]["message"]["content"]
            print("✅ GitHub Models API: Working!")
            print(f"   Response: {content}")
            return True
        else:
            print(f"❌ GitHub Models API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw Error: {response.text}")
            
            # Provide specific guidance based on error
            if response.status_code == 401:
                print("\n💡 Token Permission Issue:")
                print("   Your token may not have 'models' permission")
                print("   1. Go to: https://github.com/settings/personal-access-tokens/tokens")
                print("   2. Edit your token or create a new one")
                print("   3. Ensure 'models' permission is selected")
            elif response.status_code == 403:
                print("\n💡 Access Issue:")
                print("   GitHub Models might not be available for your account")
                print("   1. Check if you have GitHub Copilot subscription")
                print("   2. Verify GitHub Models is enabled for your organization")
            
            return False
            
    except Exception as e:
        print(f"❌ GitHub Models test failed: {str(e)}")
        return False

def show_setup_guide():
    """Show detailed setup guide"""
    print("\n📋 GitHub Token Setup Guide")
    print("=" * 30)
    print("""
🔧 Step 1: Create GitHub Token
   1. Go to: https://github.com/settings/personal-access-tokens/tokens
   2. Click "Generate new token"
   3. Select "Fine-grained personal access token" (recommended)
   4. Set expiration (90 days recommended)
   5. Select permissions:
      ✅ models (required for GitHub Models API)
      ✅ metadata (basic access)

🔧 Step 2: Set Environment Variable
   Windows PowerShell:
   $env:GITHUB_TOKEN='ghp_xxxxxxxxxxxx'
   
   Or create .env file:
   GITHUB_TOKEN=ghp_xxxxxxxxxxxx

🔧 Step 3: Verify Access
   Run this script again to verify setup

⚠️  Important Notes:
   - You need GitHub Copilot subscription
   - Token must have 'models' permission
   - Some organizations may restrict GitHub Models access
""")

def main():
    """Main diagnostic function"""
    print(f"🏦 GitHub Token Diagnostic - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = check_github_token()
    
    if not success:
        show_setup_guide()
        print("\n❌ GitHub token setup needs attention")
        return False
    else:
        print("\n🎉 GitHub token is properly configured!")
        print("\n🚀 Your GitHub Copilot integration should work now")
        return True

if __name__ == "__main__":
    main()
