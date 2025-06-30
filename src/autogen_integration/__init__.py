# -*- coding: utf-8 -*-
"""
AutoGen Integration Module for Flash Loan Arbitrage System

This module provides comprehensive AutoGen integration with the LangChain orchestrator,
enabling sophisticated multi-agent decision making for flash loan arbitrage operations.
"""

from .agent_registry import AgentRegistry
from .autogen_coordinator import AutoGenCoordinator
from .conversation_orchestrator import ConversationOrchestrator
from .decision_engine import ConsensusDecisionEngine
from .mcp_bridge import MCPBridge
from .specialized_agents import FlashLoanAgentFactory  

__version__ = "1.0.0"
__author__ = "Flash Loan Arbitrage System"

__all__ = [
    "AutoGenCoordinator",
    "FlashLoanAgentFactory", 
    "ConversationOrchestrator",
    "ConsensusDecisionEngine",
    "MCPBridge",
    "AgentRegistry"
