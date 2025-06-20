#!/usr/bin/env python3
"""
MaxKB Status Checker
Quick script to check if MaxKB is running and accessible
"""

import requests
import time
import subprocess
import sys

def check_docker_container():
    """Check if MaxKB container is running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=maxkb", "--format", "{{.Status}}"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            print(f"✅ MaxKB container status: {result.stdout.strip()}")
            return True
        else:
            print("❌ MaxKB container not found or not running")
            return False
    except subprocess.CalledProcessError:
        print("❌ Error checking Docker container")
        return False

def check_maxkb_web():
    """Check if MaxKB web interface is accessible"""
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ MaxKB web interface is accessible")
            return True
        else:
            print(f"⚠️  MaxKB responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MaxKB web interface")
        return False
    except requests.exceptions.Timeout:
        print("⏳ MaxKB web interface is slow to respond")
        return False
    except Exception as e:
        print(f"❌ Error checking web interface: {e}")
        return False

def main():
    print("🔍 MaxKB Status Check")
    print("===================")
    
    # Check Docker container
    container_ok = check_docker_container()
    
    if container_ok:
        print("\n⏳ Checking web interface...")
        time.sleep(2)
        
        # Check web interface
        web_ok = check_maxkb_web()
        
        if web_ok:
            print("\n🎉 MaxKB is fully operational!")
            print("📍 Access at: http://localhost:8080")
            print("👤 Username: admin")
            print("🔑 Password: MaxKB@123..")
        else:
            print("\n⏳ MaxKB container is running but web interface not ready yet")
            print("💡 Try again in a few minutes or check logs: docker logs maxkb")
    else:
        print("\n❌ MaxKB container is not running")
        print("🚀 Start with: docker start maxkb")
        print("📝 Or run setup script: python complete_setup_with_maxkb.py")

if __name__ == "__main__":
    main()
