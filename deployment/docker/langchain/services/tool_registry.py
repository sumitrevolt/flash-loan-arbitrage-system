"""
Tool Registry Service
====================

Service for managing and organizing tools available to agents
in the flash loan multi-agent system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import inspect

from utils.logger import setup_logger
from utils.config import get_config

logger = setup_logger(__name__)

class Tool:
    """Represents a tool that can be used by agents"""
    
    def __init__(self, name: str, description: str, func: Callable, 
                 parameters: Optional[Dict] = None, category: str = "general"):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}
        self.category = category
        self.usage_count = 0
        self.last_used = None
        self.created_at = datetime.now()

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool function"""
        try:
            self.usage_count += 1
            self.last_used = datetime.now()
            
            # Check if function is async
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)
            
            return {
                "success": True,
                "result": result,
                "tool_name": self.name,
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Tool '{self.name}' execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": self.name,
                "execution_time": datetime.now().isoformat()
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat()
        }

class ToolRegistry:
    """
    Registry for managing tools available to agents.
    
    Features:
    - Tool registration and discovery
    - Category-based organization
    - Usage tracking
    - Tool validation
    - Dynamic tool loading
    """
    
    def __init__(self):
        self.config = get_config()
        self.tools: Dict[str, Tool] = {}
        self.categories: Dict[str, List[str]] = {}
        
        logger.info("🔧 Tool Registry initialized")

    async def initialize(self):
        """Initialize the tool registry"""
        try:
            logger.info("🔧 Initializing Tool Registry...")
            
            # Register built-in tools
            await self.register_built_in_tools()
            
            # Load custom tools if available
            await self.load_custom_tools()
            
            logger.info(f"✅ Tool Registry initialization completed with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"❌ Tool Registry initialization failed: {e}")
            raise

    async def register_built_in_tools(self):
        """Register built-in tools"""
        try:
            # Mathematical tools
            await self.register_tool(
                "calculate_profit",
                "Calculate potential profit from arbitrage opportunity",
                self.calculate_profit,
                {
                    "buy_price": {"type": "float", "description": "Price to buy at"},
                    "sell_price": {"type": "float", "description": "Price to sell at"},
                    "amount": {"type": "float", "description": "Amount to trade"},
                    "gas_cost": {"type": "float", "description": "Estimated gas cost", "default": 0.0}
                },
                "financial"
            )
            
            await self.register_tool(
                "calculate_roi",
                "Calculate return on investment",
                self.calculate_roi,
                {
                    "initial_investment": {"type": "float", "description": "Initial investment amount"},
                    "final_value": {"type": "float", "description": "Final value"},
                    "gas_costs": {"type": "float", "description": "Total gas costs", "default": 0.0}
                },
                "financial"
            )
            
            # Price analysis tools
            await self.register_tool(
                "analyze_price_impact",
                "Analyze potential price impact of a trade",
                self.analyze_price_impact,
                {
                    "pool_liquidity": {"type": "float", "description": "Pool liquidity"},
                    "trade_amount": {"type": "float", "description": "Trade amount"},
                    "pool_fee": {"type": "float", "description": "Pool fee", "default": 0.003}
                },
                "analysis"
            )
            
            # Risk assessment tools
            await self.register_tool(
                "assess_risk",
                "Assess risk level of a trade",
                self.assess_risk,
                {
                    "profit_potential": {"type": "float", "description": "Potential profit"},
                    "gas_cost": {"type": "float", "description": "Gas cost"},
                    "slippage": {"type": "float", "description": "Expected slippage"},
                    "liquidity": {"type": "float", "description": "Pool liquidity"}
                },
                "risk"
            )
            
            # Data tools
            await self.register_tool(
                "get_current_time",
                "Get current timestamp",
                self.get_current_time,
                {},
                "utility"
            )
            
            await self.register_tool(
                "format_currency",
                "Format currency amount",
                self.format_currency,
                {
                    "amount": {"type": "float", "description": "Amount to format"},
                    "currency": {"type": "string", "description": "Currency symbol", "default": "USD"}
                },
                "utility"
            )
            
            logger.info("✅ Built-in tools registered successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to register built-in tools: {e}")

    async def load_custom_tools(self):
        """Load custom tools from configuration or external sources"""
        try:
            # This would load custom tools from files or plugins
            # For now, we'll just log that it's available
            logger.info("ℹ️ Custom tool loading is ready (no custom tools configured)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load custom tools: {e}")

    async def register_tool(self, name: str, description: str, func: Callable, 
                          parameters: Optional[Dict] = None, category: str = "general") -> bool:
        """Register a new tool"""
        try:
            if name in self.tools:
                logger.warning(f"⚠️ Tool '{name}' already exists, updating...")
            
            # Validate function
            if not callable(func):
                raise ValueError(f"Function for tool '{name}' is not callable")
            
            # Create tool
            tool = Tool(name, description, func, parameters, category)
            self.tools[name] = tool
            
            # Update categories
            if category not in self.categories:
                self.categories[category] = []
            if name not in self.categories[category]:
                self.categories[category].append(name)
            
            logger.info(f"✅ Tool '{name}' registered in category '{category}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register tool '{name}': {e}")
            return False

    async def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)

    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name"""
        try:
            tool = self.tools.get(name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{name}' not found",
                    "tool_name": name
                }
            
            return await tool.execute(**kwargs)
            
        except Exception as e:
            logger.error(f"❌ Failed to execute tool '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": name
            }

    async def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available tools"""
        try:
            if category:
                tool_names = self.categories.get(category, [])
                return [self.tools[name].to_dict() for name in tool_names if name in self.tools]
            else:
                return [tool.to_dict() for tool in self.tools.values()]
                
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
            return []

    async def get_categories(self) -> List[str]:
        """Get list of tool categories"""
        return list(self.categories.keys())

    async def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        try:
            stats = {
                "total_tools": len(self.tools),
                "total_categories": len(self.categories),
                "total_executions": sum(tool.usage_count for tool in self.tools.values()),
                "most_used_tools": [],
                "categories": {}
            }
            
            # Most used tools
            sorted_tools = sorted(self.tools.values(), key=lambda t: t.usage_count, reverse=True)
            stats["most_used_tools"] = [
                {"name": tool.name, "usage_count": tool.usage_count}
                for tool in sorted_tools[:10]
            ]
            
            # Category statistics
            for category, tool_names in self.categories.items():
                category_tools = [self.tools[name] for name in tool_names if name in self.tools]
                stats["categories"][category] = {
                    "tool_count": len(category_tools),
                    "total_usage": sum(tool.usage_count for tool in category_tools)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get tool usage stats: {e}")
            return {}

    # Built-in tool implementations
    async def calculate_profit(self, buy_price: float, sell_price: float, 
                             amount: float, gas_cost: float = 0.0) -> Dict[str, Any]:
        """Calculate profit from arbitrage"""
        try:
            revenue = sell_price * amount
            cost = buy_price * amount
            gross_profit = revenue - cost
            net_profit = gross_profit - gas_cost
            profit_percentage = (net_profit / cost) * 100 if cost > 0 else 0
            
            return {
                "revenue": revenue,
                "cost": cost,
                "gross_profit": gross_profit,
                "gas_cost": gas_cost,
                "net_profit": net_profit,
                "profit_percentage": profit_percentage,
                "is_profitable": net_profit > 0
            }
            
        except Exception as e:
            raise ValueError(f"Profit calculation failed: {e}")

    async def calculate_roi(self, initial_investment: float, final_value: float, 
                          gas_costs: float = 0.0) -> Dict[str, Any]:
        """Calculate return on investment"""
        try:
            total_cost = initial_investment + gas_costs
            net_return = final_value - total_cost
            roi_percentage = (net_return / total_cost) * 100 if total_cost > 0 else 0
            
            return {
                "initial_investment": initial_investment,
                "gas_costs": gas_costs,
                "total_cost": total_cost,
                "final_value": final_value,
                "net_return": net_return,
                "roi_percentage": roi_percentage,
                "is_profitable": net_return > 0
            }
            
        except Exception as e:
            raise ValueError(f"ROI calculation failed: {e}")

    async def analyze_price_impact(self, pool_liquidity: float, trade_amount: float, 
                                 pool_fee: float = 0.003) -> Dict[str, Any]:
        """Analyze price impact of a trade"""
        try:
            # Simplified price impact calculation
            impact_percentage = (trade_amount / pool_liquidity) * 100
            
            # Estimate slippage
            slippage = impact_percentage * 0.5  # Simplified slippage estimation
            
            # Categorize impact
            if impact_percentage < 0.1:
                impact_level = "MINIMAL"
            elif impact_percentage < 1.0:
                impact_level = "LOW"
            elif impact_percentage < 5.0:
                impact_level = "MEDIUM"
            else:
                impact_level = "HIGH"
            
            return {
                "pool_liquidity": pool_liquidity,
                "trade_amount": trade_amount,
                "impact_percentage": impact_percentage,
                "estimated_slippage": slippage,
                "impact_level": impact_level,
                "pool_fee": pool_fee,
                "recommended": impact_percentage < 2.0
            }
            
        except Exception as e:
            raise ValueError(f"Price impact analysis failed: {e}")

    async def assess_risk(self, profit_potential: float, gas_cost: float, 
                        slippage: float, liquidity: float) -> Dict[str, Any]:
        """Assess risk level of a trade"""
        try:
            # Risk scoring (0-100, higher is riskier)
            risk_score = 0
            
            # Profit to gas cost ratio
            if gas_cost > 0:
                profit_ratio = profit_potential / gas_cost
                if profit_ratio < 2:
                    risk_score += 30
                elif profit_ratio < 5:
                    risk_score += 15
            
            # Slippage risk
            if slippage > 2:
                risk_score += 25
            elif slippage > 1:
                risk_score += 10
            
            # Liquidity risk
            if liquidity < 100000:  # Low liquidity
                risk_score += 20
            elif liquidity < 500000:
                risk_score += 10
            
            # Determine risk level
            if risk_score < 20:
                risk_level = "LOW"
            elif risk_score < 50:
                risk_level = "MEDIUM"
            elif risk_score < 80:
                risk_level = "HIGH"
            else:
                risk_level = "CRITICAL"
            
            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "profit_potential": profit_potential,
                "gas_cost": gas_cost,
                "slippage": slippage,
                "liquidity": liquidity,
                "recommended": risk_score < 50
            }
            
        except Exception as e:
            raise ValueError(f"Risk assessment failed: {e}")

    async def get_current_time(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()

    async def format_currency(self, amount: float, currency: str = "USD") -> str:
        """Format currency amount"""
        try:
            if currency == "USD":
                return f"${amount:,.2f}"
            elif currency == "ETH":
                return f"{amount:.6f} ETH"
            else:
                return f"{amount:.2f} {currency}"
                
        except Exception as e:
            raise ValueError(f"Currency formatting failed: {e}")
