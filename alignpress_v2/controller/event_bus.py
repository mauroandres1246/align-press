"""
Event Bus for AlignPress v2

Simple typed event system for decoupled communication
"""
from __future__ import annotations

import logging
from typing import Dict, List, Callable, Any, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
from abc import ABC

logger = logging.getLogger(__name__)

EventData = TypeVar('EventData')


class EventType(Enum):
    """Typed events for the application"""
    # Configuration events
    CONFIG_LOADED = "config_loaded"
    CONFIG_CHANGED = "config_changed"

    # Detection events
    DETECTION_STARTED = "detection_started"
    DETECTION_RESULT = "detection_result"
    DETECTION_STOPPED = "detection_stopped"

    # UI events
    LOGO_SELECTED = "logo_selected"
    CALIBRATION_REQUESTED = "calibration_requested"

    # Hardware events
    HARDWARE_STATUS_CHANGED = "hardware_status_changed"
    CAMERA_CONNECTED = "camera_connected"
    CAMERA_DISCONNECTED = "camera_disconnected"

    # System events
    ERROR_OCCURRED = "error_occurred"
    MODE_CHANGED = "mode_changed"


@dataclass
class Event(Generic[EventData]):
    """Generic event with typed data"""
    type: EventType
    data: EventData
    source: str = "unknown"


class EventHandler(ABC):
    """Base class for event handlers"""
    pass


EventCallback = Callable[[Event], None]


class EventBus:
    """Simple event bus for decoupled communication"""

    def __init__(self):
        self._handlers: Dict[EventType, List[EventCallback]] = {}
        self._global_handlers: List[EventCallback] = []

    def subscribe(self, event_type: EventType, callback: EventCallback) -> None:
        """Subscribe to specific event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value}")

    def subscribe_all(self, callback: EventCallback) -> None:
        """Subscribe to all events"""
        self._global_handlers.append(callback)
        logger.debug("Subscribed to all events")

    def unsubscribe(self, event_type: EventType, callback: EventCallback) -> None:
        """Unsubscribe from specific event type"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type.value}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type.value}")

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers"""
        logger.debug(f"Publishing {event.type.value} from {event.source}")

        # Call specific handlers
        specific_handlers = self._handlers.get(event.type, [])
        for handler in specific_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.type.value}: {e}")

        # Call global handlers
        for handler in self._global_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in global event handler for {event.type.value}: {e}")

    def emit(self, event_type: EventType, data: Any = None, source: str = "unknown") -> None:
        """Convenience method to create and publish event"""
        event = Event(type=event_type, data=data, source=source)
        self.publish(event)


# Global event bus instance (singleton pattern)
_event_bus = None


def get_event_bus() -> EventBus:
    """Get global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Event data types for type safety

@dataclass
class ConfigChangedData:
    """Data for CONFIG_CHANGED event"""
    old_config: Any
    new_config: Any


@dataclass
class DetectionResultData:
    """Data for DETECTION_RESULT event"""
    logo_id: str
    success: bool
    position: tuple
    angle: float
    confidence: float
    error_mm: float
    error_deg: float


@dataclass
class ErrorData:
    """Data for ERROR_OCCURRED event"""
    message: str
    exception: Exception = None
    component: str = "unknown"


@dataclass
class ModeChangedData:
    """Data for MODE_CHANGED event"""
    old_mode: str
    new_mode: str


@dataclass
class LogoSelectedData:
    """Data for LOGO_SELECTED event"""
    logo_id: str
    style_id: str