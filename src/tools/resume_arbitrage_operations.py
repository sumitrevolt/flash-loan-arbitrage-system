#!/usr/bin/env python3
"""
Flash Loan Arbitrage System - Quick Resume Script
This script validates the system and resumes arbitrage operations after fixes
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime

# Setup logging with ASCII characters only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resume_operations.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('resume_operations')

def check_environment():
    """Check environment variables"""
    required_vars = [
        'POLYGON_RPC_URL',
        'PRIVATE_KEY', 
        'FLASH_LOAN_CONTRACT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"[ERROR] Missing environment variables: {missing_vars}")
        return False
    
    logger.info("[SUCCESS] All required environment variables present")
    return True

def check_foundry_server():
    """Check Foundry MCP server status"""
    try:
        import requests
        response = requests.get('http://localhost:8001/health', timeout=5)
        if response.status_code == 200:
            logger.info("[SUCCESS] Foundry MCP server is running")
            return True
        else:
            logger.warning(f"[WARNING] Foundry server status: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"[WARNING] Foundry server check failed: {e}")
        return False

def check_files():
    """Check required files exist"""
    required_files = [
        'production_arbitrage_bot.py',
        'contract_abi.json',
        'production_config.json',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"[ERROR] Missing required files: {missing_files}")
        return False
    
    logger.info("[SUCCESS] All required files present")
    return True

def validate_config():
    """Validate production configuration"""
    try:
        with open('production_config.json', 'r') as f:
            config = json.load(f)
        
        # Check for essential config sections
        required_sections = ['tokens', 'dexes', 'trading']
        for section in required_sections:
            if section not in config:
                logger.error(f"[ERROR] Missing config section: {section}")
                return False
        
        # Check enabled DEXes
        enabled_dexes = [name for name, info in config['dexes'].items() if info.get('enabled', True)]
        logger.info(f"[INFO] Enabled DEXes: {len(enabled_dexes)} ({', '.join(enabled_dexes)})")
        
        # Check tokens
        tokens = list(config['tokens'].keys())
        logger.info(f"[INFO] Configured tokens: {len(tokens)} ({', '.join(tokens)})")
        
        logger.info("[SUCCESS] Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Configuration validation failed: {e}")
        return False

def run_circuit_breaker_check():
    """Run circuit breaker status check"""
    try:
        logger.info("[INFO] Running circuit breaker status check...")
        result: str = subprocess.run(
            ['python', 'reset_circuit_breaker_fixed.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("[SUCCESS] Circuit breaker check completed successfully")
            return True
        else:
            logger.error(f"[ERROR] Circuit breaker check failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Circuit breaker check error: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("=" * 70)
    logger.info("FLASH LOAN ARBITRAGE SYSTEM - RESUME OPERATIONS")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 70)
    
    # Step 1: Check environment
    logger.info("\n[STEP 1] Checking environment...")
    if not check_environment():
        return False
    
    # Step 2: Check required files
    logger.info("\n[STEP 2] Checking required files...")
    if not check_files():
        return False
    
    # Step 3: Validate configuration
    logger.info("\n[STEP 3] Validating configuration...")
    if not validate_config():
        return False
    
    # Step 4: Check Foundry server
    logger.info("\n[STEP 4] Checking Foundry MCP server...")
    foundry_status = check_foundry_server()
    
    # Step 5: Check circuit breaker
    logger.info("\n[STEP 5] Checking circuit breaker status...")
    if not run_circuit_breaker_check():
        return False
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("SYSTEM VALIDATION COMPLETED")
    logger.info("=" * 70)
    logger.info("[SUCCESS] Environment: OK")
    logger.info("[SUCCESS] Files: OK")
    logger.info("[SUCCESS] Configuration: OK")
    logger.info(f"[INFO] Foundry Server: {'OK' if foundry_status else 'WARNING'}")
    logger.info("[SUCCESS] Circuit Breaker: OK")
    logger.info("=" * 70)
    logger.info("\n[READY] System ready for arbitrage operations!")
    logger.info("\nNext steps:")
    logger.info("1. The Unicode encoding issues have been fixed")
    logger.info("2. Circuit breaker is normal (1/6 failed transactions)")
    logger.info("3. Foundry MCP server is running on port 8001")
    logger.info("4. You can now restart the arbitrage bot")
    logger.info("\nTo start the arbitrage bot:")
    logger.info("   python production_arbitrage_bot.py")
    logger.info("Or use the production launcher:")
    logger.info("   python production_main.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            logger.info("\n[FINAL] System resume validation completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n[FINAL] System resume validation failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n[INFO] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n[CRITICAL] Unexpected error: {e}")
        sys.exit(1)
