# NVIDIA Inference Integration for LangChain MCP Server Agents

This guide explains how to set up and use NVIDIA Inference (TensorRT, Triton) to power your LangChain MCP server agents with GPU-accelerated inference.

## Overview

The integration provides:
- **GPU-accelerated inference** using NVIDIA TensorRT
- **Optimized model serving** via Triton Inference Server
- **Automatic batching** for improved throughput
- **FP16/INT8 quantization** for faster inference
- **Multi-GPU support** for scaling

## Prerequisites

1. **NVIDIA GPU** with compute capability 7.0+ (e.g., V100, T4, A100, RTX 3090)
2. **NVIDIA Driver** version 525.60.13 or later
3. **Docker** with NVIDIA Container Toolkit installed
4. **CUDA** 12.3 or compatible version

## Quick Start

### 1. Install NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. Deploy with Docker Compose

```bash
cd deployment/docker/langchain

# Start services with NVIDIA support
docker-compose -f docker-compose.nvidia.yml up -d
```

### 3. Verify GPU Access

```bash
# Check if GPU is accessible
docker run --rm --gpus all nvidia/cuda:12.3.1-base-ubuntu22.04 nvidia-smi

# Check Triton server status
curl http://localhost:8000/v2/health/ready
```

## Configuration

### Model Configuration

Edit `nvidia_inference_config.yaml` to configure models:

```yaml
models:
  llama2-7b:
    backend: "tensorrt_llm"
    max_batch_size: 16
    optimization:
      use_fp16: true
```

### MCP Server Integration

Enable NVIDIA for specific MCP servers:

```yaml
mcp_integration:
  enabled_servers:
    - "context7-mcp"
    - "enhanced-copilot-mcp"
    - "ai-integration-mcp"
```

## Usage Examples

### Python Integration

```python
from nvidia_inference_adapter import nvidia_generate_text

# Generate text with GPU acceleration
response = nvidia_generate_text(
    prompt="Explain flash loan arbitrage",
    model_name="llama2-7b",
    max_tokens=512,
    temperature=0.7
)
```

### REST API

```bash
# Generate text
curl -X POST http://localhost:8004/inference/text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is a flash loan?",
    "max_tokens": 200,
    "use_nvidia": true
  }'

# Generate embeddings
curl -X POST http://localhost:8004/inference/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Flash loan arbitrage", "DeFi protocols"],
    "use_nvidia": true
  }'
```

## Performance Optimization

### 1. Batch Processing

Configure dynamic batching in `nvidia_inference_config.yaml`:

```yaml
dynamic_batching:
  preferred_batch_size: [4, 8, 16]
  max_queue_delay_microseconds: 100
```

### 2. Memory Optimization

```yaml
optimization:
  tensorrt:
    workspace_size_mb: 4096
    precision_mode: "fp16"  # or "int8" for more aggressive optimization
```

### 3. Multi-GPU Setup

```yaml
gpu:
  device_ids: [0, 1, 2, 3]  # Use multiple GPUs
  per_process_gpu_memory_fraction: 0.9
```

## Monitoring

### GPU Metrics

Access GPU metrics at `http://localhost:9400/metrics`:

```bash
# View GPU utilization
curl http://localhost:9400/metrics | grep dcgm
```

### Health Checks

```bash
# Check MCP server health with GPU info
curl http://localhost:8004/health
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   ```yaml
   # Reduce batch size or model precision
   max_batch_size: 8
   precision_mode: "fp16"
   ```

2. **Triton Server Connection Failed**
   ```bash
   # Check if Triton is running
   docker logs triton-server
   ```

3. **Model Loading Error**
   ```bash
   # Verify model repository structure
   ls -la ./models/
   ```

### Debug Mode

Enable debug logging:

```yaml
# In docker-compose.nvidia.yml
environment:
  - LOG_LEVEL=DEBUG
  - TRITON_SERVER_LOG_VERBOSE=1
```

## Performance Benchmarks

Typical performance improvements with NVIDIA Inference:

| Model | CPU Inference | GPU Inference (FP32) | GPU Inference (FP16) |
|-------|--------------|---------------------|---------------------|
| Llama2-7B | 150ms/token | 25ms/token | 12ms/token |
| Mistral-7B | 140ms/token | 22ms/token | 11ms/token |
| BGE-Large | 50ms/batch | 8ms/batch | 4ms/batch |

## Advanced Features

### Custom Model Deployment

1. Convert models to TensorRT:
   ```bash
   python convert_to_tensorrt.py --model llama2-7b --precision fp16
   ```

2. Deploy to Triton:
   ```bash
   cp -r converted_model/ ./models/llama2-7b-tensorrt/
   ```

### Integration with LangChain Agents

```python
from langchain.agents import initialize_agent
from example_nvidia_mcp_integration import create_nvidia_powered_langchain_tool

# Create agent with NVIDIA-powered tool
nvidia_tool = create_nvidia_powered_langchain_tool()
agent = initialize_agent(
    tools=[nvidia_tool],
    llm=llm,
    agent="zero-shot-react-description"
)
```

## Support

For issues or questions:
1. Check logs: `docker logs <container-name>`
2. Monitor GPU: `nvidia-smi -l 1`
3. Review Triton docs: https://docs.nvidia.com/deeplearning/triton-inference-server/ 