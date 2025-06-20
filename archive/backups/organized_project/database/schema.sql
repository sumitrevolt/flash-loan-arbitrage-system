-- Flash Loan Arbitrage System Database Schema
-- PostgreSQL implementation for tracking trades, opportunities, and system metrics

-- Create database (run as superuser)
-- CREATE DATABASE flash_loan_arbitrage;

-- Use the database
-- \c flash_loan_arbitrage;

-- Create tables for the flash loan arbitrage system

-- 1. Tokens table - Track supported tokens
CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    contract_address VARCHAR(42) NOT NULL UNIQUE,
    decimals INTEGER NOT NULL DEFAULT 18,
    is_whitelisted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. DEXes table - Track supported DEX platforms
CREATE TABLE IF NOT EXISTS dexes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    router_address VARCHAR(42) NOT NULL UNIQUE,
    factory_address VARCHAR(42),
    dex_type VARCHAR(20) NOT NULL, -- 'uniswap_v2', 'uniswap_v3', 'sushiswap', etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Price feeds table - Store real-time price data
CREATE TABLE IF NOT EXISTS price_feeds (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    dex_id INTEGER REFERENCES dexes(id),
    pair_address VARCHAR(42),
    price_usd DECIMAL(20, 8) NOT NULL,
    liquidity_usd DECIMAL(20, 2),
    volume_24h DECIMAL(20, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_id, dex_id, timestamp)
);

-- 4. Arbitrage opportunities table - Track discovered opportunities
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    token_pair VARCHAR(20) NOT NULL, -- e.g., 'WETH/USDC'
    buy_dex_id INTEGER REFERENCES dexes(id),
    sell_dex_id INTEGER REFERENCES dexes(id),
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    price_difference DECIMAL(10, 6) NOT NULL, -- Percentage
    estimated_profit_usd DECIMAL(15, 2) NOT NULL,
    trade_amount DECIMAL(20, 8) NOT NULL,
    gas_estimate INTEGER,
    is_profitable BOOLEAN DEFAULT FALSE,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'discovered' -- 'discovered', 'executed', 'expired', 'failed'
);

-- 5. Trades table - Record all executed trades
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES arbitrage_opportunities(id),
    transaction_hash VARCHAR(66) UNIQUE,
    block_number BIGINT,
    token_pair VARCHAR(20) NOT NULL,
    buy_dex_id INTEGER REFERENCES dexes(id),
    sell_dex_id INTEGER REFERENCES dexes(id),
    trade_amount DECIMAL(20, 8) NOT NULL,
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    actual_profit_usd DECIMAL(15, 2),
    gas_used INTEGER,
    gas_price_gwei DECIMAL(10, 2),
    gas_cost_usd DECIMAL(10, 2),
    net_profit_usd DECIMAL(15, 2),
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. System metrics table - Track system performance
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(20, 8) NOT NULL,
    metric_unit VARCHAR(20),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(metric_name, recorded_at)
);

-- 7. Circuit breaker events table - Track circuit breaker activations
CREATE TABLE IF NOT EXISTS circuit_breaker_events (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    dex_id INTEGER REFERENCES dexes(id),
    event_type VARCHAR(20) NOT NULL, -- 'triggered', 'reset'
    reason TEXT,
    failed_count INTEGER,
    threshold_limit INTEGER,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Configuration table - Store system configuration
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. MCP server status table - Track MCP server health
CREATE TABLE IF NOT EXISTS mcp_server_status (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(100) NOT NULL,
    server_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'running', 'stopped', 'error'
    last_heartbeat TIMESTAMP,
    error_message TEXT,
    uptime_seconds INTEGER DEFAULT 0,
    requests_processed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. User wallets table - Track wallet information
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) NOT NULL UNIQUE,
    wallet_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    balance_matic DECIMAL(20, 8) DEFAULT 0,
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_price_feeds_timestamp ON price_feeds(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_price_feeds_token_dex ON price_feeds(token_id, dex_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON arbitrage_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_discovered ON arbitrage_opportunities(discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_executed ON trades(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_success ON trades(success);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON system_metrics(metric_name, recorded_at DESC);

-- Insert initial tokens (Polygon network)
INSERT INTO tokens (symbol, name, contract_address, decimals, is_whitelisted) VALUES
('WETH', 'Wrapped Ether', '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', 18, TRUE),
('WBTC', 'Wrapped Bitcoin', '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6', 8, TRUE),
('USDC', 'USD Coin', '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 6, TRUE),
('USDT', 'Tether USD', '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 6, TRUE),
('DAI', 'Dai Stablecoin', '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', 18, TRUE),
('WMATIC', 'Wrapped Matic', '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 18, TRUE),
('LINK', 'Chainlink', '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39', 18, TRUE),
('AAVE', 'Aave Token', '0xD6DF932A45C0f255f85145f286eA0b292B21C90B', 18, TRUE)
ON CONFLICT (symbol) DO NOTHING;

-- Insert initial DEXes (Polygon network)
INSERT INTO dexes (name, router_address, factory_address, dex_type, is_active) VALUES
('Uniswap V3', '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45', '0x1F98431c8aD98523631AE4a59f267346ea31F984', 'uniswap_v3', TRUE),
('QuickSwap', '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff', '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32', 'uniswap_v2', TRUE),
('SushiSwap', '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506', '0xc35DADB65012eC5796536bD9864eD8773aBc74C4', 'uniswap_v2', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insert initial system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('min_profit_threshold_usd', '5.0', 'Minimum profit threshold in USD for executing trades'),
('max_trade_amount_usd', '10000.0', 'Maximum trade amount in USD'),
('slippage_tolerance_percent', '3.0', 'Default slippage tolerance percentage'),
('circuit_breaker_threshold', '10', 'Number of failed trades before circuit breaker activates'),
('gas_price_limit_gwei', '100', 'Maximum gas price in Gwei for trade execution'),
('opportunity_expiry_seconds', '30', 'Time in seconds before an opportunity expires'),
('price_update_interval_seconds', '5', 'Interval for price feed updates'),
('health_check_interval_seconds', '60', 'Interval for system health checks')
ON CONFLICT (config_key) DO NOTHING;

-- Create views for easier data access

-- View for active opportunities
CREATE OR REPLACE VIEW active_opportunities AS
SELECT 
    ao.*,
    bd.name as buy_dex_name,
    sd.name as sell_dex_name,
    (ao.sell_price - ao.buy_price) / ao.buy_price * 100 as profit_percentage
FROM arbitrage_opportunities ao
JOIN dexes bd ON ao.buy_dex_id = bd.id
JOIN dexes sd ON ao.sell_dex_id = sd.id
WHERE ao.status = 'discovered' 
AND ao.expires_at > CURRENT_TIMESTAMP
AND ao.is_profitable = TRUE;

-- View for trade performance summary
CREATE OR REPLACE VIEW trade_performance_summary AS
SELECT 
    DATE(executed_at) as trade_date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_trades,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_trades,
    AVG(CASE WHEN success THEN net_profit_usd ELSE NULL END) as avg_profit_usd,
    SUM(CASE WHEN success THEN net_profit_usd ELSE 0 END) as total_profit_usd,
    AVG(gas_cost_usd) as avg_gas_cost_usd
FROM trades
GROUP BY DATE(executed_at)
ORDER BY trade_date DESC;

-- View for token performance
CREATE OR REPLACE VIEW token_performance AS
SELECT 
    t.symbol,
    COUNT(tr.*) as total_trades,
    SUM(CASE WHEN tr.success THEN 1 ELSE 0 END) as successful_trades,
    AVG(CASE WHEN tr.success THEN tr.net_profit_usd ELSE NULL END) as avg_profit_usd,
    SUM(CASE WHEN tr.success THEN tr.net_profit_usd ELSE 0 END) as total_profit_usd
FROM tokens t
LEFT JOIN trades tr ON tr.token_pair LIKE CONCAT(t.symbol, '%') OR tr.token_pair LIKE CONCAT('%', t.symbol)
WHERE t.is_whitelisted = TRUE
GROUP BY t.id, t.symbol
ORDER BY total_profit_usd DESC;

-- View for DEX performance comparison
CREATE OR REPLACE VIEW dex_performance AS
SELECT 
    d.name as dex_name,
    COUNT(tr.*) as total_trades,
    SUM(CASE WHEN tr.success THEN 1 ELSE 0 END) as successful_trades,
    AVG(CASE WHEN tr.success THEN tr.net_profit_usd ELSE NULL END) as avg_profit_usd,
    SUM(CASE WHEN tr.success THEN tr.net_profit_usd ELSE 0 END) as total_profit_usd
FROM dexes d
LEFT JOIN trades tr ON tr.buy_dex_id = d.id OR tr.sell_dex_id = d.id
WHERE d.is_active = TRUE
GROUP BY d.id, d.name
ORDER BY total_profit_usd DESC;

-- Create functions for common operations

-- Function to get latest price for a token on a DEX
CREATE OR REPLACE FUNCTION get_latest_price(token_symbol VARCHAR, dex_name VARCHAR)
RETURNS DECIMAL(20, 8) AS $$
DECLARE
    latest_price DECIMAL(20, 8);
BEGIN
    SELECT pf.price_usd INTO latest_price
    FROM price_feeds pf
    JOIN tokens t ON pf.token_id = t.id
    JOIN dexes d ON pf.dex_id = d.id
    WHERE t.symbol = token_symbol AND d.name = dex_name
    ORDER BY pf.timestamp DESC
    LIMIT 1;
    
    RETURN COALESCE(latest_price, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to record system metric
CREATE OR REPLACE FUNCTION record_metric(metric_name VARCHAR, metric_value DECIMAL, metric_unit VARCHAR DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    INSERT INTO system_metrics (metric_name, metric_value, metric_unit)
    VALUES (metric_name, metric_value, metric_unit);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers
CREATE TRIGGER update_tokens_timestamp
    BEFORE UPDATE ON tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_dexes_timestamp
    BEFORE UPDATE ON dexes
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_system_config_timestamp
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Grant permissions (adjust as needed for your user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO flash_loan_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO flash_loan_user;

-- Create maintenance procedures

-- Procedure to clean old price feeds (keep last 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_price_feeds()
RETURNS VOID AS $$
BEGIN
    DELETE FROM price_feeds 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Procedure to archive old trades (move to archive table)
CREATE OR REPLACE FUNCTION archive_old_trades()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Create archive table if it doesn't exist
    CREATE TABLE IF NOT EXISTS trades_archive (LIKE trades INCLUDING ALL);
    
    -- Move trades older than 90 days to archive
    WITH archived_trades AS (
        DELETE FROM trades 
        WHERE executed_at < CURRENT_TIMESTAMP - INTERVAL '90 days'
        RETURNING *
    )
    INSERT INTO trades_archive SELECT * FROM archived_trades;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Schema creation complete
-- Run this script with: psql -U username -d flash_loan_arbitrage -f schema.sql
