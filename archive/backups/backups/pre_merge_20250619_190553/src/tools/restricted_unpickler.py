#!/usr/bin/env python3
"""
Restricted unpickler for secure deserialization of pickle data.
"""


# Use secure_serialization for safe deserialization
from src.utils.secure_serialization import safe_deserialize

import io
from typing import Any, List, Type, Optional

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
            The class object
            
        Raises:
            pickle.UnpicklingError: If the class is not allowed
        """
        # Check if the class is in the allowed list
        for allowed_class in self.allowed_classes:
            if module == allowed_class.__module__ and name == allowed_class.__name__:
                return allowed_class
                
        # Allow basic types
        if module == 'builtins' and name in ('int', 'float', 'bool', 'str', 'list', 'tuple', 'dict', 'set', 'frozenset', 'bytes', 'bytearray'):
            return getattr(__import__(module), name)
            
        # Disallow everything else
        raise pickle.UnpicklingError(f"Restricted unpickler does not allow {module}.{name}")
        
    def load(self):
        """
        Load an object from the pickle data.
        
        Returns:
            The unpickled object
        """
        return self.unpickler.load()
