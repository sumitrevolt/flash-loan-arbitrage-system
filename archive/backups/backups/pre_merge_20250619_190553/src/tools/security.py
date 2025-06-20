import os
import pathlib

def is_safe_path(base_dir, path):
    """
    Verify that a path doesn't contain symlinks and is within the base directory
    
    Args:
        base_dir (str): The base directory that should contain the path
        path (str): The path to verify
        
    Returns:
        bool: True if the path is safe, False otherwise
    """
    # Resolve the real path (following symlinks)
    real_base = os.path.realpath(base_dir)
    real_path = os.path.realpath(path)
    
    # Check if the path is within the base directory
    return os.path.commonpath([real_base]) == os.path.commonpath([real_base, real_path])

def validate_file_path(path):
    """
    Validate a file path to ensure it doesn't contain symlinks
    
    Args:
        path (str): The path to validate
        
    Returns:
        bool: True if the path is valid, False otherwise
    """
    try:
        # Check if the path contains symlinks
        path_obj = pathlib.Path(path)
        return path_obj.resolve() == path_obj.absolute()
    except (ValueError, OSError):
        return False