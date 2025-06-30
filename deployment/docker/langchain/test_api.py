#!/usr/bin/env python3
"""
Test script for LangChain NVIDIA MCP Server API
"""

import requests

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_generate_text():
    """Test text generation endpoint"""
    data = {
        "text": "What is flash loan arbitrage?",
        "model": "nvidia-llama"
    }
    response = requests.post(f"{BASE_URL}/generate", json=data)
    print("Text Generation:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_embeddings():
    """Test embeddings generation endpoint"""
    data = {
        "text": "Flash loan arbitrage opportunity",
        "model": "nvidia-embeddings"
    }
    response = requests.post(f"{BASE_URL}/embeddings", json=data)
    print("Embeddings Generation:")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Dimensions: {result.get('dimensions')}")
    print(f"Model: {result.get('model')}")
    print(f"Cached: {result.get('cached')}")
    print()

def test_gpu_status():
    """Test GPU status endpoint"""
    response = requests.get(f"{BASE_URL}/gpu/status")
    print("GPU Status:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_root():
    """Test root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print("Root Endpoint:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("Testing LangChain NVIDIA MCP Server API")
    print("=" * 50)
    
    try:
        test_root()
        test_health()
        test_generate_text()
        test_embeddings()
        test_gpu_status()
        
        print("✅ All tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server")
        print("Make sure the Docker containers are running:")
        print("docker-compose -f docker-compose.simple.yml up -d")
        
    except Exception as e:
        print(f"❌ Error: {e}") 