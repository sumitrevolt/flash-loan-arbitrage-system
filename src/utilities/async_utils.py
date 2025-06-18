"""
Async Utilities for Foundry MCP Server

Provides async helper functions for timeouts, concurrency control,
and async task management.
"""

import asyncio
import functools
from typing import Any, Awaitable, List, TypeVar, Callable, Optional

T = TypeVar('T')


async def run_with_timeout(coro: Awaitable[T], timeout: float) -> T:
    """
    Run an async coroutine with a timeout.
    
    Args:
        coro: The coroutine to run
        timeout: Timeout in seconds
        
    Returns:
        The result of the coroutine
        
    Raises:
        asyncio.TimeoutError: If the operation times out
    """
    return await asyncio.wait_for(coro, timeout=timeout)


async def gather_with_concurrency(
    *awaitables: Awaitable[T],
    max_concurrency: int = 10,
    return_exceptions: bool = False
) -> List[T]:
    """
    Gather multiple awaitables with limited concurrency.
    
    Args:
        *awaitables: The awaitables to execute
        max_concurrency: Maximum number of concurrent operations
        return_exceptions: Whether to return exceptions instead of raising
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def _run_with_semaphore(awaitable: Awaitable[T]) -> T:
        async with semaphore:
            return await awaitable
    
    wrapped_awaitables = [_run_with_semaphore(aw) for aw in awaitables]
    return await asyncio.gather(*wrapped_awaitables, return_exceptions=return_exceptions)


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for async functions to retry on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff_factor: Exponential backoff factor
        exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    
            raise last_exception
        return wrapper
    return decorator


async def run_in_executor(
    func: Callable,
    *args,
    executor: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    Run a synchronous function in an executor.
    
    Args:
        func: The synchronous function to run
        *args: Positional arguments for the function
        executor: Optional executor to use
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function
    """
    loop = asyncio.get_event_loop()
    
    if kwargs:
        # Create a partial function if we have keyword arguments
        partial_func = functools.partial(func, **kwargs)
        return await loop.run_in_executor(executor, partial_func, *args)
    else:
        return await loop.run_in_executor(executor, func, *args)


class AsyncLock:
    """Thread-safe async lock with timeout support."""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire the lock with optional timeout.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            True if lock was acquired, False if timeout
        """
        try:
            if timeout is None:
                await self._lock.acquire()
                return True
            else:
                await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
                return True
        except asyncio.TimeoutError:
            return False
    
    def release(self):
        """Release the lock."""
        self._lock.release()
    
    async def __aenter__(self):
        await self._lock.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()


class AsyncQueue:
    """Async queue with size limits and timeout support."""
    
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.Queue(maxsize=maxsize)
    
    async def put(self, item: T, timeout: Optional[float] = None) -> bool:
        """
        Put an item in the queue with optional timeout.
        
        Args:
            item: Item to put in queue
            timeout: Optional timeout in seconds
            
        Returns:
            True if item was added, False if timeout
        """
        try:
            if timeout is None:
                await self._queue.put(item)
                return True
            else:
                await asyncio.wait_for(self._queue.put(item), timeout=timeout)
                return True
        except asyncio.TimeoutError:
            return False
    
    async def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """
        Get an item from the queue with optional timeout.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Item from queue or None if timeout
        """
        try:
            if timeout is None:
                return await self._queue.get()
            else:
                return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    def qsize(self) -> int:
        """Get the current queue size."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()


async def safe_cancel_task(task: asyncio.Task, timeout: float = 5.0) -> bool:
    """
    Safely cancel an async task with timeout.
    
    Args:
        task: The task to cancel
        timeout: Timeout for cancellation
        
    Returns:
        True if task was cancelled successfully
    """
    if task.done():
        return True
    
    task.cancel()
    
    try:
        await asyncio.wait_for(task, timeout=timeout)
        return True
    except (asyncio.CancelledError, asyncio.TimeoutError):
        return True
    except Exception:
        return False


async def create_task_with_name(coro: Awaitable[T], name: str) -> asyncio.Task[T]:
    """
    Create a named task for better debugging.
    
    Args:
        coro: The coroutine to run
        name: Name for the task
        
    Returns:
        Named asyncio Task
    """
    task = asyncio.create_task(coro)
    task.set_name(name)
    return task