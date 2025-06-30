# AutoGen & LangChain Deployment Guide

## 🚀 Quick Start

This guide will help you deploy the complete AutoGen and LangChain multi-agent system for flash loan arbitrage.

## 📋 Prerequisites

### Required Software
- **Docker Desktop**: Latest version with Docker Compose
- **Git**: For cloning the repository
- **PowerShell** (Windows) or **Bash** (Linux/macOS)

### System Requirements
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Minimum 4 cores, Recommended 8 cores+
- **Storage**: Minimum 20GB free space
- **Network**: Internet connection for downloading images

### API Keys (Optional but Recommended)
- **OpenAI API Key**: For GPT-4 models
- **Anthropic API Key**: For Claude models
- **Google API Key**: For Gemini models
- **GitHub Token**: For GitHub integration

## 🔧 Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd flash-loan
```

### 2. Configure Environment
Edit the environment file:
```bash
# Windows
notepad deployment/docker/.env

# Linux/macOS
nano deployment/docker/.env
```

**Required Configuration:**
```env
# Add your API keys here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Database passwords (change these for production)
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_redis_password_here
RABBITMQ_PASSWORD=your_rabbitmq_password_here
```

### 3. Deploy the System

#### Windows (PowerShell)
```powershell
cd deployment/docker
.\deploy-autogen-langchain.ps1 deploy
```

#### Linux/macOS (Bash)
```bash
cd deployment/docker
./deploy-autogen-langchain.sh deploy
```

## 📊 Service Architecture

### Core Services
- **LangChain Coordinator** (Port 8000): Multi-agent coordination system
- **AutoGen Coordinator** (Port 8010): AutoGen-based agent conversations
- **PostgreSQL** (Port 5432): Primary database
- **Redis** (Port 6379): Caching and session storage
- **RabbitMQ** (Port 5672): Message queue system

### MCP Servers
- **Supermemory MCP** (Port 8100): Memory and knowledge management
- **Context7 MCP** (Port 8101): Documentation and context retrieval
- **Filesystem MCP** (Port 8102): File system operations
- **Task Manager MCP** (Port 8103): Task coordination and management

### Monitoring & Analytics
- **Grafana** (Port 3000): Metrics dashboard
- **Prometheus** (Port 9090): Metrics collection
- **Kibana** (Port 5601): Log analytics
- **Elasticsearch** (Port 9200): Log storage
- **Web Dashboard** (Port 8090): Unified interface

## 🔍 Verification & Testing

### 1. Check Service Status
```bash
# Windows
.\deploy-autogen-langchain.ps1 status

# Linux/macOS
./deploy-autogen-langchain.sh status
```

### 2. Run Health Tests
```bash
# Windows
.\deploy-autogen-langchain.ps1 test

# Linux/macOS
./deploy-autogen-langchain.sh test
```

### 3. Access Web Interfaces

#### Primary Endpoints
- **LangChain API**: http://localhost:8000
- **AutoGen API**: http://localhost:8010
- **Web Dashboard**: http://localhost:8090
- **Grafana Monitoring**: http://localhost:3000

#### Health Check Endpoints
- **LangChain Health**: http://localhost:8000/health
- **AutoGen Health**: http://localhost:8010/health
- **Service Info**: http://localhost:8010/service/info

### 4. Test Agent Communication

#### LangChain Test
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Test agent coordination",
    "task_type": "coordination_test",
    "context": {"test": true}
  }'
```

#### AutoGen Test
```bash
curl -X POST http://localhost:8010/service/coordination-test \
  -H "Content-Type: application/json"
```

## 🛠️ Management Commands

### Start/Stop Services
```bash
# Start all services
.\deploy-autogen-langchain.ps1 deploy    # Windows
./deploy-autogen-langchain.sh deploy     # Linux/macOS

# Stop all services
.\deploy-autogen-langchain.ps1 stop      # Windows
./deploy-autogen-langchain.sh stop       # Linux/macOS

# Restart services
.\deploy-autogen-langchain.ps1 restart   # Windows
./deploy-autogen-langchain.sh restart    # Linux/macOS
```

### View Logs
```bash
# View all service logs
.\deploy-autogen-langchain.ps1 logs      # Windows
./deploy-autogen-langchain.sh logs       # Linux/macOS

# View specific service logs
docker-compose -f docker-compose.unified.yml logs langchain-coordinator
docker-compose -f docker-compose.unified.yml logs autogen-coordinator
```

### Cleanup (Caution: Removes all data)
```bash
.\deploy-autogen-langchain.ps1 cleanup   # Windows
./deploy-autogen-langchain.sh cleanup    # Linux/macOS
```

## 🔧 Configuration Options

### Environment Variables

#### Core Configuration
```env
# Database Configuration
POSTGRES_DB=flash_loan_db
POSTGRES_USER=flash_loan_user
POSTGRES_PASSWORD=your_password

# Redis Configuration  
REDIS_PASSWORD=your_redis_password

# Log Level
LOG_LEVEL=INFO  # DEBUG, INFO, WARN, ERROR

# Performance Tuning
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
WORKER_PROCESSES=2
```

#### LangChain Configuration
```env
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
VECTOR_STORE_PROVIDER=chroma
EMBEDDING_MODEL=text-embedding-ada-002
```

#### AutoGen Configuration
```env
AUTOGEN_MAX_AGENTS=10
AUTOGEN_CONVERSATION_TIMEOUT=600
AUTOGEN_WORK_DIR=/app/autogen_work
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Conflicts
If ports are already in use, you can modify them in the docker-compose file:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

#### 2. Memory Issues
For systems with limited RAM, reduce service resources:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
```

#### 3. API Key Issues
Ensure API keys are properly set in the `.env` file:
```bash
# Check if environment variables are loaded
docker-compose config
```

#### 4. Database Connection Issues
Check PostgreSQL logs:
```bash
docker-compose logs postgres
```

#### 5. Service Not Starting
Check individual service logs:
```bash
docker-compose logs langchain-coordinator
docker-compose logs autogen-coordinator
```

### Log Locations
- **Deployment Logs**: `deployment/docker/logs/deployment.log`
- **Service Logs**: Use `docker-compose logs <service-name>`
- **Application Logs**: Available via log aggregation in Kibana

### Performance Optimization

#### For Development
```env
LOG_LEVEL=DEBUG
ENABLE_METRICS=false
WORKER_PROCESSES=1
```

#### For Production
```env
LOG_LEVEL=INFO
ENABLE_METRICS=true
WORKER_PROCESSES=4
MAX_CONCURRENT_TASKS=10
```

## 📈 Monitoring & Maintenance

### Grafana Dashboards
Access monitoring at http://localhost:3000
- Default credentials: admin/admin
- Pre-configured dashboards for all services

### Health Monitoring
- Automated health checks every 30 seconds
- Alerts via webhook (configure `ALERT_WEBHOOK_URL`)
- Service recovery and restart capabilities

### Log Analysis
Access log analysis at http://localhost:5601
- Real-time log aggregation
- Search and filter capabilities
- Error tracking and alerting

## 🔒 Security Considerations

### Production Deployment
1. **Change default passwords** in `.env` file
2. **Use environment-specific API keys**
3. **Enable TLS/SSL** for external access
4. **Configure firewall rules** for port access
5. **Regular security updates** for containers

### Network Security
- Services communicate via internal Docker network
- Only necessary ports exposed to host
- MCP servers isolated with proper access controls

## 🚀 Next Steps

1. **Configure API Keys**: Add your OpenAI, Anthropic, and other API keys
2. **Customize Agents**: Modify agent configurations in respective directories
3. **Set Up Monitoring**: Configure Grafana dashboards and alerts
4. **Production Hardening**: Follow security best practices
5. **Scale Services**: Adjust resource limits based on usage

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs for error details
3. Consult the individual service documentation
4. Open an issue in the project repository

---

**Happy Deploying! 🎉**