from typing import Dict, List, Any, Optional\n#!/usr/bin/env python3
"""
Quick test of GitHub Copilot integration
"""

import os
import requests

def test_github_models():
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ No GitHub token found")
        return False
    
    print(f"✅ GitHub token: {github_token[:20]}...")
    
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
                    "content": "What are the key components of a profitable flash loan arbitrage in DeFi? List 3 main points."
                }
            ],
            "max_tokens": 200,
            "temperature": 0.1
        }
        
        print("🔄 Making request to GitHub Models API...")
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result: str = response.json()
            content = result["choices"][0]["message"]["content"]
            print("✅ GitHub Models API Response:")
            print("-" * 50)
            print(content)
            print("-" * 50)
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick GitHub Copilot Test")
    print("=" * 30)
    
    success = test_github_models()
    
    if success:
        print("\n🎉 GitHub Copilot integration is working!")
        print("✅ Your multi-agent system should work properly")
    else:
        print("\n❌ GitHub Copilot integration has issues")
