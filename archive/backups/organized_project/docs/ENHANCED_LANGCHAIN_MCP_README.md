# Enhanced LangChain MCP Integration System

## Overview

This is a comprehensive integration system that combines **LangChain** with **Model Context Protocol (MCP) servers** to create an intelligent, self-healing, and highly coordinated AI system. The system provides advanced features including:

### 🌟 Key Features

- **Advanced LangChain Integration**: Full utilization of LangChain's capabilities including chains, agents, memory, and retrieval
- **Intelligent MCP Server Coordination**: AI-powered routing, load balancing, and health management
- **Self-Healing Architecture**: Automatic detection and recovery from failures
- **Real-time Monitoring**: Comprehensive metrics collection and analysis
- **Web Dashboard**: Beautiful, real-time dashboard for monitoring and control
- **Multi-Agent Orchestration**: Coordinated agents for different specialized tasks
- **Context-Aware Decision Making**: AI-powered decisions for system optimization
- **Predictive Maintenance**: AI-based prediction of maintenance needs

## 🏗️ Architecture

### Core Components

1. **Enhanced LangChain Coordinator** (`enhanced_langchain_coordinator.py`)
   - Main coordination engine using LangChain
   - Multi-agent system with specialized agents
   - Advanced memory management and persistence
   - Custom tools and chains for MCP server interaction

2. **Enhanced MCP Server Manager** (`enhanced_mcp_server_manager.py`)
   - Intelligent MCP server lifecycle management
   - AI-powered load balancing and routing
   - Health monitoring and predictive maintenance
   - Auto-scaling and performance optimization

3. **Complete Integration System** (`complete_langchain_mcp_integration.py`)
   - Unified system that brings everything together
   - Web dashboard and API endpoints
   - Real-time WebSocket communication
   - Comprehensive monitoring and metrics

4. **System Launcher** (`launch_enhanced_system.py`)
   - Automated dependency checking and setup
   - Service initialization and configuration
   - Easy system startup with pre-flight checks

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard & API                      │
│                 (http://localhost:8000)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│              Complete Integration System                     │
│  • WebSocket Real-time Updates                             │
│  • RESTful API Endpoints                                   │
│  • System Monitoring & Metrics                            │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
┌─────────────┴───────────────┐ ┌─────────┴───────────────────┐
│  Enhanced LangChain         │ │  Enhanced MCP Server        │
│  Coordinator                │ │  Manager                    │
│  • Multi-agent system       │ │  • Intelligent routing      │
│  • Memory & context         │ │  • Health monitoring        │
│  • Decision chains          │ │  • Load balancing          │
│  • Tool integration         │ │  • Auto-scaling            │
└─────────────┬───────────────┘ └─────────┬───────────────────┘
              │                           │
              └───────────┬───────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                    MCP Servers                              │
│  • context7-mcp (port 8001)                               │
│  • enhanced-copilot-mcp (port 8002)                       │
│  • blockchain-mcp (port 8003)                             │
│  • price-oracle-mcp (port 8004)                           │
│  • dex-services-mcp (port 8005)                           │
│  • flash-loan-mcp (port 8006)                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker Desktop (recommended)
- 8GB+ RAM
- 2GB+ free disk space

### Installation

1. **Clone/Download the project** to your local machine

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the system** (choose one method):

   **Method 1: Using the launcher script**
   ```bash
   python launch_enhanced_system.py
   ```

   **Method 2: Using batch file (Windows)**
   ```cmd
   start_enhanced_system.bat
   ```

   **Method 3: Using PowerShell (Windows)**
   ```powershell
   .\start_enhanced_system.ps1
   ```

4. **Access the dashboard**:
   - Open your browser and go to: http://localhost:8000
   - The dashboard provides real-time monitoring and control

### Configuration

The system uses `enhanced_coordinator_config.yaml` for configuration. A default configuration is created automatically on first run, but you can customize:

```yaml
# MCP Server Configuration
mcp_servers:
  context7-mcp:
    port: 8001
    capabilities: ['context', 'search', 'retrieval']
    priority: 1
    
# LLM Configuration  
llm:
  model: 'llama2'  # or 'gpt-4' with API key
  temperature: 0.7
  
# Memory Configuration
memory:
  type: 'summary_buffer'
  max_token_limit: 2000
```

## 📊 Features Deep Dive

### LangChain Enhanced Features

#### 1. Multi-Agent System
- **Coordinator Agent**: Main orchestration agent
- **Analyzer Agent**: Specialized in data analysis
- **Executor Agent**: Handles action execution

#### 2. Advanced Chains
- **Health Analysis Chain**: AI-powered system health assessment
- **MCP Coordination Chain**: Intelligent server routing decisions
- **Performance Optimization Chain**: System optimization recommendations

#### 3. Memory Management
- **Conversation Buffer Memory**: Short-term context retention
- **Summary Buffer Memory**: Compressed long-term memory
- **Entity Memory**: Entity-specific context storage

#### 4. Custom Tools
- **MCP Server Tool**: Direct interaction with MCP servers
- **System Status Tool**: Real-time system information
- **Service Restart Tool**: Automated service management
- **Log Analysis Tool**: Intelligent log parsing and insights

### MCP Server Coordination

#### 1. Intelligent Routing
- **Capability-based routing**: Routes requests to servers with relevant capabilities
- **AI-powered decisions**: Uses LangChain to make optimal routing choices
- **Load balancing**: Distributes load based on server health and capacity

#### 2. Health Monitoring
- **Real-time health checks**: Continuous monitoring of all MCP servers
- **AI health analysis**: LangChain-powered health assessment
- **Predictive failure detection**: Early warning system for potential issues

#### 3. Auto-scaling
- **Dynamic scaling**: Automatically scales servers based on demand
- **Performance optimization**: Continuous performance tuning
- **Resource management**: Intelligent resource allocation

### Web Dashboard Features

#### 1. Real-time Monitoring
- **System Status**: Live system health and metrics
- **Server Status**: Individual MCP server monitoring
- **Performance Metrics**: CPU, memory, response times
- **Active Connections**: WebSocket and API connections

#### 2. Interactive Control
- **Query Interface**: Direct interaction with the LangChain system
- **Server Management**: Start, stop, restart individual servers
- **Configuration**: Live configuration updates
- **Log Viewer**: Real-time log streaming

#### 3. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/api/status` | GET | System status |
| `/api/servers` | GET | MCP server status |
| `/api/execute` | POST | Execute MCP command |
| `/api/query` | POST | LangChain query |
| `/api/metrics` | GET | System metrics |
| `/api/restart/{server}` | POST | Restart server |
| `/ws` | WebSocket | Real-time updates |

## 🔧 Advanced Configuration

### LLM Configuration Options

```yaml
llm:
  # Local LLM (Ollama)
  provider: 'ollama'
  model: 'llama2'
  temperature: 0.7
  
  # Or OpenAI
  provider: 'openai'
  model: 'gpt-4'
  api_key: 'your-api-key'
  temperature: 0.7
```

### Memory Configuration Options

```yaml
memory:
  # Buffer Memory
  type: 'buffer'
  buffer_size: 100
  
  # Summary Buffer Memory (recommended)
  type: 'summary_buffer'
  max_token_limit: 2000
  
  # Entity Memory
  type: 'entity'
  entity_extraction_llm: 'llama2'
```

### Monitoring Configuration

```yaml
monitoring:
  health_check_interval: 30  # seconds
  metrics_collection_interval: 60  # seconds
  auto_restart_on_failure: true
  
  thresholds:
    cpu_usage_warning: 70
    memory_usage_warning: 80
    response_time_warning: 5.0
```

## 🛠️ Development and Customization

### Adding New MCP Servers

1. **Add to configuration**:
```yaml
mcp_servers:
  your-custom-mcp:
    port: 8007
    capabilities: ['custom', 'feature']
    priority: 1
```

2. **Implement server endpoints**:
- `GET /health` - Health check
- `POST /execute` - Command execution

### Creating Custom Agents

```python
from langchain.agents import create_react_agent

# Define custom tools
custom_tools = [
    Tool(
        name="custom_tool",
        description="Your custom tool description",
        func=your_custom_function
    )
]

# Create custom agent
custom_agent = create_react_agent(
    llm=self.llm,
    tools=custom_tools,
    prompt=your_custom_prompt
)
```

### Adding Custom Chains

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Define custom chain
custom_prompt = PromptTemplate(
    input_variables=["input"],
    template="Your custom prompt template: {input}"
)

custom_chain = LLMChain(
    llm=self.llm,
    prompt=custom_prompt
)
```

## 📈 Monitoring and Observability

### Metrics Available

1. **System Metrics**:
   - CPU usage, memory usage, disk usage
   - Network I/O, active connections
   - Response times, error rates

2. **MCP Server Metrics**:
   - Health scores, response times
   - Success rates, error counts
   - Active connections, throughput

3. **LangChain Metrics**:
   - Agent execution times
   - Chain success rates
   - Memory usage patterns

### Logging

The system provides comprehensive logging:

- **Application logs**: `enhanced_langchain_coordinator.log`
- **Integration logs**: `complete_integration.log`
- **Server manager logs**: Console and file output
- **WebSocket logs**: Real-time browser console

### Health Checks

Automated health checks include:

- **Service availability**: Port connectivity tests
- **Response time monitoring**: Performance tracking
- **Error rate analysis**: Failure pattern detection
- **Resource utilization**: System resource monitoring

## 🔒 Security Considerations

### API Security

- **CORS**: Configurable cross-origin resource sharing
- **Rate limiting**: Request rate limiting (configurable)
- **API keys**: Optional API key authentication

### Network Security

- **Local binding**: Services bind to localhost by default
- **Docker networks**: Isolated Docker networks for services
- **Port management**: Configurable port assignments

## 🐛 Troubleshooting

### Common Issues

1. **Docker not available**:
   - Install Docker Desktop
   - Ensure Docker daemon is running
   - Check Docker permissions

2. **Port conflicts**:
   - Check if ports 8000-8006 are available
   - Modify configuration to use different ports
   - Stop conflicting services

3. **Memory issues**:
   - Ensure at least 8GB RAM available
   - Adjust memory limits in configuration
   - Monitor system resources

4. **LLM model issues**:
   - Ensure Ollama is installed for local models
   - Check API keys for cloud models
   - Verify model availability

### Debug Mode

Enable debug logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

### System Status Checks

Use the built-in status endpoints:

```bash
# Check system status
curl http://localhost:8000/api/status

# Check server status
curl http://localhost:8000/api/servers

# Check metrics
curl http://localhost:8000/api/metrics
```

## 📚 Advanced Usage Examples

### Example 1: Custom Query Processing

```python
# Send a query to the system
import requests

response = requests.post('http://localhost:8000/api/query', 
                        json={'query': 'Analyze the current system performance'})
result = response.json()
print(result['result'])
```

### Example 2: Direct MCP Server Interaction

```python
# Execute command on specific MCP server
response = requests.post('http://localhost:8000/api/execute',
                        json={
                            'server': 'blockchain-mcp',
                            'command': 'get_latest_block'
                        })
result = response.json()
```

### Example 3: WebSocket Real-time Monitoring

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'status_update') {
        console.log('System status:', data.data);
    }
};
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8 mypy
   ```
4. Run tests:
   ```bash
   pytest tests/
   ```
5. Format code:
   ```bash
   black *.py
   flake8 *.py
   ```

### Code Structure

```
├── enhanced_langchain_coordinator.py    # Main LangChain coordinator
├── enhanced_mcp_server_manager.py       # MCP server management
├── complete_langchain_mcp_integration.py # Integration system
├── launch_enhanced_system.py            # System launcher
├── enhanced_coordinator_config.yaml     # Configuration
├── requirements.txt                     # Dependencies
├── start_enhanced_system.bat            # Windows launcher
├── start_enhanced_system.ps1            # PowerShell launcher
└── README.md                           # This file
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangChain**: For the powerful AI framework
- **Model Context Protocol**: For the server coordination standard
- **Docker**: For containerization support
- **Ollama**: For local LLM support

## 📞 Support

For support and questions:

1. Check the troubleshooting section above
2. Review the system logs for error details
3. Use the web dashboard for real-time diagnostics
4. Check the API endpoints for system status

---

**Happy Coding! 🚀**
