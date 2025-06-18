import asyncio\n#!/usr/bin/env python3
"""
Enhanced Discord Bot for MCP System
===================================
Full integration with 21 MCP servers and 10 agents.
Provides monitoring, control, and real-time updates.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import aiohttp
import redis
import discord
from discord.ext import commands

# Configuration
MCP_COORD_URL = os.getenv("MCP_COORD_URL", "http://localhost:8000")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
GUILD_ID = int(os.getenv("GUILD_ID", "123456789"))
ADMIN_ROLE = os.getenv("ADMIN_ROLE", "Administrator")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for system status
service_status_cache: Dict[str, Any] = {
    'mcp_servers': {},
    'agents': {},
    'last_update': None
}

class MCPDiscordBot(commands.Bot):
    """Enhanced Discord bot for MCP system management"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize connections
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        self.logs_channel: Optional[discord.TextChannel] = None
          # Setup Redis
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)  # type: ignore
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            
    async def setup_hook(self) -> None:
        """Setup async components"""
        self.session = aiohttp.ClientSession()
        
        # Find logs channel
        guild = self.get_guild(GUILD_ID)
        if guild:
            channel = discord.utils.get(guild.text_channels, name="mcp-logs")
            if isinstance(channel, discord.TextChannel):
                self.logs_channel = channel
            
        logger.info("Discord bot initialized")
        
    async def fetch_system_status(self) -> Dict[str, Any]:
        """Fetch complete system status"""
        if not self.session:
            return {}
            
        try:
            async with self.session.get(f"{MCP_COORD_URL}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    service_status_cache['mcp_servers'] = data.get('servers', {})
                    service_status_cache['agents'] = data.get('agents', {})
                    service_status_cache['last_update'] = datetime.now(timezone.utc)
                    return data
        except Exception as e:
            logger.error(f"Failed to fetch system status: {e}")
        return {}
            
    async def get_metrics(self) -> Dict[str, Any]:
        """Fetch Prometheus metrics"""
        if not self.session:
            return {}
            
        try:
            async with self.session.get(f"{PROMETHEUS_URL}/api/v1/query", 
                                      params={'query': 'up'}) as response:
                if response.status == 200:
                    data = await response.json()
                    result: str = data.get('data', {}).get('result', [])
                    return {'metrics': result}
        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
        return {}

    def create_status_embed(self, title: str, status_data: Dict[str, Any], color: discord.Color) -> discord.Embed:
        """Create a formatted status embed"""
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Group services by status with proper type hints
        healthy: List[str] = []
        unhealthy: List[str] = []
        unknown: List[str] = []
        
        for name, data in status_data.items():
            status = data.get('status', 'unknown')
            if status == 'healthy':
                healthy.append(name)
            elif status in ['unhealthy', 'error']:
                unhealthy.append(name)
            else:
                unknown.append(name)
                
        if healthy:
            embed.add_field(
                name=f"✅ Healthy ({len(healthy)})",
                value=", ".join(healthy[:10]) + ("..." if len(healthy) > 10 else ""),
                inline=False
            )
            
        if unhealthy:
            embed.add_field(
                name=f"❌ Unhealthy ({len(unhealthy)})",
                value=", ".join(unhealthy[:10]) + ("..." if len(unhealthy) > 10 else ""),
                inline=False
            )
            
        if unknown:
            embed.add_field(
                name=f"❓ Unknown ({len(unknown)})",
                value=", ".join(unknown[:10]) + ("..." if len(unknown) > 10 else ""),
                inline=False
            )
            
        return embed
        
    async def close(self) -> None:
        """Cleanup when bot closes"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            self.redis_client.close()
        await super().close()

# Create bot instance
mcp_bot = MCPDiscordBot()

def has_admin_role():
    """Check if user has admin role"""
    def predicate(ctx: commands.Context[commands.Bot]) -> bool:
        if not ctx.guild:
            return False
        if hasattr(ctx.author, 'guild_permissions') and ctx.author.guild_permissions.administrator:  # type: ignore
            return True
        return any(role.name == ADMIN_ROLE for role in getattr(ctx.author, 'roles', []))  # type: ignore
    return commands.check(predicate)

@mcp_bot.command(name='status')
async def system_status(ctx: commands.Context[commands.Bot]) -> None:
    """Get overall system status"""
    
    try:
        # Get system status
        status_data = await mcp_bot.fetch_system_status()
        
        if not status_data:
            embed = discord.Embed(
                title="❌ System Status",
                description="Unable to fetch system status",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return
            
        # Create comprehensive status embed
        total_servers = len(status_data.get('servers', {}))
        total_agents = len(status_data.get('agents', {}))
        
        healthy_servers = sum(1 for s in status_data.get('servers', {}).values() 
                            if s.get('status') == 'healthy')
        healthy_agents = sum(1 for a in status_data.get('agents', {}).values() 
                           if a.get('status') == 'healthy')
        
        embed = discord.Embed(
            title="🖥️ MCP System Status",
            color=discord.Color.green() if (healthy_servers == total_servers and 
                                          healthy_agents == total_agents) else discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="📊 Overview",
            value=f"**Servers:** {healthy_servers}/{total_servers} healthy\n"
                  f"**Agents:** {healthy_agents}/{total_agents} healthy",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Send detailed embeds
        if status_data.get('servers'):
            server_embed = mcp_bot.create_status_embed(
                "🔧 MCP Servers Status",
                status_data['servers'], 
                discord.Color.blue()
            )
            await ctx.send(embed=server_embed)
            
        if status_data.get('agents'):
            agent_embed = mcp_bot.create_status_embed(
                "🤖 Agent Status",
                status_data['agents'],
                discord.Color.purple()
            )
            await ctx.send(embed=agent_embed)
            
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to get system status: {str(e)}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

@mcp_bot.command(name='metrics')
async def prometheus_metrics(ctx: commands.Context[commands.Bot]) -> None:
    """Get Prometheus metrics"""
    
    try:
        metrics_data = await mcp_bot.get_metrics()
        
        if not metrics_data:
            embed = discord.Embed(
                title="❌ Metrics",
                description="Unable to fetch Prometheus metrics",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return
            
        metrics_list = metrics_data.get('metrics', [])
        up_services = sum(1 for m in metrics_list if float(m.get('value', [0, 0])[1]) == 1)
        total_services = len(metrics_list)
        
        embed = discord.Embed(
            title="📈 Prometheus Metrics",
            color=discord.Color.green() if up_services == total_services else discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="📊 Service Health",
            value=f"**Up:** {up_services}/{total_services} services",
            inline=False
        )
        
        # Show sample metrics
        if metrics_list:
            sample_metrics = metrics_list[:5]
            metrics_text = "\n".join([
                f"**{m.get('metric', {}).get('instance', 'Unknown')}:** "
                f"{'🟢' if float(m.get('value', [0, 0])[1]) == 1 else '🔴'}"
                for m in sample_metrics
            ])
            
            embed.add_field(
                name="🔍 Sample Services",
                value=metrics_text + ("..." if len(metrics_list) > 5 else ""),
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in metrics command: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to get metrics: {str(e)}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

@mcp_bot.command(name='restart')
@has_admin_role()
async def restart_service(ctx: commands.Context[commands.Bot], service_name: str) -> None:
    """Restart a specific MCP service"""
    
    if not mcp_bot.session:
        embed = discord.Embed(
            title="❌ Error",
            description="Bot session not initialized",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)
        return
    
    try:
        async with mcp_bot.session.post(
            f"{MCP_COORD_URL}/restart/{service_name}"
        ) as response:
            if response.status == 200:
                result: str = await response.json()
                embed = discord.Embed(
                    title="✅ Service Restart",
                    description=f"Successfully restarted **{service_name}**",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(
                    name="📋 Details",
                    value=result.get('message', 'Restart initiated'),
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Restart Failed",
                    description=f"Failed to restart **{service_name}**",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(
                    name="📋 Details",
                    value=f"HTTP {response.status}",
                    inline=False
                )
                
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error restarting service {service_name}: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to restart **{service_name}**: {str(e)}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

@mcp_bot.event
async def on_ready() -> None:
    """Bot ready event"""
    logger.info(f'{mcp_bot.user} has connected to Discord!')
    
    # Set bot status
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="MCP System Status"
    )
    await mcp_bot.change_presence(activity=activity)

@mcp_bot.event  
async def on_command_error(ctx: commands.Context[commands.Bot], error: commands.CommandError) -> None:
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.CheckFailure):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You don't have permission to use this command",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)
    else:
        logger.error(f"Command error: {error}")
        embed = discord.Embed(
            title="❌ Command Error", 
            description=f"An error occurred: {str(error)}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN environment variable not set")
        exit(1)
    
    try:
        mcp_bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
