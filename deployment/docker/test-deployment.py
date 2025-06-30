# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import json
import sys
import time

import requests
"""
Test script for LangChain and AutoGen Docker deployment
"""


def test_service(service_name, url, timeout=30):
    """Test if a service is responding"""
    print(f"Testing {service_name} at {url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"OK {service_name} is responding")
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=True, default=str)}")
                except:
                    print(f"   Response: {response.text[:200]}...")
                return True
            else:
                print(f"ERROR {service_name} returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"WAITING {service_name} not ready yet... ({e})")
            time.sleep(2)
        
        print(f"FAILED {service_name} failed to respond within {timeout}s")
    return False

def main():
    """Main test function"""
    print("Testing LangChain and AutoGen Deployment")
    print("=" * 50)
    
    services = []
        ("LangChain Coordinator", "http://localhost:8000/health"),
        ("AutoGen Coordinator", "http://localhost:8010/health"),
        ("PostgreSQL (via LangChain)", "http://localhost:8000/status"),
        ("Redis (via LangChain)", "http://localhost:8000/status"),
    
    
    results = []
    
    for service_name, url in services:
        result = test_service(service_name, url)
        results.append((service_name, result))
        print()
    
    print("Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for service_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{service_name}: {status}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("All services are working correctly!")
        return 0
    else:
        print("Some services are not responding. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())