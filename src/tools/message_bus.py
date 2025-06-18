"""
Message bus module for Flash Loan System.
Handles event publishing and subscription across the system.
"""

import logging
import asyncio
from typing import Dict, Any, Callable, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

class MessageBus:
    """
    Message bus for system-wide event communication.
    Implements singleton pattern for system-wide access.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger(self.__class__.__name__)
        self.subscribers = defaultdict(set)
        self._initialized = True

    async def initialize(self) -> bool:
        """Initialize the message bus."""
        try:
            self.logger.info("Initializing message bus...")
            self.logger.info("Message bus initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing message bus: {e}")
            return False

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        self.subscribers[event_type].add(callback)
        self.logger.debug(f"Added subscriber for event type: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(callback)
            self.logger.debug(f"Removed subscriber for event type: {event_type}")

    def publish(self, event_type: str, data: Dict[str, Any] | None = None):
        """Publish an event."""
        self.logger.info(f"Publishing event: {event_type} with data: {data}")

        if event_type not in self.subscribers:
            self.logger.warning(f"No subscribers for event type: {event_type}")
            return

        subscriber_count = len(self.subscribers[event_type])
        self.logger.info(f"Found {subscriber_count} subscribers for event type: {event_type}")

        for callback in self.subscribers[event_type]:
            try:
                self.logger.debug(f"Calling subscriber callback: {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")
                if asyncio.iscoroutinefunction(callback):
                    self.logger.debug(f"Creating async task for coroutine callback")
                    asyncio.create_task(callback(data))
                else:
                    self.logger.debug(f"Calling synchronous callback directly")
                    callback(data)
            except Exception as e:
                self.logger.error(f"Error in subscriber callback for event {event_type}: {e}", exc_info=True)

    def get_subscriber_count(self, event_type: str | None = None) -> Dict[str, int]:
        """Get count of subscribers for each event type."""
        if event_type:
            return {event_type: len(self.subscribers.get(event_type, set()))}
        return {k: len(v) for k, v in self.subscribers.items()}

    def clear_subscribers(self, event_type: str | None = None):
        """Clear all subscribers for an event type or all events."""
        if event_type:
            self.subscribers[event_type].clear()
        else:
            self.subscribers.clear()
        self.logger.debug(f"Cleared subscribers for event type: {event_type if event_type else 'all'}")

# Create singleton instance
message_bus = MessageBus()



