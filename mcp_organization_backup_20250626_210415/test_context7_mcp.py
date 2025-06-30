#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Context7 MCP Server
"""

import asyncio
import json
import subprocess
import sys

async def test_context7_mcp_server():
    """Test the Context7 MCP server functionality"""
    
    print("Testing Context7 MCP Server...")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Initialize",
            "method": "initialize",
            "params": {},
            "expected": "protocolVersion"
        },
        {
            "name": "List Tools",
            "method": "tools/list",
            "params": {},
            "expected": "tools"
        },
        {
            "name": "Search Documentation",
            "method": "tools/call",
            "params": {
                "name": "search_docs",
                "arguments": {
                    "library": "python",
                    "query": "asyncio"

            },
            "expected": "results"
        },
        {
            "name": "Get Library Info",
            "method": "tools/call",
            "params": {
                "name": "get_library_info",
                "arguments": {
                    "library": "requests"

            },
            "expected": "description"
        },
        {
            "name": "Health Check",
            "method": "tools/call",
            "params": {
                "name": "health_check",
                "arguments": {}
            },
            "expected": "status"


    
    # Start the server process
    print("Starting Context7 MCP Server...")
    process = subprocess.Popen(
        [sys.executable, "mcp_servers/context7_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True

    
    try:
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Run test cases
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['name']}")
            print("-" * 30)
            
            # Prepare message
            message = {
                "jsonrpc": "2.0",
                "id": i,
                "method": test_case["method"],
                "params": test_case["params"]

            
            # Send message to server
            message_str = json.dumps(message) + "\n"
            process.stdin.write(message_str)
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if response_line:
                try:
                    response = json.loads(response_line.strip())
                    
                    # Check for errors
                    if "error" in response:
                        print(f"❌ Error: {response['error']}")
                        continue
                    
                    # Check result
                    result = response.get("result", {})
                    if test_case["expected"] in str(result):
                        print(f"✅ Success: {test_case['name']}")
                        print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
                    else:
                        print(f"❌ Failed: Expected '{test_case['expected']}' not found in response")
                        print(f"   Response: {json.dumps(result, indent=2)}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Parse Error: {e}")
                    print(f"   Raw response: {response_line}")
            else:
                print(f"❌ No response received for {test_case['name']}")
        
        print("\n" + "=" * 50)
        print("Context7 MCP Server Test Complete!")
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
    
    finally:
        # Clean up
        print("\nStopping Context7 MCP Server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        # Check for any errors
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"Server stderr: {stderr_output}")

def main():
    """Main entry point"""
    try:
        asyncio.run(test_context7_mcp_server())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 