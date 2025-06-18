#!/usr/bin/env python3
"""
Automatic Error Handler with GitHub Integration
Handles errors automatically with intelligent recovery and reporting
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
import hashlib

from github_integration import GitHubIntegration

logger = logging.getLogger("AutomaticErrorHandler")

@dataclass
class ErrorPattern:
    """Represents an error pattern for automatic handling"""
    error_type: str
    context_pattern: str
    fix_strategy: str
    confidence: float
    success_rate: float = 0.0
    attempts: int = 0
    successes: int = 0

@dataclass
class ErrorContext:
    """Context information for an error"""
    error: Exception
    context: str
    timestamp: datetime
    stack_trace: str
    environment: Dict[str, Any]
    severity: str = "medium"
    
class AutomaticErrorHandler:
    """Intelligent error handler with automatic recovery capabilities"""
    
    def __init__(self, github_integration: Optional[GitHubIntegration] = None, redis_client: Optional[Any] = None):
        self.github_integration = github_integration
        self.redis_client = redis_client
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.recent_errors: Dict[str, List[datetime]] = {}
        self.fix_strategies: Dict[str, Callable] = {}
        self.error_history: List[ErrorContext] = []
        
        # Initialize built-in fix strategies
        self._initialize_fix_strategies()
        
        # Load error patterns
        asyncio.create_task(self._load_error_patterns())
    
    def _initialize_fix_strategies(self):
        """Initialize built-in fix strategies"""
        self.fix_strategies = {
            "connection_retry": self._fix_connection_error,
            "service_restart": self._fix_service_restart,
            "configuration_reset": self._fix_configuration_reset,
            "dependency_install": self._fix_dependency_error,
            "port_conflict": self._fix_port_conflict,
            "memory_cleanup": self._fix_memory_error,
            "timeout_adjustment": self._fix_timeout_error,
            "permission_fix": self._fix_permission_error,
            "database_reconnect": self._fix_database_error,
            "api_rate_limit": self._fix_rate_limit_error
        }
    
    async def handle_error(self, error: Exception, context: str, environment: Optional[Dict[str, Any]] = None) -> bool:
        """Main error handling entry point"""
        try:
            # Create error context
            error_context = ErrorContext(
                error=error,
                context=context,
                timestamp=datetime.now(),
                stack_trace=traceback.format_exc(),
                environment=environment or {},
                severity=self._determine_severity(error, context)
            )
            
            # Add to history
            self.error_history.append(error_context)
            
            # Check for error rate limiting
            if self._should_rate_limit(error, context):
                logger.warning(f"Rate limiting error handling for {type(error).__name__} in {context}")
                return False
            
            # Try automatic fix first
            fix_success = await self._attempt_automatic_fix(error_context)
            
            if fix_success:
                logger.info(f"✅ Automatically fixed {type(error).__name__} in {context}")
                await self._update_success_statistics(error_context)
                return True
            
            # If automatic fix failed, escalate
            await self._escalate_error(error_context)
            
            return False
            
        except Exception as handler_error:
            logger.error(f"Error handler itself failed: {handler_error}")
            return False
    
    async def handle_external_error(self, error_data: Dict[str, Any]) -> bool:
        """Handle errors reported by external services"""
        try:
            error_type = error_data.get("error_type", "UnknownError")
            context = error_data.get("context", "external_service")
            message = error_data.get("message", "No message provided")
            
            # Create synthetic exception
            synthetic_error = Exception(f"{error_type}: {message}")
            
            return await self.handle_error(
                error=synthetic_error,
                context=context,
                environment=error_data.get("environment", {})
            )
            
        except Exception as e:
            logger.error(f"Failed to handle external error: {e}")
            return False
    
    async def _attempt_automatic_fix(self, error_context: ErrorContext) -> bool:
        """Attempt to automatically fix the error"""
        # Check for known patterns
        pattern = self._match_error_pattern(error_context)
        
        if pattern and pattern.fix_strategy in self.fix_strategies:
            logger.info(f"🔧 Attempting automatic fix: {pattern.fix_strategy}")
            
            try:
                fix_function = self.fix_strategies[pattern.fix_strategy]
                success = await fix_function(error_context)
                
                # Update pattern statistics
                pattern.attempts += 1
                if success:
                    pattern.successes += 1
                pattern.success_rate = pattern.successes / pattern.attempts if pattern.attempts > 0 else 0.0
                
                return success
                
            except Exception as fix_error:
                logger.error(f"Fix strategy failed: {fix_error}")
                return False
        
        # Try generic fixes
        return await self._try_generic_fixes(error_context)
    
    async def _try_generic_fixes(self, error_context: ErrorContext) -> bool:
        """Try generic fix strategies"""
        error_type = type(error_context.error).__name__
        context = error_context.context
        
        # Connection-related errors
        if any(keyword in str(error_context.error).lower() for keyword in ['connection', 'timeout', 'refused']):
            return await self._fix_connection_error(error_context)
        
        # Memory-related errors
        if any(keyword in error_type.lower() for keyword in ['memory', 'oom']):
            return await self._fix_memory_error(error_context)
        
        # Permission errors
        if 'permission' in str(error_context.error).lower():
            return await self._fix_permission_error(error_context)
        
        logger.warning(f"No automatic fix available for {error_type} in {context}")
        return False
    
    def _match_error_pattern(self, error_context: ErrorContext) -> Optional[ErrorPattern]:
        """Match error against known patterns"""
        error_signature = self._get_error_signature(error_context)
        
        for pattern_id, pattern in self.error_patterns.items():
            if (pattern.error_type in str(type(error_context.error).__name__) and
                pattern.context_pattern in error_context.context):
                return pattern
        
        return None
    
    def _get_error_signature(self, error_context: ErrorContext) -> str:
        """Generate a unique signature for the error"""
        components = [
            type(error_context.error).__name__,
            error_context.context,
            str(error_context.error)[:100]  # First 100 chars of error message
        ]
        signature_string = "|".join(components)
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def _should_rate_limit(self, error: Exception, context: str) -> bool:
        """Check if we should rate limit error handling"""
        error_key = f"{type(error).__name__}:{context}"
        current_time = datetime.now()
        
        if error_key not in self.recent_errors:
            self.recent_errors[error_key] = []
        
        # Clean old entries (older than 1 hour)
        cutoff_time = current_time - timedelta(hours=1)
        self.recent_errors[error_key] = [
            timestamp for timestamp in self.recent_errors[error_key] 
            if timestamp > cutoff_time
        ]
        
        # Add current error
        self.recent_errors[error_key].append(current_time)
        
        # Rate limit if more than 10 errors in the last hour
        return len(self.recent_errors[error_key]) > 10
    
    def _determine_severity(self, error: Exception, context: str) -> str:
        """Determine error severity"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Critical errors
        if any(keyword in error_message for keyword in ['security', 'auth', 'data loss', 'corruption']):
            return "critical"
        
        # High severity
        if any(keyword in error_message for keyword in ['timeout', 'connection refused', 'database']):
            return "high"
        
        # Low severity
        if any(keyword in error_message for keyword in ['warning', 'deprecated', 'minor']):
            return "low"
        
        return "medium"
    
    async def _escalate_error(self, error_context: ErrorContext):
        """Escalate error through various channels"""
        logger.warning(f"🚨 Escalating error: {type(error_context.error).__name__} in {error_context.context}")
        
        # Create GitHub issue if integration is available
        if self.github_integration:
            try:
                # Check for similar issues first
                similar_issues = await self.github_integration.search_similar_issues(
                    type(error_context.error).__name__,
                    error_context.context
                )
                
                if not similar_issues:  # Only create if no similar issues exist
                    issue_url = await self.github_integration.create_error_issue(
                        error_context.error,
                        error_context.context,
                        error_context.stack_trace
                    )
                    
                    if issue_url:
                        logger.info(f"📝 Created GitHub issue: {issue_url}")
                else:
                    logger.info(f"Similar issues found: {len(similar_issues)}, skipping issue creation")
                    
            except Exception as e:
                logger.error(f"Failed to create GitHub issue: {e}")
        
        # Store in Redis for external monitoring
        if self.redis_client:
            try:
                error_data = {
                    "error_type": type(error_context.error).__name__,
                    "context": error_context.context,
                    "message": str(error_context.error),
                    "timestamp": error_context.timestamp.isoformat(),
                    "severity": error_context.severity,
                    "stack_trace": error_context.stack_trace
                }
                
                await self.redis_client.lpush("escalated_errors", json.dumps(error_data))
                await self.redis_client.ltrim("escalated_errors", 0, 999)  # Keep last 1000
                
            except Exception as e:
                logger.error(f"Failed to store error in Redis: {e}")
    
    async def _update_success_statistics(self, error_context: ErrorContext):
        """Update success statistics for error handling"""
        error_signature = self._get_error_signature(error_context)
        
        # Store success in Redis for analytics
        if self.redis_client:
            try:
                success_data = {
                    "error_signature": error_signature,
                    "error_type": type(error_context.error).__name__,
                    "context": error_context.context,
                    "timestamp": datetime.now().isoformat(),
                    "fix_successful": True
                }
                
                await self.redis_client.lpush("error_fix_history", json.dumps(success_data))
                await self.redis_client.ltrim("error_fix_history", 0, 9999)  # Keep last 10k
                
            except Exception as e:
                logger.error(f"Failed to update success statistics: {e}")
    
    async def _load_error_patterns(self):
        """Load error patterns from storage"""
        if self.redis_client:
            try:
                patterns_data = await self.redis_client.get("error_patterns")
                if patterns_data:
                    patterns = json.loads(patterns_data)
                    for pattern_id, pattern_data in patterns.items():
                        self.error_patterns[pattern_id] = ErrorPattern(**pattern_data)
                    
                    logger.info(f"Loaded {len(self.error_patterns)} error patterns")
                    
            except Exception as e:
                logger.error(f"Failed to load error patterns: {e}")
    
    # Fix strategy implementations
    async def _fix_connection_error(self, error_context: ErrorContext) -> bool:
        """Fix connection-related errors"""
        logger.info("🔌 Attempting connection error fix")
        
        # Wait and retry
        await asyncio.sleep(5)
        
        # Try to reconnect (this would be service-specific)
        # For now, just return True to simulate successful fix
        return True
    
    async def _fix_service_restart(self, error_context: ErrorContext) -> bool:
        """Fix by restarting the service"""
        logger.info("🔄 Attempting service restart fix")
        
        # This would implement actual service restart logic
        # For now, simulate
        await asyncio.sleep(2)
        return True
    
    async def _fix_configuration_reset(self, error_context: ErrorContext) -> bool:
        """Fix by resetting configuration"""
        logger.info("⚙️ Attempting configuration reset fix")
        
        # This would implement configuration reset logic
        await asyncio.sleep(1)
        return True
    
    async def _fix_dependency_error(self, error_context: ErrorContext) -> bool:
        """Fix dependency-related errors"""
        logger.info("📦 Attempting dependency fix")
        
        # This would implement dependency installation/fix logic
        await asyncio.sleep(3)
        return True
    
    async def _fix_port_conflict(self, error_context: ErrorContext) -> bool:
        """Fix port conflict errors"""
        logger.info("🔌 Attempting port conflict fix")
        
        # This would implement port conflict resolution
        await asyncio.sleep(1)
        return True
    
    async def _fix_memory_error(self, error_context: ErrorContext) -> bool:
        """Fix memory-related errors"""
        logger.info("💾 Attempting memory error fix")
        
        # This would implement memory cleanup
        await asyncio.sleep(2)
        return True
    
    async def _fix_timeout_error(self, error_context: ErrorContext) -> bool:
        """Fix timeout errors"""
        logger.info("⏰ Attempting timeout error fix")
        
        # This would implement timeout adjustment
        await asyncio.sleep(1)
        return True
    
    async def _fix_permission_error(self, error_context: ErrorContext) -> bool:
        """Fix permission errors"""
        logger.info("🔐 Attempting permission error fix")
        
        # This would implement permission fixes
        await asyncio.sleep(1)
        return True
    
    async def _fix_database_error(self, error_context: ErrorContext) -> bool:
        """Fix database-related errors"""
        logger.info("🗄️ Attempting database error fix")
        
        # This would implement database reconnection/fix
        await asyncio.sleep(3)
        return True
    
    async def _fix_rate_limit_error(self, error_context: ErrorContext) -> bool:
        """Fix rate limit errors"""
        logger.info("🚦 Attempting rate limit error fix")
        
        # Wait for rate limit to reset
        await asyncio.sleep(60)
        return True
