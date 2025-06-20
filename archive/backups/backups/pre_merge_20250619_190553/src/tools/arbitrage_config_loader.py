"""
Arbitrage configuration loader for flash loan system
"""
import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    'enable_flash_loan_arbitrage': True,
    'enable_direct_arbitrage': False,
    'enable_triangular_arbitrage': False,
    'flash_loan_provider': 'aave',
    'arbitrage_type': 'flash_loan_only'
}

def get_config_path():
    """Get the path to the arbitrage configuration file"""
    # Try to find the config directory
    base_dirs = [
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),  # Project root
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # src directory
        os.getcwd()  # Current working directory
    ]
    
    for base_dir in base_dirs:
        config_dir = os.path.join(base_dir, 'config')
        if os.path.exists(config_dir):
            return os.path.join(config_dir, 'arbitrage_config.json')
    
    # If no config directory found, create one in the current working directory
    os.makedirs('config', exist_ok=True)
    return os.path.join('config', 'arbitrage_config.json')

def load_arbitrage_config():
    """Load arbitrage configuration from file or create default"""
    config_path = get_config_path()
    
    # Check if config file exists
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded arbitrage configuration from {config_path}")
                
                # Ensure all required keys are present
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                        logger.warning(f"Missing key '{key}' in config, using default: {value}")
                
                # Force flash loan arbitrage only
                config['enable_flash_loan_arbitrage'] = True
                config['enable_direct_arbitrage'] = False
                config['enable_triangular_arbitrage'] = False
                config['flash_loan_provider'] = 'aave'
                config['arbitrage_type'] = 'flash_loan_only'
                
                # Save the updated config
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    logger.info(f"Updated arbitrage configuration in {config_path}")
                
                return config
        except Exception as e:
            logger.error(f"Error loading arbitrage configuration: {e}")
            logger.info("Using default configuration")
            return DEFAULT_CONFIG
    else:
        # Create default config file
        try:
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
                logger.info(f"Created default arbitrage configuration in {config_path}")
            return DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Error creating default arbitrage configuration: {e}")
            return DEFAULT_CONFIG

def is_flash_loan_arbitrage_enabled():
    """Check if flash loan arbitrage is enabled"""
    config = load_arbitrage_config()
    return config.get('enable_flash_loan_arbitrage', True)

def is_direct_arbitrage_enabled():
    """Check if direct arbitrage is enabled"""
    config = load_arbitrage_config()
    return config.get('enable_direct_arbitrage', False)

def is_triangular_arbitrage_enabled():
    """Check if triangular arbitrage is enabled"""
    config = load_arbitrage_config()
    return config.get('enable_triangular_arbitrage', False)

def get_flash_loan_provider():
    """Get the flash loan provider"""
    config = load_arbitrage_config()
    return config.get('flash_loan_provider', 'aave')

def get_arbitrage_type():
    """Get the arbitrage type"""
    config = load_arbitrage_config()
    return config.get('arbitrage_type', 'flash_loan_only')

# Create a hook to be imported by other modules
def init_arbitrage_config():
    """Initialize arbitrage configuration"""
    config = load_arbitrage_config()
    logger.info(f"Arbitrage configuration initialized: {config}")
    return config

# Auto-initialize when imported
config = init_arbitrage_config()

if __name__ == "__main__":
    # If run directly, print the configuration
    print(json.dumps(config, indent=2))
