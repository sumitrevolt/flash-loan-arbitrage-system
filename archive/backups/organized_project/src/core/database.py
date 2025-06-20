"""
Database Connection and ORM Module for Flash Loan Arbitrage System
Provides database connectivity and data models using SQLAlchemy
"""

import os
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import asyncpg
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, Index, select, delete, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "flash_loan_arbitrage"),
    "username": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# Create base class for SQLAlchemy models
Base = declarative_base()

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    contract_address = Column(String(42), unique=True, nullable=False)
    decimals = Column(Integer, default=18, nullable=False)
    is_whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    price_feeds = relationship("PriceFeed", back_populates="token")

class DEX(Base):
    __tablename__ = "dexes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    router_address = Column(String(42), unique=True, nullable=False)
    factory_address = Column(String(42))
    dex_type = Column(String(20), nullable=False)  # 'uniswap_v2', 'uniswap_v3', etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    price_feeds = relationship("PriceFeed", back_populates="dex")
    buy_opportunities = relationship("ArbitrageOpportunity", foreign_keys="ArbitrageOpportunity.buy_dex_id", back_populates="buy_dex")
    sell_opportunities = relationship("ArbitrageOpportunity", foreign_keys="ArbitrageOpportunity.sell_dex_id", back_populates="sell_dex")

class PriceFeed(Base):
    __tablename__ = "price_feeds"
    
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    dex_id = Column(Integer, ForeignKey("dexes.id"), nullable=False)
    pair_address = Column(String(42))
    price_usd = Column(Numeric(20, 8), nullable=False)
    liquidity_usd = Column(Numeric(20, 2))
    volume_24h = Column(Numeric(20, 2))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    token = relationship("Token", back_populates="price_feeds")
    dex = relationship("DEX", back_populates="price_feeds")
    
    # Indexes
    __table_args__ = (
        Index("idx_price_feeds_token_dex", "token_id", "dex_id"),
        Index("idx_price_feeds_timestamp", "timestamp"),
    )

class ArbitrageOpportunity(Base):
    __tablename__ = "arbitrage_opportunities"
    
    id = Column(Integer, primary_key=True)
    token_pair = Column(String(20), nullable=False)
    buy_dex_id = Column(Integer, ForeignKey("dexes.id"), nullable=False)
    sell_dex_id = Column(Integer, ForeignKey("dexes.id"), nullable=False)
    buy_price = Column(Numeric(20, 8), nullable=False)
    sell_price = Column(Numeric(20, 8), nullable=False)
    price_difference = Column(Numeric(10, 6), nullable=False)
    estimated_profit_usd = Column(Numeric(15, 2), nullable=False)
    trade_amount = Column(Numeric(20, 8), nullable=False)
    gas_estimate = Column(Integer)
    is_profitable = Column(Boolean, default=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    status = Column(String(20), default="discovered")  # 'discovered', 'executed', 'expired', 'failed'
    
    # Relationships
    buy_dex = relationship("DEX", foreign_keys=[buy_dex_id], back_populates="buy_opportunities")
    sell_dex = relationship("DEX", foreign_keys=[sell_dex_id], back_populates="sell_opportunities")
    trades = relationship("Trade", back_populates="opportunity")
    
    # Indexes
    __table_args__ = (
        Index("idx_opportunities_status", "status"),
        Index("idx_opportunities_discovered", "discovered_at"),
    )

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("arbitrage_opportunities.id"))
    transaction_hash = Column(String(66), unique=True)
    block_number = Column(Integer)
    token_pair = Column(String(20), nullable=False)
    buy_dex_id = Column(Integer, ForeignKey("dexes.id"), nullable=False)
    sell_dex_id = Column(Integer, ForeignKey("dexes.id"), nullable=False)
    trade_amount = Column(Numeric(20, 8), nullable=False)
    buy_price = Column(Numeric(20, 8), nullable=False)
    sell_price = Column(Numeric(20, 8), nullable=False)
    actual_profit_usd = Column(Numeric(15, 2))
    gas_used = Column(Integer)
    gas_price_gwei = Column(Numeric(10, 2))
    gas_cost_usd = Column(Numeric(10, 2))
    net_profit_usd = Column(Numeric(15, 2))
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    opportunity = relationship("ArbitrageOpportunity", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index("idx_trades_executed", "executed_at"),
        Index("idx_trades_success", "success"),
    )

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Numeric(20, 8), nullable=False)
    metric_unit = Column(String(20))
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_system_metrics_name_time", "metric_name", "recorded_at"),
    )

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CircuitBreakerEvent(Base):
    __tablename__ = "circuit_breaker_events"
    
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey("tokens.id"))
    dex_id = Column(Integer, ForeignKey("dexes.id"))
    event_type = Column(String(20), nullable=False)  # 'triggered', 'reset'
    reason = Column(Text)
    failed_count = Column(Integer)
    threshold_limit = Column(Integer)
    occurred_at = Column(DateTime, default=datetime.utcnow)

class MCPServerStatus(Base):
    __tablename__ = "mcp_server_status"
    
    id = Column(Integer, primary_key=True)
    server_name = Column(String(100), nullable=False)
    server_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # 'running', 'stopped', 'error'
    last_heartbeat = Column(DateTime)
    error_message = Column(Text)
    uptime_seconds = Column(Integer, default=0)
    requests_processed = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True)
    wallet_address = Column(String(42), unique=True, nullable=False)
    wallet_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    balance_matic = Column(Numeric(20, 8), default=0)
    last_activity = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

@dataclass
class DatabaseManager:
    """Database manager for handling connections and operations"""
    
    def __init__(self):
        self.sync_engine = None
        self.async_engine = None
        self.sync_session_factory = None
        self.async_session_factory = None
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Create async engine
            db_url = f"postgresql+asyncpg://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
            self.async_engine = create_async_engine(db_url, echo=False, pool_size=10, max_overflow=20)
            
            # Create sync engine for migrations
            sync_db_url = f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
            self.sync_engine = create_engine(sync_db_url, echo=False)
            
            # Create session factories
            self.async_session_factory = async_sessionmaker(self.async_engine, class_=AsyncSession)
            self.sync_session_factory = sessionmaker(bind=self.sync_engine)
            
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_tables(self):
        """Create all database tables"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get async database session"""
        return self.async_session_factory()
    
    async def close(self):
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
        if self.sync_engine:
            self.sync_engine.dispose()

class DatabaseOperations:
    """Database operations for the flash loan arbitrage system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def get_token_by_symbol(self, symbol: str) -> Optional[Token]:
        """Get token by symbol"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Token).where(Token.symbol == symbol)
            )
            return result.scalar_one_or_none()
    
    async def get_dex_by_name(self, name: str) -> Optional[DEX]:
        """Get DEX by name"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(DEX).where(DEX.name == name)
            )
            return result.scalar_one_or_none()
    
    async def save_price_feed(self, token_symbol: str, dex_name: str, price_usd: Decimal, liquidity_usd: Optional[Decimal] = None):
        """Save price feed data"""
        async with self.db_manager.get_session() as session:
            # Get token and DEX
            token = await self.get_token_by_symbol(token_symbol)
            dex = await self.get_dex_by_name(dex_name)
            
            if not token or not dex:
                logger.warning(f"Token {token_symbol} or DEX {dex_name} not found")
                return
            
            price_feed = PriceFeed(
                token_id=token.id,
                dex_id=dex.id,
                price_usd=price_usd,
                liquidity_usd=liquidity_usd
            )
            
            session.add(price_feed)
            await session.commit()
    
    async def save_arbitrage_opportunity(self, opportunity_data: Dict[str, Any]) -> ArbitrageOpportunity:
        """Save arbitrage opportunity"""
        async with self.db_manager.get_session() as session:
            opportunity = ArbitrageOpportunity(**opportunity_data)
            session.add(opportunity)
            await session.commit()
            await session.refresh(opportunity)
            return opportunity
    
    async def save_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """Save trade execution data"""
        async with self.db_manager.get_session() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            await session.commit()
            await session.refresh(trade)
            return trade
    
    async def get_active_opportunities(self, limit: int = 50) -> List[ArbitrageOpportunity]:
        """Get active arbitrage opportunities"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(ArbitrageOpportunity)
                .where(ArbitrageOpportunity.status == "discovered")
                .where(ArbitrageOpportunity.expires_at > datetime.utcnow())
                .where(ArbitrageOpportunity.is_profitable == True)
                .order_by(ArbitrageOpportunity.estimated_profit_usd.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def record_system_metric(self, metric_name: str, metric_value: Decimal, metric_unit: str = None):
        """Record system metric"""
        async with self.db_manager.get_session() as session:
            metric = SystemMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit
            )
            session.add(metric)
            await session.commit()
    
    async def get_system_config(self, config_key: str) -> Optional[str]:
        """Get system configuration value"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == config_key)
            )
            config = result.scalar_one_or_none()
            return config.config_value if config else None
    
    async def set_system_config(self, config_key: str, config_value: str, description: str = None):
        """Set system configuration value"""
        async with self.db_manager.get_session() as session:
            # Try to update existing config
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == config_key)
            )
            config = result.scalar_one_or_none()
            
            if config:
                config.config_value = config_value
                config.updated_at = datetime.utcnow()
                if description:
                    config.description = description
            else:
                config = SystemConfig(
                    config_key=config_key,
                    config_value=config_value,
                    description=description
                )
                session.add(config)
            
            await session.commit()
    
    async def update_mcp_server_status(self, server_name: str, status: str, error_message: str = None):
        """Update MCP server status"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(MCPServerStatus).where(MCPServerStatus.server_name == server_name)
            )
            server_status = result.scalar_one_or_none()
            
            if server_status:
                server_status.status = status
                server_status.last_heartbeat = datetime.utcnow()
                if error_message:
                    server_status.error_message = error_message
                    server_status.errors_count += 1
            else:
                server_status = MCPServerStatus(
                    server_name=server_name,
                    server_type="mcp_server",
                    status=status,
                    last_heartbeat=datetime.utcnow(),
                    error_message=error_message
                )
                session.add(server_status)
            
            await session.commit()
    
    async def cleanup_old_data(self):
        """Clean up old data to maintain database performance"""
        async with self.db_manager.get_session() as session:
            # Clean price feeds older than 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            await session.execute(
                delete(PriceFeed).where(PriceFeed.timestamp < cutoff_date)
            )
            
            # Clean expired opportunities older than 1 hour
            expired_cutoff = datetime.utcnow() - timedelta(hours=1)
            await session.execute(
                update(ArbitrageOpportunity)
                .where(ArbitrageOpportunity.expires_at < expired_cutoff)
                .where(ArbitrageOpportunity.status == "discovered")
                .values(status="expired")
            )
            
            await session.commit()

# Global database manager instance
db_manager = DatabaseManager()
db_ops = DatabaseOperations(db_manager)

async def init_database():
    """Initialize database connections and create tables"""
    await db_manager.initialize()
    await db_manager.create_tables()
    logger.info("Database initialization complete")

async def shutdown_database():
    """Shutdown database connections"""
    await db_manager.close()
    logger.info("Database connections closed")

# Export main components
__all__ = [
    "Token", "DEX", "PriceFeed", "ArbitrageOpportunity", "Trade", 
    "SystemMetric", "SystemConfig", "CircuitBreakerEvent", "MCPServerStatus", "Wallet",
    "DatabaseManager", "DatabaseOperations", "db_manager", "db_ops",
    "init_database", "shutdown_database"
]
