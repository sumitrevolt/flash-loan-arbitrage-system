"""
Event System for Foundry MCP Server

Simple in-memory event system for bi-directional communication
between the MCP server and existing flash loan system components.
"""

import asyncio
import logging
from typing import Any, Dict, List, Callable, Optional
from collections import defaultdict

from ..utils.async_utils import AsyncQueue, safe_cancel_task


class EventSystem:
    """
    Simple event system for pub/sub communication.
    
    Provides event publishing, subscription, and async event handling
    for integration with the existing flash loan system.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize event system.
        
        Args:
            config: Server configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Event handling
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_queue = AsyncQueue(maxsize=1000)
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # Event statistics
        self._events_published = 0
        self._events_processed = 0
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 100
        
        # Configuration
        self.enabled = config.get("integration", {}).get("event_bus", {}).get("enabled", True)
        self.channel_prefix = config.get("integration", {}).get("event_bus", {}).get("channel_prefix", "foundry_mcp")
    
    async def initialize(self) -> bool:
        """
        Initialize the event system.
        
        Returns:
            True if initialization successful
        """
        try:
            if not self.enabled:
                self.logger.info("Event system disabled in configuration")
                return True
            
            self.logger.info("Initializing event system...")
            
            # Start event processing worker
            self._running = True
            self._worker_task = asyncio.create_task(self._event_worker())
            self._worker_task.set_name("event_system_worker")
            
            self.logger.info("Event system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize event system: {e}", exc_info=True)
            return False
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Publish an event to the system.
        
        Args:
            event_type: Type of event (e.g., "tool.executed", "compilation.completed")
            data: Event data payload
            
        Returns:
            True if event was published successfully
        """
        if not self.enabled or not self._running:
            return False
        
        try:
            event = {
                "type": event_type,
                "timestamp": asyncio.get_event_loop().time(),
                "channel": f"{self.channel_prefix}.{event_type}",
                "data": data,
                "id": f"{event_type}_{self._events_published}"
            }
            
            # Add to queue for processing
            success = await self._event_queue.put(event, timeout=1.0)
            
            if success:
                self._events_published += 1
                self.logger.debug(f"Published event: {event_type}")
                return True
            else:
                self.logger.warning(f"Event queue full, dropped event: {event_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing event {event_type}: {e}")
            return False
    
    def subscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type to subscribe to (supports wildcards with *)
            callback: Async callback function to handle events
            
        Returns:
            True if subscription successful
        """
        try:
            if not self.enabled:
                return False
            
            self._subscribers[event_type].append(callback)
            self.logger.debug(f"Added subscriber for event type: {event_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing to {event_type}: {e}")
            return False
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type to unsubscribe from
            callback: Callback function to remove
            
        Returns:
            True if unsubscription successful
        """
        try:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    self.logger.debug(f"Removed subscriber for event type: {event_type}")
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from {event_type}: {e}")
            return False
    
    async def _event_worker(self) -> None:
        """Background worker to process events."""
        self.logger.info("Event worker started")
        
        while self._running:
            try:
                # Get event from queue
                event = await self._event_queue.get(timeout=1.0)
                
                if event is None:
                    continue
                
                # Process the event
                await self._process_event(event)
                self._events_processed += 1
                
                # Add to history
                self._add_to_history(event)
                
            except Exception as e:
                self.logger.error(f"Error in event worker: {e}", exc_info=True)
                await asyncio.sleep(0.1)  # Brief pause on error
        
        self.logger.info("Event worker stopped")
    
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a single event by notifying subscribers."""
        event_type = event["type"]
        
        # Find matching subscribers
        matching_subscribers = []
        
        for pattern, subscribers in self._subscribers.items():
            if self._matches_pattern(event_type, pattern):
                matching_subscribers.extend(subscribers)
        
        # Notify subscribers
        if matching_subscribers:
            self.logger.debug(f"Notifying {len(matching_subscribers)} subscribers for {event_type}")
            
            # Run callbacks concurrently
            tasks = []
            for callback in matching_subscribers:
                task = asyncio.create_task(self._safe_callback(callback, event))
                tasks.append(task)
            
            # Wait for all callbacks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches a subscription pattern."""
        if pattern == "*":
            return True
        
        if "*" not in pattern:
            return event_type == pattern
        
        # Simple wildcard matching
        pattern_parts = pattern.split("*")
        
        if len(pattern_parts) == 2:
            prefix, suffix = pattern_parts
            return event_type.startswith(prefix) and event_type.endswith(suffix)
        
        # For now, only support single wildcard
        return event_type == pattern
    
    async def _safe_callback(self, callback: Callable, event: Dict[str, Any]) -> None:
        """Safely execute a callback with error handling."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            self.logger.error(f"Error in event callback: {e}", exc_info=True)
    
    def _add_to_history(self, event: Dict[str, Any]) -> None:
        """Add event to history for debugging."""
        self._event_history.append({
            "type": event["type"],
            "timestamp": event["timestamp"],
            "channel": event["channel"],
            "id": event["id"]
        })
        
        # Trim history
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event system statistics."""
        return {
            "enabled": self.enabled,
            "running": self._running,
            "events_published": self._events_published,
            "events_processed": self._events_processed,
            "queue_size": self._event_queue.qsize(),
            "subscribers_count": sum(len(subs) for subs in self._subscribers.values()),
            "subscription_patterns": list(self._subscribers.keys()),
            "recent_events": self._event_history[-10:]  # Last 10 events
        }
    
    async def shutdown(self) -> None:
        """Shutdown the event system."""
        try:
            self.logger.info("Shutting down event system...")
            self._running = False
            
            # Cancel worker task
            if self._worker_task:
                await safe_cancel_task(self._worker_task)
            
            # Clear subscribers
            self._subscribers.clear()
            
            self.logger.info("Event system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during event system shutdown: {e}", exc_info=True)


# Helper functions for common events
async def publish_tool_executed(event_system: EventSystem, tool_name: str, result: Dict[str, Any]) -> None:
    """Publish a tool execution event."""
    await event_system.publish("tool.executed", {
        "tool_name": tool_name,
        "success": result.get("success", False),
        "result": result
    })


async def publish_compilation_completed(event_system: EventSystem, success: bool, details: Dict[str, Any]) -> None:
    """Publish a compilation completion event."""
    await event_system.publish("compilation.completed", {
        "success": success,
        "details": details
    })


async def publish_server_status(event_system: EventSystem, status: str, details: Dict[str, Any]) -> None:
    """Publish a server status event."""
    await event_system.publish("server.status", {
        "status": status,
        "details": details
    })