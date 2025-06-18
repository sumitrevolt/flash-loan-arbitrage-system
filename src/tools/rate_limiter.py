"""
Rate limiter utility for RPC requests.

This module provides a rate limiter to prevent hitting rate limits on RPC providers.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
import functools

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter for RPC requests to prevent hitting rate limits.
    """
    
    def __init__(self, 
                 requests_per_second: float = 5.0, 
                 burst_limit: int = 10,
                 cooldown_period: float = 1.0):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_second: Maximum number of requests per second.
            burst_limit: Maximum number of requests that can be made in a burst.
            cooldown_period: Cooldown period in seconds after hitting a rate limit.
        """
        self.requests_per_second = requests_per_second
        self.burst_limit = burst_limit
        self.cooldown_period = cooldown_period
        
        # Token bucket algorithm state
        self.tokens = burst_limit
        self.last_refill_time = time.time()
        
        # Rate limit detection
        self.rate_limit_keywords = [
            "rate limit", 
            "too many requests", 
            "call rate limit", 
            "throttle", 
            "exceeded", 
            "retry",
            "too many concurrent requests",
            "request limit"
        ]
        self.rate_limited_until = 0
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        Acquire a token from the bucket. If no tokens are available, wait until one is available.
        
        Returns:
            True if a token was acquired, False if in cooldown period.
        """
        async with self.lock:
            # Check if we're in a cooldown period
            if time.time() < self.rate_limited_until:
                wait_time = self.rate_limited_until - time.time()
                logger.warning(f"In rate limit cooldown period. Waiting {wait_time:.1f} seconds.")
                return False
            
            # Refill tokens based on time elapsed
            now = time.time()
            elapsed = now - self.last_refill_time
            self.tokens = min(self.burst_limit, self.tokens + elapsed * self.requests_per_second)
            self.last_refill_time = now
            
            # If we have tokens, consume one
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            # No tokens available, need to wait
            wait_time = (1 - self.tokens) / self.requests_per_second
            logger.debug(f"Rate limit approaching. Waiting {wait_time:.3f} seconds before next request.")
            await asyncio.sleep(wait_time)
            self.tokens = 0
            self.last_refill_time = time.time()
            return True
    
    def handle_error(self, error: Exception) -> bool:
        """
        Handle an error response and check if it's a rate limit error.
        
        Args:
            error: The exception that was raised.
            
        Returns:
            True if it's a rate limit error, False otherwise.
        """
        error_str = str(error).lower()
        
        # Check if the error message contains any rate limit keywords
        is_rate_limit = any(keyword.lower() in error_str for keyword in self.rate_limit_keywords)
        
        if is_rate_limit:
            # Extract cooldown time if available
            cooldown_time = self.cooldown_period
            
            # Try to extract a specific cooldown time from the error message
            import re
            retry_match = re.search(r'retry in (\d+)m(\d+)s', error_str)
            if retry_match:
                minutes = int(retry_match.group(1))
                seconds = int(retry_match.group(2))
                cooldown_time = minutes * 60 + seconds
            
            # Set the rate limit cooldown
            self.rate_limited_until = time.time() + cooldown_time
            logger.warning(f"Rate limit detected. Cooling down for {cooldown_time:.1f} seconds.")
            return True
        
        return False

# Global rate limiter instance
global_rate_limiter = RateLimiter()

def rate_limited(func):
    """
    Decorator to apply rate limiting to a function.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        limiter = global_rate_limiter
        
        # Try to acquire a token
        if not await limiter.acquire():
            # In cooldown period, wait and try again
            cooldown_wait = limiter.rate_limited_until - time.time()
            logger.warning(f"Rate limited. Waiting {cooldown_wait:.1f} seconds before retrying.")
            await asyncio.sleep(cooldown_wait)
        
        try:
            # Execute the function
            return await func(*args, **kwargs)
        except Exception as e:
            # Check if it's a rate limit error
            if limiter.handle_error(e):
                # Wait for the cooldown period
                cooldown_wait = limiter.rate_limited_until - time.time()
                logger.warning(f"Rate limited during execution. Waiting {cooldown_wait:.1f} seconds before retrying.")
                await asyncio.sleep(cooldown_wait)
                
                # Retry once after cooldown
                return await func(*args, **kwargs)
            else:
                # Not a rate limit error, re-raise
                raise
    
    return wrapper
