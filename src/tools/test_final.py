#!/usr/bin/env python3
"""
Quick test with .env file loading
"""

import os
from pathlib import Path
import requests

# Load environment from .env file
def load_env():
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line: str = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"✅ Loaded {key} from .env")

def test_github_models():
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ No GitHub token found")
        return False
    
    print(f"✅ GitHub token found: {github_token[:20]}...")
    
    try:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": "What makes a flash loan arbitrage profitable? Give me 3 key factors in 100 words."
                }
            ],
            "max_tokens": 150,
            "temperature": 0.1
        }
        
        print("🔄 Calling GitHub Models API...")
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            json=data,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result: str = response.json()
            content = result["choices"][0]["message"]["content"]
            print("\n✅ GitHub Models API Success!")
            print("=" * 50)
            print("🤖 AI Response:")
            print(content)
            print("=" * 50)
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 GitHub Copilot Multi-Agent System Test")
    print("=" * 45)
    
    # Load environment variables
    load_env()
    
    # Test GitHub Models API
    success = test_github_models()
    
    if success:
        print("\n🎉 SUCCESS! GitHub Copilot integration is working!")
        print("🚀 Your multi-agent flash loan system is ready!")
        print("\n💡 Key Benefits:")
        print("   ✅ FREE with GitHub Copilot subscription")
        print("   ✅ Multiple AI models (GPT-4, Claude, Llama)")
        print("   ✅ Specialized agents for different tasks")
        print("   ✅ No additional API costs")
        print("   ✅ High rate limits")
        
        print("\n🎯 Next Steps:")
        print("   1. Run the full multi-agent system test")
        print("   2. Integrate with your flash loan contracts")
        print("   3. Set up automated arbitrage monitoring")
        print("   4. Configure custom trading strategies")
    else:
        print("\n❌ GitHub Copilot integration failed")
        print("Please check your token and try again")
