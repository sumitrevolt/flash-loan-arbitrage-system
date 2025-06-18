#!/usr/bin/env python3
"""
Encrypt the private key in wallet_config.json
"""

import os
import json
from cryptography.fernet import Fernet

def encrypt_private_key():
    """Encrypt the private key in wallet_config.json"""
    try:
        # Load wallet config
        with open("config/wallet_config.json", "r") as f:
            wallet_config = json.load(f)
        
        # Get the encryption key
        encryption_key = wallet_config.get("encryption_key", "")
        print(f"Using encryption key: {encryption_key}")
        
        # Create Fernet cipher with the encryption key
        cipher = Fernet(encryption_key.encode())
        
        # Get the private key for Polygon Mainnet
        private_key = wallet_config["polygon-mainnet"]["privateKey"]
        print(f"Found private key: {private_key}")
        
        # Check if the private key is already encrypted
        if private_key.startswith("gAAAAA"):
            print("Private key is already encrypted")
            return True
        
        # Encrypt the private key
        encrypted_key = cipher.encrypt(private_key.encode()).decode()
        print(f"Encrypted private key: {encrypted_key}")
        
        # Update wallet config
        wallet_config["polygon-mainnet"]["privateKey"] = encrypted_key
        
        # Save wallet config
        with open("config/wallet_config.json", "w") as f:
            json.dump(wallet_config, f, indent=2)
        
        print("Updated wallet_config.json with encrypted private key")
        
        return True
    except Exception as e:
        print(f"Error encrypting private key: {e}")
        return False

if __name__ == "__main__":
    encrypt_private_key()
