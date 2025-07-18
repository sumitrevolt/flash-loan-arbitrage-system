# AutoGen Multi-Agent Flash Loan System

## Overview

This is a comprehensive AutoGen-based multi-agent system designed for flash loan arbitrage coordination. The system leverages Microsoft's AutoGen framework to orchestrate multiple AI agents that collaborate to analyze market opportunities, assess risks, and execute profitable arbitrage strategies.

## Architecture

### Core Components

1. **AutoGen Coordinator** (`src/autogen_agents/autogen_coordinator.py`)
   - Main coordination service with enhanced functionality
   - Real AutoGen group chat implementation
   - Comprehensive monitoring and metrics
   - REST API endpoints for external integration

2. **Multi-Agent System**
   - **ArbitrageCoordinator**: Master coordinator for strategic decisions
   - **MarketAnalyzer**: DeFi market data analysis and opportunity identification
   - **TransactionExecutor**: Flash loan transaction execution
   - **RiskManager**: Risk assessment and management
   - **UserProxy**: Automated user proxy for conversation management

3. **Infrastructure Integration**
   - Redis for caching and state management
   - PostgreSQL for persistent data storage
   - FastAPI for REST API endpoints
   - Docker containerization with health checks

## Features

### Real AutoGen Functionality
- ✅ Actual AutoGen group chat conversations
- ✅ Multi-agent coordination with structured decision making
- ✅ Conversation history tracking and analysis
- ✅ Automated decision extraction from agent discussions

### Monitoring & Observability
- ✅ Comprehensive performance metrics
- ✅ Task tracking and history
- ✅ Health check endpoints
- ✅ Detailed logging and error handling
- ✅ Redis-based caching for task results

### Integration Capabilities
- ✅ LangChain system integration
- ✅ MCP server connectivity
- ✅ Web3 and blockchain integration ready
- ✅ RESTful API for external coordination

## API Endpoints

### Core Endpoints
- `GET /health` - Basic health check
- `GET /status` - Detailed service status
- `POST /coordinate` - Coordinate multi-agent task
- `GET /agents` - List available agents
- `GET /metrics` - Performance metrics

### Advanced Endpoints
- `GET /tasks/{task_id}` - Get specific task status
- `GET /tasks` - List recent tasks
- `POST /agents/reset` - Reset and reinitialize agents
- `POST /system/health-check` - Comprehensive health check
- `GET /system/info` - Detailed system information

### Service-Level Endpoints
- `GET /service/info` - Service information
- `GET /service/health-detailed` - Detailed health status
- `POST /service/coordination-test` - Test coordination system
- `GET /service/logs` - Recent service logs

## Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API key for LLM access
- `REDIS_URL` - Redis connection URL (default: redis://redis:6379)

### Optional
- `POSTGRES_URL` - PostgreSQL connection URL
- `OLLAMA_HOST` - Ollama server URL (default: http://ollama:11434/v1)
- `SERVICE_PORT` - Service port (default: 8000)
- `HOST` - Bind host (default: 0.0.0.0)
- `MAX_ROUND` - Maximum conversation rounds (default: 10)
- `AUTOGEN_LOG_LEVEL` - Logging level (default: INFO)
- `AUTOGEN_WORK_DIR` - Working directory (default: /app/autogen_work)

## Docker Deployment

### Build Image
```bash
docker build -t autogen-coordinator:latest .
```

### Run Container
```bash
docker run -d \
  --name autogen-coordinator \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key \
  -e REDIS_URL=redis://redis:6379 \
  -v ./logs:/app/logs \
  autogen-coordinator:latest
```

### Docker Compose Integration
```yaml
autogen-coordinator:
  build: ./deployment/docker/autogen
  container_name: autogen-coordinator
  ports:
    - "8000:8000"
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_URL=redis://redis:6379
    - POSTGRES_URL=postgresql://postgres:password@postgres:5432/flash_loan
  volumes:
    - ./logs:/app/logs
    - ./data:/app/data
  depends_on:
    - redis
    - postgres
  networks:
    - flash-loan-network
  restart: unless-stopped
```

## Usage Examples

### Basic Task Coordination
```python
import asyncio
import aiohttp

async def coordinate_task():
    task = {
        "id": "arbitrage_001",
        "description": "Analyze USDC/USDT arbitrage opportunity between Uniswap and SushiSwap",
        "priority": "high"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/coordinate",
            json=task
        ) as response:
            result = await response.json()
            print(f"Coordination result: {result}")

# Run the task
asyncio.run(coordinate_task())
```

### Monitor System Health
```python
import aiohttp
import asyncio

async def check_health():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/system/health-check"
        ) as response:
            health = await response.json()
            print(f"System health: {health}")

asyncio.run(check_health())
```

## Development

### Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Run: `python main.py`

### Testing
```bash
# Test coordination
curl -X POST http://localhost:8000/service/coordination-test

# Check health
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/metrics
```

## Security Features

- Non-root user execution in container
- Secure dependency management
- Input validation and sanitization
- Error handling without information leakage
- Comprehensive logging for audit trails

## Performance Optimizations

- Docker layer caching for faster builds
- Redis caching for task results
- Async/await patterns throughout
- Connection pooling for database access
- Health check optimizations

## Integration with Other Systems

### LangChain Integration
The AutoGen system seamlessly integrates with the LangChain coordination system for hybrid multi-agent workflows.

### MCP Server Integration
Built-in support for Model Context Protocol (MCP) servers for enhanced context and tool access.

### Blockchain Integration
Ready for Web3 integration with support for:
- Flash loan execution
- DEX price monitoring
- Transaction analysis
- Risk assessment

## Troubleshooting

### Common Issues

1. **AutoGen Import Errors**
   - Ensure `ag2` is installed: `pip install ag2==0.2.25`
   - Check Python version compatibility (3.11+ recommended)

2. **Redis Connection Issues**
   - Verify Redis is running and accessible
   - Check `REDIS_URL` environment variable
   - Test connectivity: `redis-cli ping`

3. **Agent Initialization Failures**
   - Verify OpenAI API key is valid
   - Check network connectivity to LLM providers
   - Review logs in `/app/logs/autogen_main.log`

### Debug Mode
Set `DEBUG=true` environment variable for verbose logging.

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure Docker builds successfully
5. Test integration with existing systems

## License

This project is part of the Flash Loan Arbitrage System. See the main project license for details.