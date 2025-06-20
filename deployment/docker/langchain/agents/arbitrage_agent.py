"""
Arbitrage Agent
==============

Specialized agent for identifying and analyzing arbitrage opportunities
in the flash loan system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from utils.logger import setup_logger

logger = setup_logger(__name__)

class ArbitrageAgent:
    """
    Arbitrage Agent for identifying and analyzing arbitrage opportunities.
    
    Capabilities:
    - Price difference detection
    - Profit calculation
    - Opportunity ranking
    - Market analysis
    - Risk assessment integration
    """
    
    def __init__(self, name: str, memory_manager, tool_registry):
        self.name = name
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        
        # LLM for arbitrage analysis
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            max_tokens=2000
        )
        
        # Agent capabilities
        self.capabilities = [
            "arbitrage_detection",
            "profit_calculation",
            "opportunity_ranking",
            "market_analysis",
            "price_monitoring"
        ]
        
        self.setup_prompts()
        logger.info(f"💰 Arbitrage Agent '{name}' initialized")

    def setup_prompts(self):
        """Set up arbitrage-specific prompt templates"""
        
        self.arbitrage_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized arbitrage agent for flash loan opportunities.

            Your responsibilities:
            1. Analyze price differences across DEXs
            2. Calculate potential profits and costs
            3. Assess opportunity viability
            4. Rank opportunities by profitability
            5. Consider gas costs and slippage
            
            Analysis framework:
            - Identify profitable price differences
            - Calculate net profit after all costs
            - Assess execution complexity
            - Consider market volatility
            - Evaluate liquidity constraints
            
            Respond with JSON containing:
            - opportunity_found: Boolean indicating if viable opportunity exists
            - profit_analysis: Detailed profit breakdown
            - risk_factors: List of identified risks
            - execution_plan: Steps to execute the arbitrage
            - confidence_score: Float between 0 and 1
            - priority_level: HIGH, MEDIUM, or LOW
            """),
            ("human", "Market Data: {market_data}\nRequest: {request}")
        ])

    async def initialize(self):
        """Initialize the arbitrage agent"""
        try:
            logger.info(f"💰 Initializing Arbitrage Agent '{self.name}'...")
            
            # Register with tool registry
            if self.tool_registry:
                await self.register_tools()
            
            logger.info(f"✅ Arbitrage Agent '{self.name}' initialization completed")
            
        except Exception as e:
            logger.error(f"❌ Arbitrage Agent initialization failed: {e}")
            raise

    async def register_tools(self):
        """Register arbitrage-specific tools"""
        try:
            # Register arbitrage calculation tools
            await self.tool_registry.register_tool(
                "detect_arbitrage_opportunity",
                "Detect arbitrage opportunities between DEXs",
                self.detect_arbitrage_opportunity,
                {
                    "token_pair": {"type": "string", "description": "Trading pair (e.g., ETH/USDC)"},
                    "dex_prices": {"type": "object", "description": "Prices from different DEXs"},
                    "gas_price": {"type": "float", "description": "Current gas price in gwei"}
                },
                "arbitrage"
            )
            
            await self.tool_registry.register_tool(
                "calculate_arbitrage_profit",
                "Calculate potential arbitrage profit",
                self.calculate_arbitrage_profit,
                {
                    "buy_price": {"type": "float", "description": "Buy price"},
                    "sell_price": {"type": "float", "description": "Sell price"},
                    "amount": {"type": "float", "description": "Trade amount"},
                    "gas_cost": {"type": "float", "description": "Gas cost"}
                },
                "arbitrage"
            )
            
            logger.info("✅ Arbitrage tools registered")
            
        except Exception as e:
            logger.error(f"❌ Failed to register arbitrage tools: {e}")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process arbitrage requests within the agent workflow"""
        try:
            messages = state.get("messages", [])
            context = state.get("context", {})
            
            if not messages:
                return state
            
            # Get the latest message
            latest_message = messages[-1]
            request = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)
            
            logger.info(f"💰 Processing arbitrage request: {request[:100]}...")
            
            # Analyze arbitrage opportunity
            result = await self.analyze_arbitrage_opportunity(request, context)
            
            # Create response message
            response_msg = AIMessage(
                content=f"Arbitrage Analysis: {result.get('response', 'No response generated')}"
            )
            state["messages"].append(response_msg)
            
            # Update result
            state["result"] = result
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Arbitrage processing failed: {e}")
            error_msg = AIMessage(content=f"Arbitrage error: {str(e)}")
            state["messages"].append(error_msg)
            return state

    async def process_direct(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct arbitrage request"""
        try:
            return await self.analyze_arbitrage_opportunity(request, context)
            
        except Exception as e:
            logger.error(f"❌ Direct arbitrage processing failed: {e}")
            return {
                "response": f"Arbitrage processing error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def analyze_arbitrage_opportunity(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze arbitrage opportunity"""
        try:
            # Extract market data from context
            market_data = context.get("market_data", {})
            
            # Prepare analysis input
            analysis_input = {
                "market_data": str(market_data),
                "request": request
            }
            
            # Get LLM analysis
            response = await self.llm.ainvoke(
                self.arbitrage_analysis_prompt.format_messages(**analysis_input)
            )
            
            # Parse response
            analysis = self.parse_arbitrage_response(response.content)
            
            # Enhance with tool calculations if market data is available
            if market_data and "prices" in market_data:
                enhanced_analysis = await self.enhance_with_calculations(analysis, market_data)
                analysis.update(enhanced_analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Arbitrage analysis failed: {e}")
            return {
                "response": f"Arbitrage analysis error: {str(e)}",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    async def enhance_with_calculations(self, analysis: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance analysis with tool-based calculations"""
        try:
            enhanced = {}
            
            # Use profit calculation tool if available
            if self.tool_registry:
                prices = market_data.get("prices", {})
                if len(prices) >= 2:
                    price_list = list(prices.values())
                    buy_price = min(price_list)
                    sell_price = max(price_list)
                    
                    if sell_price > buy_price:
                        # Calculate profit using tool
                        profit_result = await self.tool_registry.execute_tool(
                            "calculate_arbitrage_profit",
                            buy_price=buy_price,
                            sell_price=sell_price,
                            amount=market_data.get("amount", 1000),  # Default amount
                            gas_cost=market_data.get("gas_cost", 50)  # Default gas cost
                        )
                        
                        if profit_result.get("success"):
                            enhanced["tool_calculations"] = profit_result["result"]
            
            return enhanced
            
        except Exception as e:
            logger.error(f"❌ Failed to enhance with calculations: {e}")
            return {}

    def parse_arbitrage_response(self, response: str) -> Dict[str, Any]:
        """Parse the arbitrage analysis response"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "response": response,
                    "confidence": parsed.get("confidence_score", 0.5),
                    "metadata": {
                        "opportunity_found": parsed.get("opportunity_found", False),
                        "profit_analysis": parsed.get("profit_analysis", {}),
                        "risk_factors": parsed.get("risk_factors", []),
                        "execution_plan": parsed.get("execution_plan", []),
                        "priority_level": parsed.get("priority_level", "MEDIUM")
                    }
                }
            
            # Fallback parsing
            opportunity_found = any(word in response.lower() for word in ["profitable", "opportunity", "arbitrage"])
            confidence = 0.7 if opportunity_found else 0.3
            
            return {
                "response": response,
                "confidence": confidence,
                "metadata": {
                    "opportunity_found": opportunity_found,
                    "parsing_method": "fallback"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse arbitrage response: {e}")
            return {
                "response": response,
                "confidence": 0.3,
                "metadata": {"error": str(e)}
            }

    # Tool implementations
    async def detect_arbitrage_opportunity(self, token_pair: str, dex_prices: Dict[str, float], gas_price: float) -> Dict[str, Any]:
        """Detect arbitrage opportunity between DEXs"""
        try:
            if not dex_prices or len(dex_prices) < 2:
                return {
                    "opportunity_found": False,
                    "reason": "Insufficient price data"
                }
            
            # Find price spread
            prices = list(dex_prices.values())
            min_price = min(prices)
            max_price = max(prices)
            price_spread = max_price - min_price
            spread_percentage = (price_spread / min_price) * 100
            
            # Find best DEXs
            buy_dex = None
            sell_dex = None
            for dex, price in dex_prices.items():
                if price == min_price:
                    buy_dex = dex
                if price == max_price:
                    sell_dex = dex
            
            # Estimate gas cost (simplified)
            estimated_gas_cost = gas_price * 0.0001  # Rough estimation
            
            # Check if profitable after gas costs
            min_profitable_spread = estimated_gas_cost * 2  # 2x gas cost for safety
            is_profitable = price_spread > min_profitable_spread
            
            return {
                "opportunity_found": is_profitable,
                "token_pair": token_pair,
                "buy_dex": buy_dex,
                "sell_dex": sell_dex,
                "buy_price": min_price,
                "sell_price": max_price,
                "price_spread": price_spread,
                "spread_percentage": spread_percentage,
                "estimated_gas_cost": estimated_gas_cost,
                "is_profitable": is_profitable,
                "all_prices": dex_prices
            }
            
        except Exception as e:
            logger.error(f"❌ Arbitrage detection failed: {e}")
            return {
                "opportunity_found": False,
                "error": str(e)
            }

    async def calculate_arbitrage_profit(self, buy_price: float, sell_price: float, amount: float, gas_cost: float) -> Dict[str, Any]:
        """Calculate arbitrage profit"""
        try:
            # Basic profit calculation
            revenue = sell_price * amount
            cost = buy_price * amount
            gross_profit = revenue - cost
            net_profit = gross_profit - gas_cost
            
            # Calculate percentages
            profit_percentage = (net_profit / cost) * 100 if cost > 0 else 0
            roi = (net_profit / (cost + gas_cost)) * 100 if (cost + gas_cost) > 0 else 0
            
            # Determine profitability
            is_profitable = net_profit > 0
            
            # Calculate minimum amount for profitability
            min_amount_profitable = gas_cost / (sell_price - buy_price) if sell_price > buy_price else float('inf')
            
            return {
                "amount": amount,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "revenue": revenue,
                "cost": cost,
                "gross_profit": gross_profit,
                "gas_cost": gas_cost,
                "net_profit": net_profit,
                "profit_percentage": profit_percentage,
                "roi": roi,
                "is_profitable": is_profitable,
                "min_amount_profitable": min_amount_profitable
            }
            
        except Exception as e:
            logger.error(f"❌ Profit calculation failed: {e}")
            return {
                "error": str(e),
                "is_profitable": False
            }
