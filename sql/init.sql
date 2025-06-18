-- MCP Coordination Database Initialization
-- PostgreSQL database schema for 10 MCP agent coordination

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Agent registry table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    agent_id INTEGER NOT NULL,
    container_name VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    url VARCHAR(255) NOT NULL,
    mcp_server_path TEXT NOT NULL,
    capabilities JSONB NOT NULL DEFAULT '[]',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'unknown',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    tasks_assigned INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task management table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    assigned_agent_id UUID REFERENCES agents(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    requirements JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Agent performance metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- System events log
CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Arbitrage opportunities
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_symbol VARCHAR(20) NOT NULL,
    token_address VARCHAR(42) NOT NULL,
    buy_dex VARCHAR(50) NOT NULL,
    sell_dex VARCHAR(50) NOT NULL,
    buy_price NUMERIC(20, 8) NOT NULL,
    sell_price NUMERIC(20, 8) NOT NULL,
    profit_usd NUMERIC(15, 2) NOT NULL,
    profit_percentage NUMERIC(8, 4) NOT NULL,
    gas_cost_usd NUMERIC(10, 2) NOT NULL,
    net_profit_usd NUMERIC(15, 2) NOT NULL,
    liquidity_available NUMERIC(15, 2) NOT NULL,
    max_trade_size NUMERIC(15, 2) NOT NULL,
    confidence_score NUMERIC(3, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    github_tracked BOOLEAN DEFAULT FALSE,
    documentation_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending'
);

-- MCP server configurations
CREATE TABLE IF NOT EXISTS mcp_servers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    server_name VARCHAR(255) NOT NULL,
    description TEXT,
    tools JSONB NOT NULL DEFAULT '[]',
    enabled BOOLEAN DEFAULT TRUE,
    priority VARCHAR(20) DEFAULT 'medium',
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_priority ON agents(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent ON agent_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_timestamp ON agent_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_arbitrage_status ON arbitrage_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_arbitrage_timestamp ON arbitrage_opportunities(created_at);
CREATE INDEX IF NOT EXISTS idx_mcp_servers_enabled ON mcp_servers(enabled);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mcp_servers_updated_at BEFORE UPDATE ON mcp_servers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial system event
INSERT INTO system_events (event_type, source, message, severity) 
VALUES ('system_init', 'database', 'MCP coordination database initialized', 'info');

-- Create views for monitoring
CREATE OR REPLACE VIEW agent_status_summary AS
SELECT 
    agent_type,
    COUNT(*) as total_agents,
    COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy_agents,
    COUNT(CASE WHEN status = 'unhealthy' THEN 1 END) as unhealthy_agents,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_agents,
    AVG(tasks_assigned) as avg_tasks_assigned,
    AVG(tasks_completed) as avg_tasks_completed,
    AVG(error_count) as avg_error_count
FROM agents
GROUP BY agent_type;

CREATE OR REPLACE VIEW task_status_summary AS
SELECT 
    task_type,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
    COUNT(CASE WHEN status = 'assigned' THEN 1 END) as assigned_tasks,
    COUNT(CASE WHEN status = 'running' THEN 1 END) as running_tasks,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_execution_time_seconds
FROM tasks
GROUP BY task_type;

CREATE OR REPLACE VIEW system_performance AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total_events,
    COUNT(CASE WHEN severity = 'error' THEN 1 END) as error_events,
    COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_events,
    COUNT(CASE WHEN severity = 'info' THEN 1 END) as info_events
FROM system_events
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mcp_user;

COMMIT;
