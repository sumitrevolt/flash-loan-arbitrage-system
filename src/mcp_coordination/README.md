# MCP Unified Coordination System

A comprehensive management and orchestration system for Model Context Protocol (MCP) servers, specifically designed to coordinate LangChain and AutoGen integrations for flash loan arbitrage operations.

## 🚀 Overview

The MCP Unified Coordination System provides centralized management, monitoring, and orchestration for all MCP servers in your flash loan arbitrage infrastructure. It seamlessly integrates with existing LangChain and AutoGen systems while providing advanced features like health monitoring, automatic deployment, and real-time dashboards.

## ✨ Key Features

### 🔍 **Automatic Server Discovery**

- Scans project directories for MCP servers
- Supports Python, Node.js, and Docker-based servers
- Intelligent tier classification (Critical/Integration/Specialized)
- Automatic capability detection

### 🏥 **Health Monitoring & Alerting**

- Real-time health checks with circuit breakers
- Configurable monitoring intervals by server tier
- Pattern-based log analysis and alerting
- Performance metrics and SLA tracking

### 🚢 **Unified Deployment Management**

- Dependency-aware startup/shutdown sequences
- Process and container lifecycle management
- Auto-restart policies with backoff strategies
- Resource limit enforcement

### 📊 **Real-time Web Dashboard**

- Interactive server management interface
- Live metrics and performance graphs
- Log streaming and search capabilities
- System-wide status monitoring

### ⚙️ **Configuration Management**

- Centralized configuration with hot-reload
- Schema validation and error detection
- Environment variable integration
- Multi-format support (YAML/JSON/TOML)

### 📝 **Advanced Log Aggregation**

- Centralized log collection and indexing
- Pattern-based analysis and alerting
- Real-time streaming and search
- Automatic log rotation and compression

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Unified Coordinator                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Server    │  │   Health    │  │ Deployment  │  │Dashboard│ │
│  │  Registry   │  │  Monitor    │  │  Manager    │  │ Server  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │   Config    │  │     Log     │                              │
│  │  Manager    │  │ Aggregator  │                              │
│  └─────────────┘  └─────────────┘                              │
├─────────────────────────────────────────────────────────────────┤
│                     Integration Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                        ┌─────────────┐        │
│  │ LangChain   │                        │   AutoGen   │        │
│  │Integration  │                        │Integration  │        │
│  └─────────────┘                        └─────────────┘        │
├─────────────────────────────────────────────────────────────────┤
│                      MCP Server Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Critical Tier    │ Integration Tier    │ Specialized Tier     │
│  ┌─────────────┐  │ ┌─────────────┐    │ ┌─────────────┐      │
│  │ FileSystem  │  │ │ LangChain   │    │ │ Flash Loan  │      │
│  │ Context     │  │ │ AutoGen     │    │ │ Risk Mgmt   │      │
│  │ Memory      │  │ │ MCP Bridge  │    │ │ Arbitrage   │      │
│  └─────────────┘  │ └─────────────┘    │ └─────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Node.js 16+ (for Node.js servers)
- Docker (optional, for containerized servers)

### Quick Start

1. **Clone and navigate to the project:**

   ```bash
   cd flash-loan-system/src/mcp_coordination
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the system:**

   ```bash
   python main.py
   ```

4. **Access the dashboard:**

   Open <http://localhost:8080> in your browser

### Advanced Installation

1. **Install with all optional dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install redis docker numpy pandas  # Optional components
   ```

2. **Create configuration:**

   ```bash
   # The system will auto-create default configurations
   python main.py --check-config
   ```

3. **Run with custom configuration:**

   ```bash
   python main.py --config config/production.yaml
   ```

## 📖 Usage

### Starting the System

```bash
# Basic startup
python main.py

# With custom configuration
python main.py --config config/custom.yaml

# With debug logging
python main.py --log-level DEBUG

# As background daemon
python main.py --daemonize

# Dry run (initialize but don't start)
python main.py --dry-run
```

### Configuration Validation

```bash
# Validate all configurations
python main.py --check-config

# Validate specific configuration
python main.py --config myconfig.yaml --check-config
```

### System Management

```bash
# Check if system is running
ps aux | grep mcp_coordination

# Stop the system (if running as daemon)
kill $(cat mcp_coordination.pid)

# View logs
tail -f logs/mcp_coordination.log
```

## 📊 Dashboard Features

### Server Management

- **Server List**: View all discovered MCP servers
- **Status Monitoring**: Real-time health and deployment status
- **Control Actions**: Start, stop, restart individual servers
- **Bulk Operations**: Deploy or shutdown all servers

### Health Monitoring

- **System Overview**: Health percentage and key metrics
- **Alert Dashboard**: Active alerts and resolution status
- **Performance Graphs**: Response times and success rates
- **Circuit Breaker Status**: Server resilience monitoring

### Log Analysis

- **Real-time Logs**: Live log streaming from all components
- **Search & Filter**: Advanced log search with filters
- **Pattern Analysis**: Automatic detection of issues
- **Export Options**: Download logs in various formats

### Configuration Management

- **Live Config View**: Current configuration status
- **Validation Results**: Schema validation and errors
- **Hot Reload**: Apply configuration changes without restart

## ⚙️ Configuration

### Main Configuration (`config/mcp_coordination.yaml`)

```yaml
coordination:
  system_name: "MCP Flash Loan Arbitrage System"
  version: "1.0.0"
  environment: "production"

discovery:
  auto_discover: true
  scan_interval: 300
  discovery_paths:
    - "mcp_servers/"
    - "src/langchain_integration/"
    - "src/autogen_integration/"

health_monitoring:
  enabled: true
  timeout: 10
  intervals:
    critical: 10    # seconds
    integration: 30
    specialized: 60
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout: 60

deployment:
  mode: "production"
  auto_start: true
  restart_policy: "on-failure"
  max_restarts: 3

dashboard:
  enabled: true
  host: "0.0.0.0"
  port: 8080
  debug: false

logging:
  level: "INFO"
  log_dir: "logs"
  max_log_size: 104857600  # 100MB
  backup_count: 10
  compress_logs: true
```

### Server Classification

Servers are automatically classified into tiers:

- **Critical Tier**: Core infrastructure (filesystem, context, memory)
- **Integration Tier**: LangChain/AutoGen bridges and orchestrators
- **Specialized Tier**: Flash loan, arbitrage, and risk management servers

## 🔧 Development

### Project Structure

```text
src/mcp_coordination/
├── __init__.py                 # Package initialization
├── main.py                     # Main entry point
├── unified_coordinator.py      # Central coordinator
├── mcp_server_registry.py     # Server discovery and registry
├── health_monitor.py          # Health monitoring system
├── deployment_manager.py      # Deployment orchestration
├── dashboard_server.py        # Web dashboard
├── config_manager.py          # Configuration management
├── log_aggregator.py          # Log collection and analysis
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Adding Custom Components

1. **Custom Health Checks:**

   ```python
   from health_monitor import HealthMonitor, HealthCheckType
   
   # Register custom health check
   monitor.register_custom_check("my_check", my_check_function)
   ```

2. **Custom Log Patterns:**

   ```python
   from log_aggregator import LogPattern, LogLevel
   
   # Add custom pattern
   pattern = LogPattern(
       name="custom_error",
       pattern=r"CUSTOM_ERROR.*",
       severity=LogLevel.ERROR,
       description="Custom error detected"
   )
   aggregator.add_pattern(pattern)
   ```

3. **Configuration Schemas:**

   ```python
   from config_manager import ConfigSchema
   
   # Define custom schema
   schema = ConfigSchema(
       name="my_component",
       required_fields=["setting1", "setting2"],
       field_types={"setting1": str, "setting2": int}
   )
   config_manager.register_schema(schema)
   ```

### Integration Examples

#### LangChain Integration

```python
from src.mcp_coordination.unified_coordinator import UnifiedCoordinator

# Initialize coordinator
coordinator = UnifiedCoordinator()
await coordinator.initialize()

# Access LangChain integration
langchain_integration = coordinator.langchain_integration
if langchain_integration:
    # Use LangChain with coordinated MCP servers
    result = await langchain_integration.execute_workflow("arbitrage_analysis")
```

#### AutoGen Integration

```python
# Access AutoGen integration
autogen_integration = coordinator.autogen_integration
if autogen_integration:
    # Start multi-agent conversation with MCP server access
    result = await autogen_integration.start_conversation(
        "risk_assessment",
        context={"opportunity": arbitrage_data}
    )
```

## 🚨 Monitoring & Alerts

### Health Check Types

- **HTTP Endpoint**: Standard REST API health checks
- **WebSocket Ping**: WebSocket connection verification
- **TCP Connect**: Basic connectivity testing
- **Process Check**: Process existence verification

### Alert Conditions

- Server down or unreachable
- High response times (>5 seconds)
- Low success rate (<80%)
- Circuit breaker activation
- Memory or disk space warnings
- Configuration errors

### Alert Actions

- Log alert generation
- Dashboard notifications
- Automatic restart attempts
- Circuit breaker activation
- External webhook notifications (configurable)

## 📈 Performance Optimization

### Recommended Settings

**Production Environment:**

```yaml
health_monitoring:
  intervals:
    critical: 10
    integration: 30  
    specialized: 60
  circuit_breaker:
    failure_threshold: 3
    recovery_timeout: 30

deployment:
  restart_policy: "always"
  max_restarts: 5
  startup_timeout: 60

logging:
  level: "WARNING"
  compress_logs: true
```

**Development Environment:**

```yaml
health_monitoring:
  intervals:
    critical: 30
    integration: 60
    specialized: 120
  
deployment:
  restart_policy: "on-failure"
  auto_start: false

logging:
  level: "DEBUG"
  compress_logs: false

dashboard:
  debug: true
```

## 🔒 Security Considerations

- **Network Security**: Configure firewall rules for dashboard port
- **Authentication**: Implement dashboard authentication in production
- **Log Security**: Sanitize sensitive information in logs
- **Process Security**: Run with minimal required privileges
- **Configuration Security**: Protect configuration files with appropriate permissions

## 🐛 Troubleshooting

### Common Issues

**System Won't Start:**

```bash
# Check configuration
python main.py --check-config

# Check permissions
ls -la config/ logs/

# Check for running instances
ps aux | grep mcp_coordination
```

**Servers Not Discovered:**

```bash
# Check discovery paths in config
# Verify server files exist
# Check server file patterns (*.py, *.js, package.json)
```

**Health Checks Failing:**

```bash
# Check server URLs and ports
# Verify network connectivity
# Review health check logs
tail -f logs/mcp_coordination.log | grep HEALTH
```

**Dashboard Not Accessible:**

```bash
# Check dashboard configuration
# Verify port availability
netstat -tulpn | grep 8080

# Check firewall rules
sudo ufw status
```

### Debug Mode

```bash
# Enable debug logging
python main.py --log-level DEBUG

# Check specific component logs
tail -f logs/health_monitor.log
tail -f logs/deployment_manager.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black isort flake8

# Run tests
pytest tests/

# Format code
black src/mcp_coordination/
isort src/mcp_coordination/

# Lint code
flake8 src/mcp_coordination/
```

## 📄 License

This project is part of the Flash Loan LangChain AutoGen MCP Integration system.

## 🆘 Support

For support, please check:

1. This README file
2. System logs in `logs/` directory
3. Dashboard error messages
4. Configuration validation output

---

### Built with ❤️ for the MCP ecosystem