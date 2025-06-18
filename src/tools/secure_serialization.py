#!/usr/bin/env python3
"""
Secure serialization and deserialization utilities.
Provides safe alternatives to pickle and other insecure serialization methods.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Union, List, Tuple

logger = logging.getLogger("SecureSerialization")

def safe_deserialize(data: Union[str, bytes], 
                     format_type: str = 'json', 
                     trusted_source: bool = False,
                     allowed_classes: Optional[List[type]] = None) -> Any:
    """
    Safely deserialize data from various formats.
    
    Args:
        data: The serialized data to deserialize
        format_type: The format of the data ('json', 'yaml', etc.)
        trusted_source: Whether the data comes from a trusted source
        allowed_classes: List of allowed classes for deserialization
        
    Returns:
        The deserialized data
        
    Raises:
        ValueError: If the format is not supported or the data is invalid
        SecurityError: If the data contains potentially unsafe content
    """
    if not data:
        return None
        
    if format_type.lower() == 'json':
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Error deserializing JSON data: {e}")
            raise ValueError(f"Invalid JSON data: {e}")
    elif format_type.lower() == 'yaml':
        try:
            import yaml
            # Use safe_load to prevent arbitrary code execution
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            return yaml.safe_load(data)
        except ImportError:
            logger.error("YAML support requires PyYAML package")
            raise ValueError("YAML support requires PyYAML package")
        except yaml.YAMLError as e:
            logger.error(f"Error deserializing YAML data: {e}")
            raise ValueError(f"Invalid YAML data: {e}")
    elif format_type.lower() == 'pickle' and trusted_source:
        # Only use pickle if explicitly trusted and allowed_classes is provided
        if not trusted_source:
            raise SecurityError("Pickle deserialization is not allowed from untrusted sources")
        if not allowed_classes:
            raise SecurityError("Pickle deserialization requires a list of allowed classes")
            
        try:
            import pickle
            import io
            from restricted_unpickler import RestrictedUnpickler
            
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            # Use RestrictedUnpickler to limit which classes can be loaded
            unpickler = RestrictedUnpickler(io.BytesIO(data), allowed_classes)
            return unpickler.load()
        except ImportError:
            logger.error("RestrictedUnpickler not available")
            raise ValueError("RestrictedUnpickler not available")
        except Exception as e:
            logger.error(f"Error deserializing pickle data: {e}")
            raise ValueError(f"Invalid pickle data: {e}")
    else:
        raise ValueError(f"Unsupported format: {format_type}")

def safe_serialize(data: Any, format_type: str = 'json') -> Union[str, bytes]:
    """
    Safely serialize data to various formats.
    
    Args:
        data: The data to serialize
        format_type: The format to serialize to ('json', 'yaml', etc.)
        
    Returns:
        The serialized data
        
    Raises:
        ValueError: If the format is not supported or the data cannot be serialized
    """
    if format_type.lower() == 'json':
        try:
            return json.dumps(data, default=_json_serializer)
        except TypeError as e:
            logger.error(f"Error serializing to JSON: {e}")
            raise ValueError(f"Cannot serialize to JSON: {e}")
    elif format_type.lower() == 'yaml':
        try:
            import yaml
            return yaml.safe_dump(data)
        except ImportError:
            logger.error("YAML support requires PyYAML package")
            raise ValueError("YAML support requires PyYAML package")
        except yaml.YAMLError as e:
            logger.error(f"Error serializing to YAML: {e}")
            raise ValueError(f"Cannot serialize to YAML: {e}")
    else:
        raise ValueError(f"Unsupported format: {format_type}")

def _json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for handling non-serializable types.
    
    Args:
        obj: The object to serialize
        
    Returns:
        A JSON-serializable representation of the object
    """
    # Handle common non-serializable types
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'hex'):
        return obj.hex()
    else:
        return str(obj)

class SecurityError(Exception):
    """Exception raised for security-related issues during deserialization."""
    pass

class RestrictedUnpickler:
    """
    A restricted unpickler that only allows certain classes to be loaded.
    
    This helps prevent arbitrary code execution when unpickling data.
    """
    
    def __init__(self, io_bytes, allowed_classes=None):
        """
        Initialize the restricted unpickler.
        
        Args:
            io_bytes: The bytes-like object to unpickle from
            allowed_classes: List of allowed classes for deserialization
        """
        import pickle
        self.unpickler = pickle.Unpickler(io_bytes)
        self.allowed_classes = allowed_classes or []
        self.unpickler.find_class = self.find_class
        
    def find_class(self, module, name):
        """
        Override find_class to restrict which classes can be loaded.
        
        Args:
            module: The module name
            name: The class name
            
        Returns:
            The requested class if allowed
            
        Raises:
            SecurityError: If the class is not allowed
        """
        # Check if the class is in the allowed list
        for allowed_class in self.allowed_classes:
            if module == allowed_class.__module__ and name == allowed_class.__name__:
                return allowed_class
                
        # Allow safe builtins
        if module == 'builtins' and name in ('int', 'float', 'bool', 'str', 'list', 'tuple', 'dict', 'set'):
            import builtins
            return getattr(builtins, name)
            
        # Deny everything else
        raise SecurityError(f"Unpickling class {module}.{name} is not allowed")
        
    def load(self):
        """
        Load and return the unpickled object.
        
        Returns:
            The unpickled object
        """
        return self.unpickler.load()
