#!/usr/bin/env python3
"""Debug environment variables"""

import os
import sys

print("🔍 DEBUG: Environment Variable Investigation")
print("="*50)

# Check GITHUB_TOKEN specifically
github_token = os.getenv("GITHUB_TOKEN")
print(f"GITHUB_TOKEN: {github_token[:20] if github_token else 'None'}...")

# Check all environment variables containing 'GITHUB'
for key, value in os.environ.items():
    if 'GITHUB' in key.upper():
        print(f"{key}: {value[:20]}...")

# Check if there's any import that might be setting variables
print("\n🔍 Python path:")
for path in sys.path[:5]:
    print(f"  {path}")

print("\n🔍 Current working directory:")
print(f"  {os.getcwd()}")
