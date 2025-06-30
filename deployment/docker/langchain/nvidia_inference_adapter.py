#!/usr/bin/env python3
"""
NVIDIA Inference Adapter for LangChain MCP Server Agents
Provides GPU-accelerated inference capabilities using NVIDIA TensorRT and Triton
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
import numpy as np
import tritonclient.grpc as grpcclient
import tritonclient.http as httpclient
from transformers import AutoTokenizer
import torch
from pathlib import Path
import nvidia_smi
from tritonclient.grpc import InferenceServerClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NVIDIAInferenceAdapter:
    """Adapter for NVIDIA Inference integration with MCP servers"""
    
    def __init__(self, config_path: str = "nvidia_inference_config.yaml"):
        """
        Initialize the NVIDIA Inference Adapter with the given configuration.
        """
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Triton Inference Server client
        self.triton_client = InferenceServerClient(
            url=f"{self.config['triton']['host']}:{self.config['triton']['port']}"
        )
        
        # Initialize NVIDIA SMI for GPU monitoring
        nvidia_smi.nvmlInit()
        
        self.tokenizers = {}
        self._load_tokenizers()
        
    def _load_tokenizers(self):
        """Load tokenizers for configured models"""
        for model_name, model_config in self.config.get("models", {}).items():
            try:
                if "llama" in model_name.lower():
                    self.tokenizers[model_name] = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
                elif "mistral" in model_name.lower():
                    self.tokenizers[model_name] = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
                elif "bge" in model_name.lower():
                    self.tokenizers[model_name] = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
                logger.info(f"Loaded tokenizer for {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load tokenizer for {model_name}: {e}")
                
    def generate_text(self, prompt: str, model_name: str = "text-generation") -> str:
        """
        Generate text using the specified NVIDIA model.
        """
        try:
            # Placeholder for actual inference logic
            logger.info(f"Generating text for prompt: {prompt}")
            return f"Generated text for: {prompt}"
        except Exception as e:
            logger.error(f"Error in text generation: {e}")
            raise
    
    def get_embeddings(self, text: str, model_name: str = "embeddings") -> List[float]:
        """
        Get embeddings for the given text using the specified NVIDIA model.
        """
        try:
            # Placeholder for actual inference logic
            logger.info(f"Generating embeddings for text: {text}")
            return [0.1, 0.2, 0.3]  # Dummy embeddings
        except Exception as e:
            logger.error(f"Error in embeddings generation: {e}")
            raise
    
    def monitor_gpu(self) -> Dict[str, Any]:
        """
        Monitor GPU usage and return statistics.
        """
        try:
            handle = nvidia_smi.nvmlDeviceGetHandleByIndex(self.config['gpu']['device_id'])
            util = nvidia_smi.nvmlDeviceGetUtilizationRates(handle)
            memory = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
            
            return {
                "gpu_utilization": util.gpu,
                "memory_utilization": util.memory,
                "memory_used": memory.used,
                "memory_total": memory.total
            }
        except Exception as e:
            logger.error(f"Error in GPU monitoring: {e}")
            raise
    
    def __del__(self):
        """
        Cleanup NVIDIA SMI on object destruction.
        """
        nvidia_smi.nvmlShutdown()


# Singleton instance
_nvidia_adapter = None


def get_nvidia_adapter() -> NVIDIAInferenceAdapter:
    """Get or create the NVIDIA Inference adapter singleton"""
    global _nvidia_adapter
    if _nvidia_adapter is None:
        _nvidia_adapter = NVIDIAInferenceAdapter()
    return _nvidia_adapter


# Integration functions for MCP servers
def nvidia_generate_text(prompt: str, **kwargs) -> str:
    """Generate text using NVIDIA-accelerated inference"""
    adapter = get_nvidia_adapter()
    return adapter.generate_text(prompt, **kwargs)


def nvidia_generate_embeddings(texts: List[str], **kwargs) -> np.ndarray:
    """Generate embeddings using NVIDIA-accelerated inference"""
    adapter = get_nvidia_adapter()
    return adapter.generate_embeddings(texts, **kwargs)


def get_mcp_optimization_config(server_name: str) -> Dict[str, Any]:
    """Get NVIDIA optimization configuration for a specific MCP server"""
    adapter = get_nvidia_adapter()
    return adapter.optimize_for_mcp_server(server_name) 