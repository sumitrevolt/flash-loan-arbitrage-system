#!/usr/bin/env node
/**
 * Claude Desktop Bridge Server
 * Bridges Claude Desktop with MCP servers and AI agents
 */

const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const Redis = require('redis');

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

// Configuration
const PORT = process.env.PORT || 8080;
const WEB_PORT = process.env.WEB_PORT || 9090;
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379';
const MCP_CONFIG_PATH = process.env.MCP_SERVERS_CONFIG || '/app/config/claude_mcp_config.json';

// Redis client
const redis = Redis.createClient({ url: REDIS_URL });

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Enable CORS
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    next();
});

// MCP Server Management
class MCPServerManager {
    constructor() {
        this.servers = new Map();
        this.config = this.loadConfig();
    }

    loadConfig() {
        try {
            if (fs.existsSync(MCP_CONFIG_PATH)) {
                const config = JSON.parse(fs.readFileSync(MCP_CONFIG_PATH, 'utf8'));
                return config.mcpServers || {};
            }
        } catch (error) {
            console.error('Error loading MCP config:', error);
        }
        return {};
    }

    async startServer(serverName, serverConfig) {
        if (this.servers.has(serverName)) {
            console.log(`Server ${serverName} already running`);
            return;
        }

        console.log(`Starting MCP server: ${serverName}`);
        
        const process = spawn(serverConfig.command, serverConfig.args, {
            cwd: serverConfig.cwd || '/app',
            env: { ...process.env, ...serverConfig.env },
            stdio: ['pipe', 'pipe', 'pipe']
        });

        process.stdout.on('data', (data) => {
            console.log(`[${serverName}] ${data.toString().trim()}`);
            this.broadcastServerLog(serverName, data.toString());
        });

        process.stderr.on('data', (data) => {
            console.error(`[${serverName}] ERROR: ${data.toString().trim()}`);
            this.broadcastServerLog(serverName, data.toString(), 'error');
        });

        process.on('close', (code) => {
            console.log(`[${serverName}] Process exited with code ${code}`);
            this.servers.delete(serverName);
            this.broadcastServerStatus(serverName, 'stopped');
        });

        this.servers.set(serverName, {
            process,
            config: serverConfig,
            status: 'running',
            startTime: new Date()
        });

        this.broadcastServerStatus(serverName, 'running');
        
        // Store server info in Redis
        await redis.hset(`mcp:servers:${serverName}`, {
            status: 'running',
            startTime: new Date().toISOString(),
            config: JSON.stringify(serverConfig)
        });
    }

    async stopServer(serverName) {
        const serverInfo = this.servers.get(serverName);
        if (!serverInfo) {
            console.log(`Server ${serverName} not found`);
            return;
        }

        console.log(`Stopping MCP server: ${serverName}`);
        serverInfo.process.kill('SIGTERM');
        this.servers.delete(serverName);
        
        await redis.hdel(`mcp:servers:${serverName}`, 'status', 'startTime', 'config');
        this.broadcastServerStatus(serverName, 'stopped');
    }

    async startAllServers() {
        console.log('Starting all MCP servers...');
        
        for (const [serverName, serverConfig] of Object.entries(this.config)) {
            try {
                await this.startServer(serverName, serverConfig);
                // Small delay between server starts
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                console.error(`Failed to start ${serverName}:`, error);
            }
        }
    }

    getServerStatus() {
        const status = {};
        for (const [name, info] of this.servers) {
            status[name] = {
                status: info.status,
                startTime: info.startTime,
                uptime: Date.now() - info.startTime.getTime()
            };
        }
        return status;
    }

    broadcastServerLog(serverName, message, level = 'info') {
        this.broadcast({
            type: 'server_log',
            server: serverName,
            message: message.trim(),
            level,
            timestamp: new Date().toISOString()
        });
    }

    broadcastServerStatus(serverName, status) {
        this.broadcast({
            type: 'server_status',
            server: serverName,
            status,
            timestamp: new Date().toISOString()
        });
    }

    broadcast(message) {
        wss.clients.forEach(client => {
            if (client.readyState === client.OPEN) {
                client.send(JSON.stringify(message));
            }
        });
    }
}

// Initialize MCP Server Manager
const mcpManager = new MCPServerManager();

// WebSocket handling
wss.on('connection', (ws) => {
    console.log('New WebSocket connection');
    
    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            
            switch (data.type) {
                case 'get_server_status':
                    ws.send(JSON.stringify({
                        type: 'server_status_response',
                        servers: mcpManager.getServerStatus()
                    }));
                    break;
                    
                case 'start_server':
                    if (data.serverName && mcpManager.config[data.serverName]) {
                        await mcpManager.startServer(data.serverName, mcpManager.config[data.serverName]);
                    }
                    break;
                    
                case 'stop_server':
                    if (data.serverName) {
                        await mcpManager.stopServer(data.serverName);
                    }
                    break;
            }
        } catch (error) {
            console.error('WebSocket message error:', error);
        }
    });
    
    ws.on('close', () => {
        console.log('WebSocket connection closed');
    });
});

// API Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        servers: mcpManager.getServerStatus(),
        redis_connected: redis.isReady
    });
});

app.get('/api/servers', (req, res) => {
    res.json({
        servers: mcpManager.getServerStatus(),
        config: mcpManager.config
    });
});

app.post('/api/servers/:name/start', async (req, res) => {
    const { name } = req.params;
    const serverConfig = mcpManager.config[name];
    
    if (!serverConfig) {
        return res.status(404).json({ error: 'Server not found' });
    }
    
    try {
        await mcpManager.startServer(name, serverConfig);
        res.json({ message: `Server ${name} started` });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/servers/:name/stop', async (req, res) => {
    const { name } = req.params;
    
    try {
        await mcpManager.stopServer(name);
        res.json({ message: `Server ${name} stopped` });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/claude/config', (req, res) => {
    res.json({
        mcpServers: mcpManager.config
    });
});

// Initialize and start server
async function init() {
    try {
        await redis.connect();
        console.log('✅ Connected to Redis');
        
        // Start all MCP servers
        await mcpManager.startAllServers();
        
        server.listen(PORT, () => {
            console.log(`🌉 Claude Desktop Bridge running on port ${PORT}`);
            console.log(`🌐 WebSocket server ready`);
            console.log(`📊 Health check: http://localhost:${PORT}/health`);
        });
        
    } catch (error) {
        console.error('❌ Failed to initialize:', error);
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('Shutting down gracefully...');
    
    // Stop all MCP servers
    for (const serverName of mcpManager.servers.keys()) {
        await mcpManager.stopServer(serverName);
    }
    
    await redis.quit();
    process.exit(0);
});

// Start the application
init();
