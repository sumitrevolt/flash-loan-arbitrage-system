#!/usr/bin/env python3
"""
GitHub Token Diagnostic Script
This helps diagnose issues with GitHub Copilot token integration
"""

import os
import requests
import sys
from pathlib import Path

def load_env_file():
    """Load .env file manually"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line: str = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Loaded .env file")
    else:
        print("❌ No .env file found")

def check_github_token():
    """Check GitHub token validity and permissions"""
    print("\n🔍 GitHub Token Diagnostic")
    print("-" * 30)
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not found in environment")
        return False
    
    print(f"✅ Token found: {token[:16]}...")
    
    # Test basic GitHub API access
    print("\n🧪 Testing GitHub API access...")
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub API access successful")
            print(f"   User: {user_data.get('login', 'Unknown')}")
            print(f"   Name: {user_data.get('name', 'Not set')}")
        else:
            print(f"❌ GitHub API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ GitHub API request failed: {str(e)}")
        return False
    
    # Test GitHub Models API access
    print("\n🤖 Testing GitHub Models API...")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello, test message"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            'https://models.inference.ai.azure.com/chat/completions',
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ GitHub Models API access successful!")
            result: str = response.json()
            print(f"   Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ GitHub Models API Error: {response.status_code}")
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"   Error: {error_data}")
            
            if response.status_code == 401:
                print("\n💡 Token Permission Issue:")
                print("   Your token needs the 'models' permission scope")
                print("   1. Go to: https://github.com/settings/tokens")
                print("   2. Edit your token or create a new one")
                print("   3. Enable the 'models' permission")
                print("   4. Update GITHUB_TOKEN in .env file")
            
            return False
            
    except Exception as e:
        print(f"❌ GitHub Models API request failed: {str(e)}")
        return False

def check_alternative_providers():
    """Check if other AI providers are available"""
    print("\n🔄 Alternative AI Providers")
    print("-" * 30)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if openai_key and openai_key != 'sk-test-key-for-demo':
        print("✅ OpenAI API key found")
        print("   You can use: AI_PROVIDER=openai")
    else:
        print("❌ OpenAI API key not configured")
    
    if anthropic_key and anthropic_key != 'your_anthropic_api_key_here':
        print("✅ Anthropic API key found")
        print("   You can use: AI_PROVIDER=anthropic")
    else:
        print("❌ Anthropic API key not configured")

def provide_recommendations():
    """Provide recommendations based on diagnostic results"""
    print("\n📋 Recommendations")
    print("-" * 20)
    print("1. 🔑 Fix GitHub Token:")
    print("   - Generate new token at: https://github.com/settings/tokens")
    print("   - Ensure 'models' permission is enabled")
    print("   - Update GITHUB_TOKEN in .env file")
    print("")
    print("2. 🔄 Alternative Setup:")
    print("   - Get OpenAI API key: https://platform.openai.com/api-keys")
    print("   - Set AI_PROVIDER=openai in .env file")
    print("")
    print("3. 🧪 Test Again:")
    print("   - Run: python test_github_copilot_agents.py")
    print("   - Or run: python github_token_diagnostic.py")

def main():
    """Main diagnostic function"""
    print("🔧 GitHub Copilot Integration Diagnostic")
    print("=" * 40)
    
    # Load environment
    load_env_file()
    
    # Check GitHub token
    github_success = check_github_token()
    
    # Check alternatives
    check_alternative_providers()
    
    # Provide recommendations
    if not github_success:
        provide_recommendations()
    else:
        print("\n🎉 GitHub Copilot integration is working correctly!")
        print("You can now run the multi-agent system tests.")

if __name__ == "__main__":
    main()
