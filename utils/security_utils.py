"""
Security Utilities for Flash Loan Arbitrage System
===============================================

Security utilities and safety mechanisms for protecting the system:
- Input validation and sanitization
- Rate limiting and access control
- Risk assessment and position limits
- Emergency stop mechanisms
- Audit logging
"""

import hashlib
import hmac
import time
import logging
import re
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: datetime
    source: str
    details: Dict[str, Any]

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.emergency_stop = False
        self.security_alerts: List[SecurityAlert] = []
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.max_failed_attempts = 5
        self.rate_limit_window = timedelta(minutes=1)
        self.max_requests_per_window = 60
    
    def validate_wallet_address(self, address: str) -> bool:
        """Validate Ethereum wallet address format"""
        if not address:
            return False
        
        # Remove '0x' prefix if present
        if address.startswith('0x'):
            address = address[2:]
        
        # Check if it's 40 hexadecimal characters
        if len(address) != 40:
            return False
        
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
    
    def validate_private_key(self, private_key: str) -> bool:
        """Validate private key format (without exposing it)"""
        if not private_key:
            return False
        
        # Remove '0x' prefix if present
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        
        # Check if it's 64 hexadecimal characters
        if len(private_key) != 64:
            return False
        
        try:
            int(private_key, 16)
            return True
        except ValueError:
            return False
    
    def sanitize_trade_amount(self, amount: float, max_amount: float) -> float:
        """Sanitize and validate trade amounts"""
        if not isinstance(amount, (int, float)):
            raise ValueError("Trade amount must be numeric")
        
        if amount <= 0:
            raise ValueError("Trade amount must be positive")
        
        if amount > max_amount:
            self.log_security_alert(
                severity="high",
                message=f"Trade amount {amount} exceeds maximum {max_amount}",
                source="trade_validation"
            )
            raise ValueError(f"Trade amount exceeds maximum allowed: {max_amount}")
        
        return float(amount)
    
    def validate_slippage_tolerance(self, slippage: float) -> bool:
        """Validate slippage tolerance is within reasonable bounds"""
        if not isinstance(slippage, (int, float)):
            return False
        
        # Slippage should be between 0.1% and 10%
        return 0.001 <= slippage <= 0.1
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limits"""
        now = datetime.now()
        
        # Initialize rate limit tracking for this identifier
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # Remove old requests outside the window
        cutoff_time = now - self.rate_limit_window
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier]
            if req_time > cutoff_time
        ]
        
        # Check if under rate limit
        if len(self.rate_limits[identifier]) >= self.max_requests_per_window:
            self.log_security_alert(
                severity="medium",
                message=f"Rate limit exceeded for {identifier}",
                source="rate_limiting"
            )
            return False
        
        # Add this request to the tracking
        self.rate_limits[identifier].append(now)
        return True
    
    def log_failed_attempt(self, identifier: str) -> bool:
        """Log failed attempt and check if should be blocked"""
        self.failed_attempts[identifier] = self.failed_attempts.get(identifier, 0) + 1
        
        if self.failed_attempts[identifier] >= self.max_failed_attempts:
            self.log_security_alert(
                severity="high",
                message=f"Too many failed attempts for {identifier}",
                source="authentication"
            )
            return True  # Should be blocked
        
        return False
    
    def reset_failed_attempts(self, identifier: str):
        """Reset failed attempts counter after successful operation"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def emergency_stop_system(self, reason: str):
        """Trigger emergency stop"""
        self.emergency_stop = True
        self.log_security_alert(
            severity="critical",
            message=f"Emergency stop triggered: {reason}",
            source="emergency_stop"
        )
        logger.critical(f"🚨 EMERGENCY STOP: {reason}")
    
    def check_emergency_stop(self) -> bool:
        """Check if system is in emergency stop state"""
        return self.emergency_stop
    
    def lift_emergency_stop(self, authorization_code: str) -> bool:
        """Lift emergency stop with proper authorization"""
        # In production, implement proper authorization mechanism
        if authorization_code == "EMERGENCY_LIFT_AUTHORIZED":
            self.emergency_stop = False
            self.log_security_alert(
                severity="high",
                message="Emergency stop lifted",
                source="emergency_stop"
            )
            logger.warning("🔓 Emergency stop lifted")
            return True
        return False
    
    def log_security_alert(self, severity: str, message: str, source: str, details: Optional[Dict] = None):
        """Log security alert"""
        alert = SecurityAlert(
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            source=source,
            details=details or {}
        )
        
        self.security_alerts.append(alert)
        
        # Log with appropriate level
        if severity == "critical":
            logger.critical(f"🚨 SECURITY ALERT: {message}")
        elif severity == "high":
            logger.error(f"⚠️ SECURITY WARNING: {message}")
        elif severity == "medium":
            logger.warning(f"⚠️ Security notice: {message}")
        else:
            logger.info(f"ℹ️ Security log: {message}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[SecurityAlert]:
        """Get security alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.security_alerts
            if alert.timestamp > cutoff_time
        ]
    
    def assess_trade_risk(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk level of a trade"""
        risk_score = 0.0
        risk_factors = []
        
        # Check trade size
        trade_size = trade_data.get('amount_usd', 0)
        if trade_size > 50000:
            risk_score += 0.3
            risk_factors.append("Large trade size")
        
        # Check profit margin
        profit_margin = trade_data.get('profit_percentage', 0)
        if profit_margin > 5.0:  # >5% profit might be too good to be true
            risk_score += 0.2
            risk_factors.append("Unusually high profit margin")
        
        # Check gas costs
        gas_cost_usd = trade_data.get('gas_cost_usd', 0)
        if gas_cost_usd > trade_size * 0.1:  # Gas costs >10% of trade
            risk_score += 0.2
            risk_factors.append("High gas costs")
        
        # Check liquidity
        liquidity = trade_data.get('liquidity_usd', 0)
        if liquidity < trade_size * 2:  # Liquidity less than 2x trade size
            risk_score += 0.3
            risk_factors.append("Low liquidity")
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': 'block' if risk_score >= 0.8 else 'allow'
        }

# Global security manager instance
security_manager = SecurityManager()

def rate_limited(identifier_func: Callable = None):
    """Decorator for rate limiting function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = f"{func.__name__}_{id(args)}"
            
            # Check rate limit
            if not security_manager.check_rate_limit(identifier):
                raise Exception(f"Rate limit exceeded for {identifier}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def emergency_stop_check(func):
    """Decorator to check emergency stop before executing critical functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if security_manager.check_emergency_stop():
            raise Exception("System is in emergency stop mode")
        return func(*args, **kwargs)
    return wrapper

def risk_assessment_required(func):
    """Decorator to require risk assessment for trading functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract trade data from arguments (simplified)
        trade_data = kwargs.get('trade_data', {})
        if not trade_data and args:
            trade_data = args[0] if isinstance(args[0], dict) else {}
        
        # Perform risk assessment
        risk_assessment = security_manager.assess_trade_risk(trade_data)
        
        if risk_assessment['recommendation'] == 'block':
            security_manager.log_security_alert(
                severity="high",
                message=f"Trade blocked by risk assessment: {risk_assessment['risk_factors']}",
                source="risk_assessment",
                details=risk_assessment
            )
            raise Exception(f"Trade blocked: {risk_assessment['risk_factors']}")
        
        return await func(*args, **kwargs)
    return wrapper

def validate_input(**validations):
    """Decorator for input validation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate keyword arguments
            for param_name, validator in validations.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid {param_name}: {value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Validation functions
def is_valid_address(address: str) -> bool:
    """Validate Ethereum address"""
    return security_manager.validate_wallet_address(address)

def is_positive_number(value: Any) -> bool:
    """Check if value is a positive number"""
    try:
        return float(value) > 0
    except (ValueError, TypeError):
        return False

def is_valid_percentage(value: Any) -> bool:
    """Check if value is a valid percentage (0-100)"""
    try:
        num = float(value)
        return 0 <= num <= 100
    except (ValueError, TypeError):
        return False

def is_reasonable_gas_price(value: Any) -> bool:
    """Check if gas price is reasonable (1-1000 gwei)"""
    try:
        gwei = float(value)
        return 1 <= gwei <= 1000
    except (ValueError, TypeError):
        return False

# Audit logging
class AuditLogger:
    """Audit logging for security-sensitive operations"""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        self.logger = logging.getLogger("audit")
        
        # Setup file handler
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_trade_attempt(self, user_id: str, trade_data: Dict[str, Any]):
        """Log trade attempt"""
        self.logger.info(f"TRADE_ATTEMPT - User: {user_id} - Data: {json.dumps(trade_data, default=str)}")
    
    def log_config_change(self, user_id: str, config_key: str, old_value: Any, new_value: Any):
        """Log configuration changes"""
        self.logger.warning(f"CONFIG_CHANGE - User: {user_id} - Key: {config_key} - Old: {old_value} - New: {new_value}")
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        self.logger.error(f"SECURITY_EVENT - Type: {event_type} - Details: {json.dumps(details, default=str)}")

# Global audit logger
audit_logger = AuditLogger()

def audit_log(event_type: str):
    """Decorator for audit logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log function call
            audit_logger.logger.info(f"{event_type} - Function: {func.__name__} - Args: {str(args)[:100]}")
            
            try:
                result = func(*args, **kwargs)
                audit_logger.logger.info(f"{event_type}_SUCCESS - Function: {func.__name__}")
                return result
            except Exception as e:
                audit_logger.logger.error(f"{event_type}_FAILED - Function: {func.__name__} - Error: {str(e)}")
                raise
        return wrapper
    return decorator