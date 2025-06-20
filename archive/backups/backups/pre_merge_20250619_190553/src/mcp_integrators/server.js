const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        services: {
            node: 'running',
            mcp_servers: 'starting'
        }
    });
});

// API endpoints
app.get('/api/status', (req, res) => {
    res.json({
        service: 'Flash Loan Arbitrage System',
        version: '1.0.0',
        uptime: process.uptime(),
        environment: process.env.NODE_ENV || 'development'
    });
});

// Start MCP servers
function startMCPServers() {
    
    const mcpServers = [
        'simple_mcp_server.py',
        'working_flash_loan_mcp.py',
        'minimal-mcp-server.py'
    ];
}

// Start the server
app.listen(PORT, () => {
    console.log(`Flash Loan Arbitrage System running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
    
    // Start MCP servers after a short delay
    setTimeout(startMCPServers, 2000);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('Received SIGINT, shutting down gracefully...');
    process.exit(0);
});
            console.log(`[${server}] Process exited with code ${code}`);
        });
    });
}

// Start the server
app.listen(PORT, () => {
    console.log(`Flash Loan Arbitrage System running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
    
    // Start MCP servers after a short delay
    setTimeout(startMCPServers, 2000);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('Received SIGINT, shutting down gracefully...');
    process.exit(0);
});
