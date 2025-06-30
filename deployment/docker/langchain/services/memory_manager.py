# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import json
import sqlite3

from utils.config import get_config
from utils.logger import setup_logger
import redis
"""
Memory Manager Service
====================
Service for managing agent memory, conversation history, and persistent state
across the multi-agent flash loan system.
"""


logger = setup_logger(__name__)

class MemoryManager:
    """
    Memory Manager for maintaining agent state and conversation history.

    Features:
    - Short-term memory (Redis)
    - Long-term memory (SQLite/PostgreSQL)
    - Conversation history
    - Agent state persistence
    - Memory cleanup and optimization
    """

    def __init__(self):
        self.config = get_config()
        self.redis_client = None
        self.sqlite_conn = None
        self.memory_db_path = "/app/data/memory.db"

        logger.info("🧠 Memory Manager initialized")

    async def initialize(self):
        """Initialize the memory manager"""
        try:
            logger.info("🧠 Initializing Memory Manager...")

            # Initialize Redis for short-term memory
            await self.setup_redis()

            # Initialize SQLite for long-term memory
            await self.setup_sqlite()

            # Create memory tables
            await self.create_memory_tables()

            # Start cleanup task
            asyncio.create_task(self.periodic_cleanup())

            logger.info("[OK] Memory Manager initialization completed")

        except Exception as e:
            logger.error(str(f"[ERROR] Memory Manager initialization failed: {e}")
            raise

    async def setup_redis(self):
        """Set up Redis connection for short-term memory"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password,
                db=self.config.redis.db,
                decode_responses=True


            # Test connection
            await asyncio.to_thread(self.redis_client.ping)
            logger.info("[OK] Redis connection established for short-term memory")

        except Exception as e:
            logger.error(str(f"[ERROR] Redis setup failed: {e}")
            self.redis_client = None

    async def setup_sqlite(self):
        """Set up SQLite connection for long-term memory"""
        try:
            # Ensure directory exists
            Path(self.memory_db_path).parent.mkdir(parents=True, exist_ok=True)

            self.sqlite_conn = sqlite3.connect(self.memory_db_path, check_same_thread=False)
            self.sqlite_conn.row_factory = sqlite3.Row

            logger.info(str(f"[OK] SQLite connection established: {self.memory_db_path}")

        except Exception as e:
            logger.error(str(f"[ERROR] SQLite setup failed: {e}")
            self.sqlite_conn = None

    async def create_memory_tables(self):
        """Create memory storage tables"""
        try:
            if not self.sqlite_conn:
                logger.warning("[WARN] SQLite not available, skipping table creation")
                return

            cursor = self.sqlite_conn.cursor()

            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    agent_name TEXT,
                    message_type TEXT,
                    message_content TEXT,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP

            '''

            # Agent states table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_states (
                    agent_name TEXT PRIMARY KEY,
                    state_data TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP

            '''

            # Memory facts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_type TEXT,
                    fact_content TEXT,
                    agent_name TEXT,
                    relevance_score REAL DEFAULT 0.5,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP

            '''

            # Session metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT

            '''

            self.sqlite_conn.commit()
            logger.info("[OK] Memory tables created successfully")

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to create memory tables: {e}")

    async def store_conversation(self, session_id: str, agent_name: str,
                                message_type: str, message_content: str,
                                metadata: Optional[Dict] = None) -> bool:
        """Store conversation message"""
        try:
            message_id = f"{session_id}_{agent_name}_{datetime.now().isoformat()}"

            # Store in Redis for quick access
            if self.redis_client:
                conversation_key = f"conversation:{session_id}"
                message_data = {
                    "id": message_id,
                    "agent_name": agent_name,
                    "message_type": message_type,
                    "message_content": message_content,
                    "metadata": json.dumps(metadata or {}, ensure_ascii=True, default=str),
                    "timestamp": datetime.now().isoformat()


                await asyncio.to_thread(
                    self.redis_client.lpush,
                    conversation_key,
                    json.dumps(message_data, ensure_ascii=True, default=str)


                # Set expiration for Redis entries (24 hours)
                await asyncio.to_thread(self.redis_client.expire, conversation_key, 86400)

            # Store in SQLite for persistence
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    INSERT INTO conversations
                    (id, session_id, agent_name, message_type, message_content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    message_id, session_id, agent_name, message_type,
                    message_content, json.dumps(metadata or {}, ensure_ascii=True, default=str)


                self.sqlite_conn.commit()

            return True

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to store conversation: {e}")
            return False

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a session"""
        try:
            messages = []

            # Try Redis first (faster)
            if self.redis_client:
                conversation_key = f"conversation:{session_id}"
                redis_messages = await asyncio.to_thread(
                    self.redis_client.lrange, conversation_key, 0, limit - 1


                for msg_str in redis_messages:
                    try:
                        messages.append(json.loads(msg_str))
                    except json.JSONDecodeError:
                        continue

                if messages:
                    # Reverse to get chronological order
                    messages.reverse()
                    return messages

            # Fallback to SQLite
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    SELECT * FROM conversations
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (session_id, limit)

                rows = cursor.fetchall()
                messages = []
                for row in rows:
                    messages.append({
                        "id": row["id"],
                        "agent_name": row["agent_name"],
                        "message_type": row["message_type"],
                        "message_content": row["message_content"],
                        "metadata": json.loads(row["metadata"] or "{}"),
                        "timestamp": row["timestamp"]


                # Reverse to get chronological order
                messages.reverse()

            return messages

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to get conversation history: {e}")
            return []

    async def store_agent_state(self, agent_name: str, state_data: Dict[str, Any]) -> bool:
        """Store agent state"""
        try:
            state_json = json.dumps(state_data, ensure_ascii=True, default=str)

            # Store in Redis for quick access
            if self.redis_client:
                state_key = f"agent_state:{agent_name}"
                await asyncio.to_thread(self.redis_client.set, state_key, state_json)
                # Set expiration for Redis entries (1 hour)
                await asyncio.to_thread(self.redis_client.expire, state_key, 3600)

            # Store in SQLite for persistence
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO agent_states
                    (agent_name, state_data, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (agent_name, state_json)

                self.sqlite_conn.commit()

            return True

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to store agent state: {e}")
            return False

    async def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent state"""
        try:
            # Try Redis first
            if self.redis_client:
                state_key = f"agent_state:{agent_name}"
                state_data = await asyncio.to_thread(self.redis_client.get, state_key)
                if state_data:
                    return json.loads(state_data)

            # Fallback to SQLite
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    SELECT state_data FROM agent_states
                    WHERE agent_name = ?
                ''', (agent_name,)

                row = cursor.fetchone()
                if row:
                    return json.loads(row["state_data"])

            return None

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to get agent state: {e}")
            return None

    async def store_memory_fact(self, fact_type: str, fact_content: str,
                               agent_name: str, relevance_score: float = 0.5) -> bool:
        """Store a memory fact"""
        try:
            if not self.sqlite_conn:
                logger.warning("[WARN] SQLite not available, cannot store memory fact")
                return False

            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                INSERT INTO memory_facts
                (fact_type, fact_content, agent_name, relevance_score)
                VALUES (?, ?, ?, ?)
            ''', (fact_type, fact_content, agent_name, relevance_score)

            self.sqlite_conn.commit()

            return True

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to store memory fact: {e}")
            return False

    async def search_memory_facts(self, query: str, agent_name: Optional[str] = None,
                                fact_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search memory facts"""
        try:
            if not self.sqlite_conn:
                return []

            cursor = self.sqlite_conn.cursor()

            # Build query
            sql = "SELECT * FROM memory_facts WHERE fact_content LIKE ?"
            params = [f"%{query}%"]

            if agent_name:
                sql += " AND agent_name = ?"
                params.append(agent_name)

            if fact_type:
                sql += " AND fact_type = ?"
                params.append(fact_type)

            sql += " ORDER BY relevance_score DESC, last_accessed DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            facts = []
            for row in rows:
                facts.append({
                    "id": row["id"],
                    "fact_type": row["fact_type"],
                    "fact_content": row["fact_content"],
                    "agent_name": row["agent_name"],
                    "relevance_score": row["relevance_score"],
                    "created_at": row["created_at"],
                    "last_accessed": row["last_accessed"]


                # Update last accessed time
                cursor.execute('''
                    UPDATE memory_facts
                    SET last_accessed = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (row["id"],)

            self.sqlite_conn.commit()
            return facts

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to search memory facts: {e}")
            return []

    async def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> bool:
        """Create a new session"""
        try:
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions
                    (session_id, created_at, last_activity, metadata)
                    VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
                ''', (session_id, json.dumps(metadata or {}, ensure_ascii=True, default=str))

                self.sqlite_conn.commit()

            return True

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to create session: {e}")
            return False

    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        try:
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    UPDATE sessions
                    SET last_activity = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                ''', (session_id,)
                self.sqlite_conn.commit()

            return True

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to update session activity: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            stats = {
                "redis_available": self.redis_client is not None,
                "sqlite_available": self.sqlite_conn is not None,
                "total_conversations": 0,
                "total_sessions": 0,
                "total_facts": 0,
                "active_sessions": 0


            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()

                # Count conversations
                cursor.execute("SELECT COUNT(*) as count FROM conversations")
                stats["total_conversations"] = cursor.fetchone()["count"]

                # Count sessions
                cursor.execute("SELECT COUNT(*) as count FROM sessions")
                stats["total_sessions"] = cursor.fetchone()["count"]

                # Count memory facts
                cursor.execute("SELECT COUNT(*) as count FROM memory_facts")
                stats["total_facts"] = cursor.fetchone()["count"]

                # Count active sessions (last 24 hours)
                cursor.execute('''
                    SELECT COUNT(*) as count FROM sessions
                    WHERE last_activity > datetime('now', '-1 day')
                '''
                stats["active_sessions"] = cursor.fetchone()["count"]

            return stats

        except Exception as e:
            logger.error(str(f"[ERROR] Failed to get memory stats: {e}")
            return {}

    async def periodic_cleanup(self):
        """Periodic cleanup of old memory data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                logger.info("🧹 Starting periodic memory cleanup...")

                if self.sqlite_conn:
                    cursor = self.sqlite_conn.cursor()

                    # Clean up old conversations (older than 30 days)
                    cursor.execute('''
                        DELETE FROM conversations
                        WHERE timestamp < datetime('now', '-30 days')
                    '''

                    # Clean up inactive sessions (older than 7 days)
                    cursor.execute('''
                        DELETE FROM sessions
                        WHERE last_activity < datetime('now', '-7 days')
                    '''

                    # Clean up low relevance facts (older than 7 days and relevance < 0.3)
                    cursor.execute('''
                        DELETE FROM memory_facts
                        WHERE created_at < datetime('now', '-7 days')
                        AND relevance_score < 0.3
                    '''

                    self.sqlite_conn.commit()
                    logger.info("[OK] Memory cleanup completed")

            except Exception as e:
                logger.error(str(f"[ERROR] Periodic cleanup failed: {e}")

    async def cleanup(self):
        """Cleanup memory manager resources"""
        try:
            if self.redis_client:
                self.redis_client.close()

            if self.sqlite_conn:
                self.sqlite_conn.close()

            logger.info("[OK] Memory Manager cleanup completed")

        except Exception as e:
            logger.error(str(f"[ERROR] Memory Manager cleanup failed: {e}")