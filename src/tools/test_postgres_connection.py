# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import sys

import psycopg2
"""
Quick PostgreSQL Connection Test
"""

try:
    print("🔗 Testing PostgreSQL connection...")
    conn = psycopg2.connect()
        host='localhost',
        port=5432,
        user='langchain',
        password='langchain123',
        database='langchain'
    
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"[OK] Connected to: {version}")
    
    cursor.execute("SELECT COUNT(*) FROM mcp_sessions;")
    session_count = cursor.fetchone()[0]
    print(f"[OK] MCP sessions table: {session_count} records")
    
    cursor.close()
    conn.close()
    print("[OK] PostgreSQL connection test successful!")
    
except Exception as e:
    print(f"[ERROR] PostgreSQL connection failed: {e}")
    sys.exit(1)