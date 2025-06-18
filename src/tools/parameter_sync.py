"""
Parameter synchronizer for flash loan arbitrage.

This module synchronizes tuned parameters across different components
of the flash loan arbitrage system.
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List

# Set up logging
logger = logging.getLogger(__name__)

class ParameterSynchronizer:
    """
    Synchronizes parameters across different components of the system.
    """
    
    def __init__(self, config_path: str = "config/parameter_sync_config.json"):
        """
        Initialize the parameter synchronizer.
        
        Args:
            config_path: Path to the parameter synchronizer configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load parameter synchronizer configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading parameter synchronizer config: {e}")
            
        # Default configuration
        return {
            "parameter_mappings": {
                "slippage.base_slippage": [
                    {
                        "config_file": "config/slippage_config.json",
                        "target_path": "base_slippage"
                    }
                ],
                "slippage.max_slippage": [
                    {
                        "config_file": "config/slippage_config.json",
                        "target_path": "max_slippage"
                    }
                ],
                "slippage.volatility_factor": [
                    {
                        "config_file": "config/slippage_config.json",
                        "target_path": "volatility_factor"
                    }
                ],
                "circuit_breaker.max_consecutive_failures": [
                    {
                        "config_file": "config/circuit_breaker_config.json",
                        "target_path": "max_consecutive_failures"
                    }
                ],
                "circuit_breaker.cooldown_period_seconds": [
                    {
                        "config_file": "config/circuit_breaker_config.json",
                        "target_path": "cooldown_period_seconds"
                    }
                ],
                "gas.gas_price_multipliers.standard": [
                    {
                        "config_file": "config/gas_optimizer_config.json",
                        "target_path": "gas_price_multipliers.standard"
                    }
                ],
                "gas.gas_price_multipliers.fast": [
                    {
                        "config_file": "config/gas_optimizer_config.json",
                        "target_path": "gas_price_multipliers.fast"
                    }
                ],
                "retry.max_retries": [
                    {
                        "config_file": "config/auto_executor_config.json",
                        "target_path": "max_retries"
                    }
                ],
                "retry.retry_delay": [
                    {
                        "config_file": "config/auto_executor_config.json",
                        "target_path": "retry_delay"
                    }
                ],
                "trade.min_profit_threshold_usd": [
                    {
                        "config_file": "config/auto_executor_config.json",
                        "target_path": "min_profit_threshold_usd"
                    }
                ],
                "trade.min_profit_percentage": [
                    {
                        "config_file": "config/auto_executor_config.json",
                        "target_path": "min_profit_percentage"
                    }
                ]
            },
            "token_specific_mappings": {
                "slippage.base_slippage": [
                    {
                        "config_file": "config/slippage_config.json",
                        "target_path": "token_specific_adjustments.{token}"
                    }
                ]
            },
            "dex_specific_mappings": {
                "gas.gas_price_multipliers.standard": [
                    {
                        "config_file": "config/gas_optimizer_config.json",
                        "target_path": "dex_specific_adjustments.{dex}"
                    }
                ]
            }
        }
    
    def sync_parameters(self, parameters: Dict[str, Any], token_specific: Optional[Dict[str, Dict[str, Any]]] = None, dex_specific: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """
        Synchronize parameters across different components.
        
        Args:
            parameters: Global parameters to synchronize
            token_specific: Token-specific parameters to synchronize
            dex_specific: DEX-specific parameters to synchronize
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = True
        
        # Synchronize global parameters
        for param_key, param_value in parameters.items():
            if param_key in self.config.get("parameter_mappings", {}):
                mappings = self.config["parameter_mappings"][param_key]
                for mapping in mappings:
                    config_file = mapping.get("config_file")
                    target_path = mapping.get("target_path")
                    
                    if config_file and target_path:
                        if not self._update_config_value(config_file, target_path, param_value):
                            success = False
        
        # Synchronize token-specific parameters
        if token_specific:
            for token, token_params in token_specific.items():
                for param_key, param_value in token_params.items():
                    if param_key in self.config.get("token_specific_mappings", {}):
                        mappings = self.config["token_specific_mappings"][param_key]
                        for mapping in mappings:
                            config_file = mapping.get("config_file")
                            target_path = mapping.get("target_path")
                            
                            if config_file and target_path:
                                # Replace {token} placeholder with actual token
                                target_path = target_path.replace("{token}", token)
                                
                                if not self._update_config_value(config_file, target_path, param_value):
                                    success = False
        
        # Synchronize DEX-specific parameters
        if dex_specific:
            for dex, dex_params in dex_specific.items():
                for param_key, param_value in dex_params.items():
                    if param_key in self.config.get("dex_specific_mappings", {}):
                        mappings = self.config["dex_specific_mappings"][param_key]
                        for mapping in mappings:
                            config_file = mapping.get("config_file")
                            target_path = mapping.get("target_path")
                            
                            if config_file and target_path:
                                # Replace {dex} placeholder with actual DEX
                                target_path = target_path.replace("{dex}", dex)
                                
                                if not self._update_config_value(config_file, target_path, param_value):
                                    success = False
        
        return success
    
    def _update_config_value(self, config_file: str, target_path: str, value: Any) -> bool:
        """
        Update a value in a configuration file.
        
        Args:
            config_file: Path to the configuration file
            target_path: Path to the target value in the configuration
            value: New value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if the config file exists
            if not os.path.exists(config_file):
                self.logger.warning(f"Config file {config_file} does not exist")
                return False
            
            # Load the configuration file
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Update the value
            if "." in target_path:
                # Handle nested paths
                parts = target_path.split(".")
                target = config
                
                # Navigate to the target location
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        # Last part - update the value
                        target[part] = value
                    else:
                        # Create nested dictionaries if they don't exist
                        if part not in target:
                            target[part] = {}
                        target = target[part]
            else:
                # Handle top-level paths
                config[target_path] = value
            
            # Save the updated configuration
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Updated {target_path} in {config_file} to {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating {target_path} in {config_file}: {e}")
            return False
    
    def load_all_configs(self) -> Dict[str, Any]:
        """
        Load all configuration files referenced in the parameter mappings.
        
        Returns:
            Dict[str, Any]: Dictionary of loaded configurations
        """
        configs = {}
        
        # Get all unique config files
        config_files = set()
        
        for mappings in self.config.get("parameter_mappings", {}).values():
            for mapping in mappings:
                config_files.add(mapping.get("config_file"))
        
        for mappings in self.config.get("token_specific_mappings", {}).values():
            for mapping in mappings:
                config_files.add(mapping.get("config_file"))
        
        for mappings in self.config.get("dex_specific_mappings", {}).values():
            for mapping in mappings:
                config_files.add(mapping.get("config_file"))
        
        # Load each config file
        for config_file in config_files:
            if config_file and os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        configs[config_file] = json.load(f)
                except Exception as e:
                    self.logger.error(f"Error loading {config_file}: {e}")
        
        return configs
    
    def extract_current_parameters(self) -> Dict[str, Any]:
        """
        Extract current parameter values from all configuration files.
        
        Returns:
            Dict[str, Any]: Dictionary of current parameter values
        """
        parameters = {}
        configs = self.load_all_configs()
        
        # Extract global parameters
        for param_key, mappings in self.config.get("parameter_mappings", {}).items():
            for mapping in mappings:
                config_file = mapping.get("config_file")
                target_path = mapping.get("target_path")
                
                if config_file in configs and target_path:
                    value = self._get_config_value(configs[config_file], target_path)
                    if value is not None:
                        parameters[param_key] = value
                        break  # Use the first mapping that works
        
        return parameters
    
    def _get_config_value(self, config: Dict[str, Any], target_path: str) -> Any:
        """
        Get a value from a configuration dictionary.
        
        Args:
            config: Configuration dictionary
            target_path: Path to the target value in the configuration
            
        Returns:
            Any: The value at the target path, or None if not found
        """
        try:
            if "." in target_path:
                # Handle nested paths
                parts = target_path.split(".")
                target = config
                
                # Navigate to the target location
                for part in parts:
                    if part in target:
                        target = target[part]
                    else:
                        return None
                
                return target
            else:
                # Handle top-level paths
                return config.get(target_path)
                
        except Exception as e:
            self.logger.error(f"Error getting value at {target_path}: {e}")
            return None
