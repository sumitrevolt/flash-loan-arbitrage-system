#!/usr/bin/env python3
"""
Enhanced Discord Bot for Flash Loan Arbitrage System
Integrates with all 21 MCP servers and provides comprehensive control
"""

import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import redis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FlashLoanDiscordBot')

class FlashLoanBot(commands.Bot):
    """Enhanced Discord bot for flash loan arbitrage system"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Flash Loan Arbitrage System Control Bot'
        )
        
        # Configuration
        self.config = {
            'mcp_coordinator_url': os.getenv('MCP_COORDINATOR_URL', 'http://mcp-coordinator:9000'),
            'aave_executor_url': os.getenv('AAVE_EXECUTOR_URL', 'http://aave-flash-loan-executor:8001'),
            'price_oracle_url': os.getenv('PRICE_ORACLE_URL', 'http://price-oracle-mcp:8005'),
            'arbitrage_detector_url': os.getenv('ARBITRAGE_DETECTOR_URL', 'http://arbitrage-detector:8010'),
            'redis_url': os.getenv('REDIS_URL', 'redis://redis:6379')
        }
        
        # State management
        self.system_status = {}
        self.active_trades = {}
        self.performance_metrics = {}
        self.alerts_enabled = True
        
        # Redis connection
        try:
            self.redis_client = redis.from_url(self.config['redis_url'], decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # HTTP session
        self.session = None
        
        # MCP server endpoints
        self.mcp_servers = {
            'coordinator': self.config['mcp_coordinator_url'],
            'aave_executor': self.config['aave_executor_url'],
            'price_oracle': self.config['price_oracle_url'],
            'arbitrage_detector': self.config['arbitrage_detector_url'],
            'context7': 'http://context7-mcp:8004',
            'grok3': 'http://grok3-mcp:3003',
            'matic': 'http://matic-mcp:8002',
            'evm': 'http://evm-mcp:8003',
            'foundry': 'http://foundry-mcp:8007',
            'contract_executor': 'http://contract-executor-mcp:3005',
            'flash_loan_strategist': 'http://flash-loan-strategist-mcp:3004'
        }
    
    async def setup_hook(self):
        """Setup hook called when bot starts"""
        self.session = aiohttp.ClientSession()
        
        # Start background tasks
        self.monitor_system.start()
        self.check_opportunities.start()
        self.update_metrics.start()
        
        logger.info("Bot setup completed")
    
    async def close(self):
        """Cleanup when bot shuts down"""
        if self.session:
            await self.session.close()
        
        # Stop background tasks
        self.monitor_system.cancel()
        self.check_opportunities.cancel()
        self.update_metrics.cancel()
        
        await super().close()
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'Bot logged in as {self.user} (ID: {self.user.id})')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Flash Loan Opportunities"
        )
        await self.change_presence(activity=activity)
        
        # Send startup message to configured channel
        startup_channel_id = os.getenv('STARTUP_CHANNEL_ID')
        if startup_channel_id:
            channel = self.get_channel(int(startup_channel_id))
            if channel:
                embed = discord.Embed(
                    title="🚀 Flash Loan Bot Online",
                    description="All systems operational. Ready for arbitrage!",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                await channel.send(embed=embed)
    
    async def make_request(self, url: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to MCP server"""
        try:
            if not self.session:
                return None
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            if method.upper() == 'GET':
                async with self.session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.json()
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Request failed to {url}: {e}")
            return None
    
    @tasks.loop(minutes=1)
    async def monitor_system(self):
        """Monitor system health"""
        try:
            # Check all MCP servers
            server_status = {}
            
            for server_name, url in self.mcp_servers.items():
                health_url = f"{url}/health"
                status = await self.make_request(health_url)
                
                if status:
                    server_status[server_name] = {
                        'status': 'healthy',
                        'last_check': datetime.utcnow().isoformat(),
                        'details': status
                    }
                else:
                    server_status[server_name] = {
                        'status': 'unhealthy',
                        'last_check': datetime.utcnow().isoformat(),
                        'details': None
                    }
            
            self.system_status = server_status
            
            # Store in Redis
            if self.redis_client:
                self.redis_client.setex(
                    'system_status',
                    300,  # 5 minutes TTL
                    json.dumps(server_status, default=str)
                )
            
            # Check for critical failures
            unhealthy_servers = [
                name for name, status in server_status.items()
                if status['status'] == 'unhealthy'
            ]
            
            if unhealthy_servers and self.alerts_enabled:
                await self.send_alert(
                    f"⚠️ **System Alert**: {len(unhealthy_servers)} servers unhealthy: {', '.join(unhealthy_servers)}"
                )
            
        except Exception as e:
            logger.error(f"Error monitoring system: {e}")
    
    @tasks.loop(minutes=5)
    async def check_opportunities(self):
        """Check for arbitrage opportunities"""
        try:
            opportunities_url = f"{self.config['arbitrage_detector_url']}/opportunities"
            opportunities = await self.make_request(opportunities_url)
            
            if opportunities and opportunities.get('opportunities'):
                top_opportunities = opportunities['opportunities'][:3]  # Top 3
                
                if top_opportunities:
                    # Send opportunity alert
                    embed = discord.Embed(
                        title="💰 Arbitrage Opportunities Detected",
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow()
                    )
                    
                    for i, opp in enumerate(top_opportunities, 1):
                        profit_pct = opp.get('profit_percentage', 0)
                        if profit_pct > 0.5:  # Only show significant opportunities
                            embed.add_field(
                                name=f"#{i} {opp.get('pair', 'Unknown')}",
                                value=f"Profit: {profit_pct:.2f}%\nBuy: {opp.get('buy_dex', 'Unknown')}\nSell: {opp.get('sell_dex', 'Unknown')}",
                                inline=True
                            )
                    
                    if embed.fields:  # Only send if there are significant opportunities
                        await self.send_alert(embed=embed)
            
        except Exception as e:
            logger.error(f"Error checking opportunities: {e}")
    
    @tasks.loop(minutes=10)
    async def update_metrics(self):
        """Update performance metrics"""
        try:
            # Get metrics from coordinator
            metrics_url = f"{self.config['mcp_coordinator_url']}/system_status"
            metrics = await self.make_request(metrics_url)
            
            if metrics:
                self.performance_metrics = metrics
                
                # Store in Redis
                if self.redis_client:
                    self.redis_client.setex(
                        'performance_metrics',
                        600,  # 10 minutes TTL
                        json.dumps(metrics, default=str)
                    )
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def send_alert(self, message: str = None, embed: discord.Embed = None):
        """Send alert to configured channel"""
        try:
            alert_channel_id = os.getenv('ALERT_CHANNEL_ID')
            if not alert_channel_id:
                return
            
            channel = self.get_channel(int(alert_channel_id))
            if not channel:
                return
            
            if embed:
                await channel.send(embed=embed)
            elif message:
                await channel.send(message)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")

# Bot commands
bot = FlashLoanBot()

@bot.command(name='status')
async def status_command(ctx):
    """Get system status"""
    try:
        embed = discord.Embed(
            title="🏦 Flash Loan System Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if bot.system_status:
            healthy_count = sum(1 for s in bot.system_status.values() if s['status'] == 'healthy')
            total_count = len(bot.system_status)
            
            embed.add_field(
                name="System Health",
                value=f"{healthy_count}/{total_count} servers healthy",
                inline=False
            )
            
            # Show unhealthy servers
            unhealthy = [name for name, status in bot.system_status.items() if status['status'] == 'unhealthy']
            if unhealthy:
                embed.add_field(
                    name="⚠️ Unhealthy Servers",
                    value=", ".join(unhealthy),
                    inline=False
                )
            
            # Performance metrics
            if bot.performance_metrics:
                metrics = bot.performance_metrics
                embed.add_field(
                    name="📊 Performance",
                    value=f"Active Tasks: {metrics.get('active_tasks', 0)}\nSuccess Rate: {metrics.get('success_rate', 0):.1%}",
                    inline=True
                )
        else:
            embed.add_field(
                name="Status",
                value="System status not available",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting status: {e}")

@bot.command(name='opportunities')
async def opportunities_command(ctx):
    """Get current arbitrage opportunities"""
    try:
        opportunities_url = f"{bot.config['arbitrage_detector_url']}/opportunities"
        data = await bot.make_request(opportunities_url)
        
        if not data or not data.get('opportunities'):
            await ctx.send("📊 No arbitrage opportunities found at the moment.")
            return
        
        opportunities = data['opportunities'][:5]  # Top 5
        
        embed = discord.Embed(
            title="💰 Current Arbitrage Opportunities",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        for i, opp in enumerate(opportunities, 1):
            profit_pct = opp.get('profit_percentage', 0)
            net_profit = opp.get('net_profit', 0)
            
            embed.add_field(
                name=f"#{i} {opp.get('pair', 'Unknown')}",
                value=f"💰 Profit: {profit_pct:.3f}% (${net_profit:.2f})\n"
                      f"📈 Buy: {opp.get('buy_dex', 'Unknown')} @ ${opp.get('buy_price', 0):.6f}\n"
                      f"📉 Sell: {opp.get('sell_dex', 'Unknown')} @ ${opp.get('sell_price', 0):.6f}\n"
                      f"⏰ Confidence: {opp.get('confidence_score', 0):.1%}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting opportunities: {e}")

@bot.command(name='execute')
async def execute_flash_loan(ctx, opportunity_id: str = None):
    """Execute a flash loan arbitrage"""
    try:
        if not opportunity_id:
            await ctx.send("❌ Please provide an opportunity ID. Use `!opportunities` to see available opportunities.")
            return
        
        # Get opportunity details
        opp_url = f"{bot.config['arbitrage_detector_url']}/opportunities/{opportunity_id}"
        opportunity = await bot.make_request(opp_url)
        
        if not opportunity:
            await ctx.send(f"❌ Opportunity {opportunity_id} not found or expired.")
            return
        
        # Confirm execution
        embed = discord.Embed(
            title="⚡ Flash Loan Execution Request",
            description=f"Executing opportunity: {opportunity.get('pair', 'Unknown')}",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="Details",
            value=f"Expected Profit: {opportunity.get('profit_percentage', 0):.3f}%\n"
                  f"Net Profit: ${opportunity.get('net_profit', 0):.2f}\n"
                  f"Buy DEX: {opportunity.get('buy_dex', 'Unknown')}\n"
                  f"Sell DEX: {opportunity.get('sell_dex', 'Unknown')}",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Execute via coordinator
        execute_url = f"{bot.config['mcp_coordinator_url']}/execute_flash_loan"
        execution_data = {
            'opportunity_id': opportunity_id,
            'asset': opportunity.get('pair', '').split('/')[0],
            'amount': 10000,  # Default amount
            'expected_profit': opportunity.get('net_profit', 0),
            'arbitrage_path': [
                {'dex': opportunity.get('buy_dex'), 'action': 'buy'},
                {'dex': opportunity.get('sell_dex'), 'action': 'sell'}
            ]
        }
        
        result: str = await bot.make_request(execute_url, 'POST', execution_data)
        
        if result:
            embed = discord.Embed(
                title="✅ Flash Loan Executed",
                description=f"Task ID: {result.get('task_id', 'Unknown')}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Status",
                value=result.get('status', 'Unknown'),
                inline=True
            )
            
            await ctx.send(embed=embed)
            
            # Store active trade
            bot.active_trades[result.get('task_id')] = {
                'opportunity_id': opportunity_id,
                'started_at': datetime.utcnow(),
                'status': 'executing'
            }
        else:
            await ctx.send("❌ Failed to execute flash loan. Check system status.")
        
    except Exception as e:
        await ctx.send(f"❌ Error executing flash loan: {e}")

@bot.command(name='prices')
async def prices_command(ctx, symbol: str = None):
    """Get current token prices"""
    try:
        if symbol:
            # Get specific token price
            price_url = f"{bot.config['price_oracle_url']}/prices/{symbol.upper()}"
            data = await bot.make_request(price_url)
            
            if data:
                embed = discord.Embed(
                    title=f"💰 {symbol.upper()} Price",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="Current Price",
                    value=f"${data.get('price', 0):.6f}",
                    inline=True
                )
                
                embed.add_field(
                    name="Source",
                    value=data.get('source', 'Unknown'),
                    inline=True
                )
                
                embed.add_field(
                    name="Confidence",
                    value=f"{data.get('confidence', 0):.1%}",
                    inline=True
                )
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Price not found for {symbol.upper()}")
        else:
            # Get all prices
            prices_url = f"{bot.config['price_oracle_url']}/prices"
            data = await bot.make_request(prices_url)
            
            if data:
                embed = discord.Embed(
                    title="💰 Current Token Prices",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                # Show top tokens
                count = 0
                for symbol, price_data in data.items():
                    if count >= 10:  # Limit to 10 tokens
                        break
                    
                    embed.add_field(
                        name=symbol,
                        value=f"${price_data.get('price', 0):.6f}",
                        inline=True
                    )
                    count += 1
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Unable to fetch prices")
        
    except Exception as e:
        await ctx.send(f"❌ Error getting prices: {e}")

@bot.command(name='metrics')
async def metrics_command(ctx):
    """Get performance metrics"""
    try:
        if not bot.performance_metrics:
            await ctx.send("📊 Performance metrics not available")
            return
        
        metrics = bot.performance_metrics
        
        embed = discord.Embed(
            title="📊 Performance Metrics",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="System Stats",
            value=f"Active Agents: {len([a for a in bot.system_status.values() if a['status'] == 'healthy'])}\n"
                  f"Active Tasks: {metrics.get('active_tasks', 0)}\n"
                  f"Success Rate: {metrics.get('success_rate', 0):.1%}",
            inline=True
        )
        
        embed.add_field(
            name="Trading Stats",
            value=f"Total Profit: ${metrics.get('total_profit', 0):.2f}\n"
                  f"Avg Execution Time: {metrics.get('average_execution_time', 0):.1f}s\n"
                  f"Opportunities Found: {metrics.get('opportunities_detected', 0)}",
            inline=True
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error getting metrics: {e}")

@bot.command(name='alerts')
async def toggle_alerts(ctx, enabled: str = None):
    """Toggle system alerts"""
    try:
        if enabled is None:
            status = "enabled" if bot.alerts_enabled else "disabled"
            await ctx.send(f"🔔 Alerts are currently **{status}**")
            return
        
        if enabled.lower() in ['on', 'true', 'enable', 'yes']:
            bot.alerts_enabled = True
            await ctx.send("🔔 Alerts **enabled**")
        elif enabled.lower() in ['off', 'false', 'disable', 'no']:
            bot.alerts_enabled = False
            await ctx.send("🔕 Alerts **disabled**")
        else:
            await ctx.send("❌ Use 'on' or 'off' to toggle alerts")
        
    except Exception as e:
        await ctx.send(f"❌ Error toggling alerts: {e}")

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="🤖 Flash Loan Bot Commands",
        description="Available commands for the Flash Loan Arbitrage System",
        color=discord.Color.blue()
    )
    
    commands_list = [
        ("!status", "Get system health status"),
        ("!opportunities", "View current arbitrage opportunities"),
        ("!execute <id>", "Execute a flash loan arbitrage"),
        ("!prices [symbol]", "Get token prices"),
        ("!metrics", "View performance metrics"),
        ("!alerts [on/off]", "Toggle system alerts"),
        ("!help", "Show this help message")
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await ctx.send(embed=embed)

def main():
    """Main entry point"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        return
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

if __name__ == '__main__':
    main()