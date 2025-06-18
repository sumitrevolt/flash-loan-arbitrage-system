# src/flash_loan/core/dex_integration_singleton.py
from .dex_integration import DEXIntegration

class DEXIntegrationSingleton:
    _instance = None
    _initialized_successfully = False # New flag to track successful initialization

    @staticmethod
    def initialize(rpc_manager=None):
        # Only attempt initialization if not already successfully done
        if not DEXIntegrationSingleton._initialized_successfully:
            try:
                # Attempt to create the DEXIntegration instance
                instance = DEXIntegration(rpc_manager=rpc_manager)
                DEXIntegrationSingleton._instance = instance
                # Mark as successfully initialized
                DEXIntegrationSingleton._initialized_successfully = True
                # Optional: Log successful initialization if a logger is available
                # For example, if using standard logging:
                # import logging
                # logging.getLogger(__name__).info("DEXIntegrationSingleton initialized successfully.")
            except Exception as e:
                # Ensure instance is None and flag is False if initialization fails
                DEXIntegrationSingleton._instance = None
                DEXIntegrationSingleton._initialized_successfully = False
                # Log the error if a logger is available.
                # import logging
                # logging.getLogger(__name__).error(f"Failed to initialize DEXIntegration: {e}", exc_info=True)
                # For the singleton pattern, it's often better to let get_instance() report the failure
                # rather than re-raising the exception here, to avoid crashing the initial call site
                # if the error is recoverable or needs specific handling by the main application logic.
                pass # Keep _initialized_successfully as False, error will be caught by get_instance
        return DEXIntegrationSingleton._instance

    @staticmethod
    def get_instance():
        # If not initialized, try to initialize (e.g., with default rpc_manager=None if initialize() is called by this path)
        if not DEXIntegrationSingleton._initialized_successfully:
            DEXIntegrationSingleton.initialize()  # This attempts initialization, potentially with rpc_manager=None

        # After attempting initialization (either explicit or automatic via the call above), check the flag
        if not DEXIntegrationSingleton._initialized_successfully:
            raise RuntimeError(
                "DEXIntegrationSingleton could not be initialized. "
                "Ensure DEXIntegration class can be instantiated correctly (it may require a valid rpc_manager) "
                "and that DEXIntegrationSingleton.initialize() is called successfully before get_instance()."
            )
        return DEXIntegrationSingleton._instance

# Helper functions for easier access
def initialize(rpc_manager=None):
    return DEXIntegrationSingleton.initialize(rpc_manager)

def get_instance():
    return DEXIntegrationSingleton.get_instance()

# Export the singleton class as dex_integration without initializing it right away
# This allows importing it without requiring immediate initialization
class DexIntegrationProxy:
    def __getattr__(self, name):
        return getattr(DEXIntegrationSingleton.get_instance(), name)
    
# Create a proxy instance that will lazily get the real instance when needed
dex_integration = DexIntegrationProxy()
