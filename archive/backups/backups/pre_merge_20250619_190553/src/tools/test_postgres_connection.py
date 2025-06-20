#!/usr/bin/env python3
"""
Quick PostgreSQL Connection Test
"""
import psycopg2
import sys

try:
    print("🔗 Testing PostgreSQL connection...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='langchain',
        password='langchain123',
        database='langchain'
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ Connected to: {version}")
    
    cursor.execute("SELECT COUNT(*) FROM mcp_sessions;")
    session_count = cursor.fetchone()[0]
    print(f"✅ MCP sessions table: {session_count} records")
    
    cursor.close()
    conn.close()
    print("✅ PostgreSQL connection test successful!")
    
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    sys.exit(1)
