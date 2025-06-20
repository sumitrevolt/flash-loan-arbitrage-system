#!/usr/bin/env python3
"""
PostgreSQL LangChain Setup and Verification
Ensures PostgreSQL is properly configured for LangChain operations
"""

import psycopg2
import logging
import time
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLLangChainSetup:
    """PostgreSQL setup for LangChain integration"""
    
    def __init__(self, host='localhost', port=5432, admin_user='postgres', admin_password='password'):
        self.host = host
        self.port = port
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.langchain_user = 'langchain'
        self.langchain_password = 'langchain123'
        self.langchain_db = 'langchain'
        
    def wait_for_postgres(self, max_attempts=30):
        """Wait for PostgreSQL to be ready"""
        logger.info("Waiting for PostgreSQL to be ready...")
        
        for attempt in range(max_attempts):
            try:
                conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.admin_user,
                    password=self.admin_password,
                    database='postgres'
                )
                conn.close()
                logger.info("✅ PostgreSQL is ready")
                return True
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}: {e}")
                time.sleep(2)
        
        logger.error("❌ PostgreSQL not ready after maximum attempts")
        return False
    
    def create_langchain_user(self):
        """Create LangChain user if it doesn't exist"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database='postgres'
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            # Check if user exists
            cur.execute("SELECT 1 FROM pg_user WHERE usename = %s", (self.langchain_user,))
            if cur.fetchone():
                logger.info(f"✅ User '{self.langchain_user}' already exists")
            else:
                # Create user
                cur.execute(f"CREATE USER {self.langchain_user} WITH SUPERUSER PASSWORD %s", (self.langchain_password,))
                logger.info(f"✅ Created user '{self.langchain_user}'")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            return False
    
    def create_langchain_database(self):
        """Create LangChain database if it doesn't exist"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                database='postgres'
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.langchain_db,))
            if cur.fetchone():
                logger.info(f"✅ Database '{self.langchain_db}' already exists")
            else:
                # Create database
                cur.execute(f"CREATE DATABASE {self.langchain_db} OWNER {self.langchain_user}")
                logger.info(f"✅ Created database '{self.langchain_db}'")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False
    
    def setup_langchain_extensions(self):
        """Set up PostgreSQL extensions for LangChain"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.langchain_user,
                password=self.langchain_password,
                database=self.langchain_db
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            # Enable useful extensions for LangChain
            extensions = ['uuid-ossp', 'hstore']
            
            for ext in extensions:
                try:
                    cur.execute(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\"")
                    logger.info(f"✅ Enabled extension: {ext}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not enable extension {ext}: {e}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup extensions: {e}")
            return False
    
    def create_langchain_tables(self):
        """Create basic LangChain tables"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.langchain_user,
                password=self.langchain_password,
                database=self.langchain_db
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            # Create basic tables for LangChain operations
            tables = {
                'mcp_sessions': '''
                    CREATE TABLE IF NOT EXISTS mcp_sessions (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        session_name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                ''',
                'flash_loan_operations': '''
                    CREATE TABLE IF NOT EXISTS flash_loan_operations (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        operation_type VARCHAR(100) NOT NULL,
                        token_symbol VARCHAR(20) NOT NULL,
                        amount DECIMAL(36, 18) NOT NULL,
                        profit DECIMAL(36, 18),
                        gas_used BIGINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                ''',
                'arbitrage_opportunities': '''
                    CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        token_pair VARCHAR(50) NOT NULL,
                        dex_source VARCHAR(50) NOT NULL,
                        dex_target VARCHAR(50) NOT NULL,
                        profit_percentage DECIMAL(10, 6) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_executed BOOLEAN DEFAULT FALSE,
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                '''
            }
            
            for table_name, create_sql in tables.items():
                cur.execute(create_sql)
                logger.info(f"✅ Created/verified table: {table_name}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            return False
    
    def test_langchain_connection(self):
        """Test LangChain connection and operations"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.langchain_user,
                password=self.langchain_password,
                database=self.langchain_db
            )
            cur = conn.cursor()
            
            # Test basic operations
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            logger.info(f"✅ Connected to: {version}")
            
            # Test table access
            cur.execute("SELECT COUNT(*) FROM mcp_sessions")
            session_count = cur.fetchone()[0]
            logger.info(f"✅ MCP sessions table accessible: {session_count} records")
            
            # Insert test data
            cur.execute("""
                INSERT INTO mcp_sessions (session_name, metadata) 
                VALUES (%s, %s) 
                ON CONFLICT DO NOTHING
            """, ('test_session', '{"test": true}'))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info("✅ LangChain PostgreSQL connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ LangChain connection test failed: {e}")
            return False
    
    def get_connection_string(self):
        """Get connection string for LangChain"""
        return f"postgresql://{self.langchain_user}:{self.langchain_password}@{self.host}:{self.port}/{self.langchain_db}"
    
    def setup_complete(self):
        """Perform complete PostgreSQL setup for LangChain"""
        logger.info("🚀 Starting PostgreSQL LangChain Setup")
        
        steps = [
            ("Waiting for PostgreSQL", self.wait_for_postgres),
            ("Creating LangChain user", self.create_langchain_user),
            ("Creating LangChain database", self.create_langchain_database),
            ("Setting up extensions", self.setup_langchain_extensions),
            ("Creating LangChain tables", self.create_langchain_tables),
            ("Testing connection", self.test_langchain_connection),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Failed at step: {step_name}")
                return False
        
        logger.info("🎉 PostgreSQL LangChain setup completed successfully!")
        logger.info(f"📊 Connection string: {self.get_connection_string()}")
        
        return True

def main():
    """Main setup function"""
    print("🏦 PostgreSQL LangChain Setup")
    print("=" * 40)
    
    # Try different PostgreSQL configurations
    configs = [
        # Try with admin user 'postgres' and password 'password' (from docker-compose.complete.yml)
        {'admin_user': 'postgres', 'admin_password': 'password'},
        # Try with langchain user if it already exists
        {'admin_user': 'langchain', 'admin_password': 'langchain123'},
        # Try with default postgres setup
        {'admin_user': 'postgres', 'admin_password': 'postgres'},
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n🔧 Trying configuration {i}: user={config['admin_user']}")
        
        setup = PostgreSQLLangChainSetup(**config)
        
        if setup.wait_for_postgres():
            if setup.setup_complete():
                print(f"\n✅ Success with configuration {i}!")
                print(f"🔗 LangChain connection string:")
                print(f"   {setup.get_connection_string()}")
                return 0
            else:
                print(f"❌ Setup failed with configuration {i}")
        else:
            print(f"❌ Could not connect with configuration {i}")
    
    print(f"\n❌ All configurations failed. Check PostgreSQL container status.")
    return 1

if __name__ == "__main__":
    exit(main())
