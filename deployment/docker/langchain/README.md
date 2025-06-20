# LangChain Multi-Agent Flash Loan System

## Overview

This is a comprehensive multi-agent system built with LangChain for flash loan arbitrage opportunities. The system provides:

- **Multi-Agent Coordination**: Specialized agents working together through LangGraph
- **RAG (Retrieval-Augmented Generation)**: Knowledge base integration for informed decisions
- **Tool Integration**: Advanced tools for calculations, analysis, and code execution
- **Code Interpretation**: Safe Python code execution for analysis and calculations
- **Memory Management**: Persistent agent memory and conversation history
- **Real-time Monitoring**: Health checks, metrics, and performance tracking

## Architecture

### Core Components

1. **Agent Coordinator**: Central orchestration of agent interactions
2. **Arbitrage Agent**: Identifies and analyzes arbitrage opportunities
3. **Risk Agent**: Assesses risks and validates safety parameters
4. **Execution Agent**: Handles transaction execution and gas optimization
5. **Monitoring Agent**: Tracks system health and performance
6. **RAG Agent**: Provides information retrieval and context
7. **Code Interpreter Agent**: Executes calculations and analysis code

### Services

- **Vector Store Service**: Manages embeddings and similarity search
- **Memory Manager**: Handles agent memory and conversation history
- **Tool Registry**: Organizes and manages available tools
- **Configuration Management**: Centralized configuration handling

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (recommended)
- At least 8GB RAM available for containers

### Environment Setup

1. **Create environment file**:
```bash
cp .env.example .env
```

2. **Set API keys in `.env`**:
```bash
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional
GOOGLE_API_KEY=your_google_api_key_here        # Optional
```

### Launch the System

1. **Start the complete system**:
```bash
cd deployment/docker
docker-compose -f docker-compose.langchain-enhanced.yml up -d
```

2. **Check system status**:
```bash
# Check all services
docker-compose -f docker-compose.langchain-enhanced.yml ps

# Check main coordinator logs
docker logs flash-loan-langchain-coordinator

# Check health
curl http://localhost:8000/health
```

### Verify Installation

1. **Health Check**:
```bash
curl http://localhost:8000/health
```

2. **List Available Agents**:
```bash
curl http://localhost:8000/agents
```

3. **Test RAG Service**:
```bash
curl http://localhost:8003/health
```

## Usage Examples

### 1. Basic Agent Interaction

```bash
# Send a request to the multi-agent system
curl -X POST http://localhost:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "arbitrage",
    "message": "Analyze ETH/USDC arbitrage opportunity between Uniswap and SushiSwap",
    "context": {
      "market_data": {
        "prices": {
          "uniswap": 2500.50,
          "sushiswap": 2505.25
        },
        "amount": 1000,
        "gas_cost": 50
      }
    }
  }'
```

### 2. Direct Agent Communication

```bash
# Send request directly to arbitrage agent
curl -X POST http://localhost:8000/agent/arbitrage/direct \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate profit for ETH arbitrage",
    "context": {
      "buy_price": 2500,
      "sell_price": 2505,
      "amount": 1000
    }
  }'
```

### 3. RAG Query

```bash
# Query the knowledge base
curl -X POST http://localhost:8000/agent/rag/direct \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the best practices for flash loan arbitrage?",
    "context": {}
  }'
```

### 4. Code Execution

```bash
# Execute code through code interpreter
curl -X POST http://localhost:8000/agent/code_interpreter/direct \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate the profit for buying 1 ETH at $2500 and selling at $2505, with $50 gas cost",
    "context": {}
  }'
```

## Service Endpoints

### Main Coordinator (Port 8000)
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /status` - Detailed system status
- `GET /agents` - List all agents
- `POST /agent/process` - Process through multi-agent system
- `POST /agent/{agent_name}/direct` - Direct agent communication

### RAG Service (Port 8003)
- `GET /health` - RAG service health
- `POST /search` - Search knowledge base
- `POST /add_document` - Add document to knowledge base

### Code Interpreter (Port 8004)
- `GET /health` - Code interpreter health
- `POST /execute` - Execute code safely

### Monitoring

- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090
- **RabbitMQ Management**: http://localhost:15672 (flash_loan_mq/flash_loan_mq_2025)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `LLM_MODEL` | Default LLM model | gpt-4-turbo-preview |
| `LOG_LEVEL` | Logging level | INFO |
| `ENABLE_CODE_EXECUTION` | Enable code execution | true |
| `VECTOR_STORE_PROVIDER` | Vector store provider | chroma |

### Configuration File

Create `/app/config.json` for detailed configuration:

```json
{
  "llm": {
    "model_name": "gpt-4-turbo-preview",
    "temperature": 0.1,
    "max_tokens": 2000
  },
  "vector_store": {
    "provider": "chroma",
    "collection_name": "flash_loan_knowledge"
  },
  "agent": {
    "max_concurrent_tasks": 5,
    "task_timeout": 300
  },
  "security": {
    "enable_code_execution": true,
    "execution_timeout": 30
  }
}
```

## Agent Capabilities

### Arbitrage Agent
- Price difference detection across DEXs
- Profit/loss calculations
- Opportunity ranking and prioritization
- Gas cost optimization analysis

### Risk Agent
- Risk assessment and scoring
- Safety parameter validation
- Exposure monitoring
- Risk mitigation recommendations

### RAG Agent
- Document retrieval and analysis
- Knowledge base management
- Context-aware question answering
- Information synthesis

### Code Interpreter Agent
- Safe Python code execution
- Mathematical calculations
- Data analysis and visualization
- Smart contract analysis

## Development

### Adding Custom Agents

1. Create agent class in `agents/custom_agent.py`:
```python
class CustomAgent:
    def __init__(self, name: str, memory_manager, tool_registry):
        # Agent initialization
        pass
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Agent processing logic
        pass
```

2. Register in `main.py`:
```python
system_state.agents["custom"] = CustomAgent(
    name="CustomAgent",
    memory_manager=system_state.memory_manager,
    tool_registry=system_state.tool_registry
)
```

### Adding Custom Tools

```python
await tool_registry.register_tool(
    "custom_calculation",
    "Description of the tool",
    custom_function,
    {
        "param1": {"type": "float", "description": "Parameter description"},
        "param2": {"type": "string", "description": "Parameter description"}
    },
    "custom_category"
)
```

## Troubleshooting

### Common Issues

1. **Container won't start**:
   ```bash
   # Check logs
   docker logs flash-loan-langchain-coordinator
   
   # Check dependencies
   docker-compose -f docker-compose.langchain-enhanced.yml ps
   ```

2. **API key errors**:
   - Verify `.env` file has correct API keys
   - Restart containers after adding keys

3. **Memory issues**:
   - Increase Docker memory allocation
   - Check vector store disk usage

4. **Agent not responding**:
   ```bash
   # Check agent status
   curl http://localhost:8000/agents
   
   # Check system status
   curl http://localhost:8000/status
   ```

### Health Checks

```bash
# Main system health
curl http://localhost:8000/health

# Individual service health
curl http://localhost:8003/health  # RAG
curl http://localhost:8004/health  # Code Interpreter

# Database connections
docker exec flash-loan-postgres-langchain pg_isready
docker exec flash-loan-redis-langchain redis-cli ping
```

## Security Considerations

- Code execution is sandboxed with timeouts
- Database connections use authenticated users
- File system access is restricted
- Network isolation through Docker networks

## Performance Optimization

- Vector store uses persistent storage
- Redis caching for frequently accessed data
- Connection pooling for databases
- Horizontal scaling support for agents

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create GitHub issue
- Check troubleshooting section
- Review logs for error details
