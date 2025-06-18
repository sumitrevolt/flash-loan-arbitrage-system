"""
Revenue Model - Tracks flash loan arbitrage revenue and transactions
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .agent import Base

class Revenue(Base):
    """Revenue model for tracking arbitrage profits"""
    __tablename__ = 'revenues'

    id = Column(String(36), primary_key=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100), nullable=False)  # e.g., 'aave_flash_loan', 'uniswap_arb'
    transaction_hash = Column(String(66), nullable=False, unique=True)
    block_number = Column(Integer, nullable=False)
    agent_id = Column(String(36), ForeignKey('agents.id'))
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with Agent
    agent = relationship("Agent", backref="revenues")

    def __repr__(self):
        return f"<Revenue(amount={self.amount} {self.currency}, tx={self.transaction_hash[:10]}...)>"

    @property
    def amount_usd(self) -> float:
        """Calculate USD value of the revenue
        
        Note: In production, this should use a price feed or oracle
        """
        # Simplified conversion - should use real-time rates in production
        rates = {
            'ETH': 3000,
            'WETH': 3000,
            'BTC': 50000,
            'WBTC': 50000,
            'USDC': 1,
            'USDT': 1,
            'DAI': 1
        }
        return self.amount * rates.get(self.currency.upper(), 1)

    def to_dict(self) -> dict:
        """Convert revenue record to dictionary"""
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'amount_usd': self.amount_usd,
            'date': self.date.isoformat(),
            'source': self.source,
            'transaction_hash': self.transaction_hash,
            'block_number': self.block_number,
            'agent_id': self.agent_id,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def create_from_transaction(cls, 
                              amount: float,
                              currency: str,
                              source: str,
                              tx_hash: str,
                              block_number: int,
                              agent_id: Optional[str] = None,
                              description: Optional[str] = None) -> 'Revenue':
        """Create a new revenue record from transaction data"""
        return cls(
            amount=amount,
            currency=currency,
            source=source,
            transaction_hash=tx_hash,
            block_number=block_number,
            agent_id=agent_id,
            description=description
        )