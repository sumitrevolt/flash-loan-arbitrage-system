#!/usr/bin/env python3
"""Test GitHub token authentication"""

import os
from github import Github
import requests

def test_github_token():
    """Test GitHub token with different methods"""
    
    # Get token from environment
    token = os.getenv("GITHUB_TOKEN")
    print(f"Token from environment: {token[:20]}...{token[-10:] if token else 'None'}")
    
    if not token:
        print("❌ No GITHUB_TOKEN found in environment")
        return
    
    # Test 1: Direct API call with requests
    print("\n🧪 Testing with requests library:")
    try:
        response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {token}'}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   User: {user_data.get('login', 'Unknown')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: PyGithub library
    print("\n🧪 Testing with PyGithub library:")
    try:
        github_client = Github(token)
        user = github_client.get_user()
        print(f"   Success! User: {user.login}")
        print(f"   Name: {user.name}")
        print(f"   Public repos: {user.public_repos}")
    except Exception as e:
        print(f"   Exception: {e}")
        print(f"   Exception type: {type(e)}")

if __name__ == "__main__":
    test_github_token()
