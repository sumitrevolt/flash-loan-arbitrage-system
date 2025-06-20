# 🚀 Multi-MCP Server Container System - Usage Guide

## System Overview

Your enhanced Multi-MCP Server Container system is now configured with GitHub Pro integration, following the comprehensive plan from `MULTI_MCP_SERVER_CONTAINER_PLAN.md`.

## 🏗️ Architecture Deployed

### Core Components
- **GitHub Pro Enhanced Orchestrator** (Port 8080)
- **MCP Servers with Copilot Integration** (Ports 8000-8030)
- **AI Agents with GitHub Integration** (Port 8001)
- **High-Performance Redis Cluster** (Port 6379)
- **PostgreSQL with Performance Tuning** (Port 5432)
- **InfluxDB for Time Series Data** (Port 8086)
- **Enhanced Prometheus with GitHub Metrics** (Port 9090)
- **Grafana with GitHub Dashboards** (Port 3000)
- **GitHub Metrics Collector** (Port 8090)

## 🚀 Quick Start

### 1. Deploy the System
```powershell
# On Windows
.\setup_multi_mcp_containers.ps1

# On Linux/Mac
python setup_multi_mcp_containers.py
```

### 2. Verify Deployment
Check that all services are running:
```bash
docker-compose -f docker-compose.github-enhanced.yml ps
```

### 3. Access Service Endpoints
- **Main Dashboard**: http://localhost:3000 (Grafana)
- **Orchestrator**: http://localhost:8080
- **MCP Servers**: http://localhost:8000
- **Prometheus**: http://localhost:9090

## 🔧 Configuration

### Environment Variables (.env file)
Update these critical variables:

```env
# GitHub Integration
GITHUB_TOKEN=ghp_your_github_token
COPILOT_API_KEY=your_copilot_api_key

# Database Passwords
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password
GRAFANA_PASSWORD=your_secure_password

# API Keys
OPENAI_API_KEY=sk-your_openai_key
```

### GitHub Repository Settings
1. **Enable GitHub Actions** in your repository
2. **Set up repository secrets**:
   - `GITHUB_TOKEN`
   - `COPILOT_API_KEY`
   - `OPENAI_API_KEY`
3. **Configure branch protection rules**
4. **Enable CodeQL security scanning**

## 📊 Monitoring & Dashboards

### Grafana Dashboards
Access at http://localhost:3000

**Default Login**: admin / [your_grafana_password]

### Key Metrics to Monitor
- **Flash Loan Execution Time**: < 500ms target
- **Arbitrage Opportunity Detection**: < 100ms latency
- **System Uptime**: 99.9% target
- **Error Rate**: < 0.1% target

### Prometheus Metrics
Access at http://localhost:9090

**Key Endpoints**:
- `/metrics` - System metrics
- `/api/v1/query` - Query interface
- `/graph` - Query browser

## 🤖 AI Features

### GitHub Copilot Integration
- **Automatic Code Reviews**: Pull requests get AI-powered reviews
- **Code Optimization**: Real-time suggestions for performance improvements
- **Bug Detection**: Automated syntax and logic error detection
- **Test Generation**: AI-generated unit tests

### Auto-Fix Capabilities
- **Syntax Errors**: Automatically fixed by Copilot
- **Code Style**: Auto-formatting with Black/Prettier
- **Import Organization**: Automatic import sorting
- **Security Issues**: Vulnerability detection and suggestions

## 🔄 GitHub Actions Workflows

### Deployed Workflows

1. **Flash Loan MCP CI/CD** (`.github/workflows/flash-loan-mcp.yml`)
   - Triggers on MCP flash loan server changes
   - Runs tests, security scans, and deployments

2. **Price Feed MCP CI/CD** (`.github/workflows/price-feed-mcp.yml`)
   - Monitors price feed accuracy
   - Runs every 4 hours for data validation

3. **Risk Manager MCP CI/CD** (`.github/workflows/risk-manager-mcp.yml`)
   - Enhanced security scanning with CodeQL
   - Risk model validation

### Workflow Triggers
- **Push to main**: Full deployment pipeline
- **Pull Requests**: Code review and testing
- **Scheduled**: Regular health checks and updates

## 🛠️ MCP Servers Available

### Core Trading Servers
- **Flash Loan Server** (Port 8000): Primary flash loan execution
- **Price Feed Server** (Port 8001): Real-time price aggregation
- **Arbitrage Server** (Port 8002): Opportunity detection
- **Risk Manager Server** (Port 8003): Risk assessment

### GitHub Integration Servers
- **GitHub Copilot Server** (Port 8010): AI code assistance
- **GitHub Actions Server** (Port 8011): CI/CD automation
- **Code Quality Server** (Port 8012): Automated code review

### Infrastructure Servers
- **Monitoring Server** (Port 8020): System health monitoring
- **Cache Manager Server** (Port 8021): Redis management
- **Database Server** (Port 8022): PostgreSQL operations

## 🔍 Testing & Performance

### Run Performance Benchmarks
```bash
cd benchmarks
python flash_loan_performance.py
```

### Run Integration Tests
```bash
cd tests
pytest integration/ -v --asyncio-mode=auto
```

### Health Checks
```bash
# Check all services
curl http://localhost:8080/health
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## 📈 Performance Targets

### Latency Requirements
- **Flash Loan Execution**: < 500ms
- **Price Feed Updates**: < 100ms
- **Arbitrage Detection**: < 200ms
- **Risk Assessment**: < 300ms

### Availability Targets
- **System Uptime**: 99.9%
- **Success Rate**: > 99%
- **Error Recovery**: < 30 seconds

## 🚨 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check logs
docker-compose -f docker-compose.github-enhanced.yml logs [service_name]

# Restart specific service
docker-compose -f docker-compose.github-enhanced.yml restart [service_name]
```

#### GitHub Integration Issues
1. Verify GitHub token has correct permissions
2. Check repository secrets are set
3. Ensure workflows are enabled

#### Performance Issues
1. Check Grafana dashboards for bottlenecks
2. Monitor resource usage in Docker stats
3. Review MCP server logs for errors

### Log Locations
- **Container Logs**: `docker-compose logs`
- **Application Logs**: `./logs/` directory
- **System Metrics**: Prometheus at port 9090

## 🔧 Maintenance

### Daily Tasks
- Monitor Grafana dashboards
- Check GitHub Actions status
- Review error logs

### Weekly Tasks
- Update dependencies via Dependabot
- Review security scan results
- Optimize performance based on metrics

### Monthly Tasks
- Update system configuration
- Review and update documentation
- Capacity planning based on usage

## 📚 Additional Resources

### Documentation
- `MULTI_MCP_SERVER_CONTAINER_PLAN.md` - Complete architecture plan
- `setup_report.json` - Detailed setup results
- `.github/workflows/` - CI/CD pipeline definitions

### Support
- Check GitHub Issues for common problems
- Review container logs for debugging
- Monitor Grafana dashboards for system health

## 🎯 Next Steps

1. **Configure GitHub Repository**:
   - Set up branch protection
   - Add repository secrets
   - Enable security features

2. **Customize Monitoring**:
   - Create custom Grafana dashboards
   - Set up alerting rules
   - Configure notification channels

3. **Optimize Performance**:
   - Review benchmark results
   - Tune database settings
   - Optimize container resources

4. **Scale the System**:
   - Add more MCP servers as needed
   - Implement load balancing
   - Set up multi-region deployment

---

**System Status**: ✅ Operational  
**Last Updated**: $(date)  
**Version**: 1.0.0 - GitHub Pro Enhanced
