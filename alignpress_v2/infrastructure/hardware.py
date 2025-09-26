"""
Hardware Abstraction Layer for AlignPress v2

Provides abstraction for different hardware interfaces
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class LEDColor(Enum):
    """LED color states"""
    OFF = "off"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    WHITE = "white"


class HardwareInterface(ABC):
    """Abstract base class for hardware interfaces"""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize hardware. Returns True if successful."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean shutdown of hardware"""
        pass

    @abstractmethod
    def set_led(self, color: LEDColor) -> bool:
        """Set LED color. Returns True if successful."""
        pass

    @abstractmethod
    def get_button_state(self) -> bool:
        """Get button state. Returns True if pressed."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if hardware is connected"""
        pass


class MockHardware(HardwareInterface):
    """Mock hardware implementation for development/testing"""

    def __init__(self):
        self._connected = False
        self._led_color = LEDColor.OFF
        self._button_pressed = False
        logger.info("MockHardware created")

    def initialize(self) -> bool:
        """Initialize mock hardware"""
        logger.info("Initializing mock hardware")
        self._connected = True
        return True

    def shutdown(self) -> None:
        """Shutdown mock hardware"""
        logger.info("Shutting down mock hardware")
        self._connected = False
        self._led_color = LEDColor.OFF

    def set_led(self, color: LEDColor) -> bool:
        """Set mock LED color"""
        if not self._connected:
            return False

        self._led_color = color
        logger.debug(f"Mock LED set to {color.value}")
        return True

    def get_button_state(self) -> bool:
        """Get mock button state"""
        # Simulate occasional button presses for testing
        import random
        if random.random() < 0.01:  # 1% chance per call
            self._button_pressed = not self._button_pressed

        return self._button_pressed

    def is_connected(self) -> bool:
        """Check mock connection status"""
        return self._connected


class HardwareManager:
    """Manages hardware interfaces for the application"""

    def __init__(self):
        self._interfaces: Dict[str, HardwareInterface] = {}
        self._active_interface: Optional[HardwareInterface] = None
        logger.info("HardwareManager created")

    def register_interface(self, name: str, interface: HardwareInterface) -> None:
        """Register a hardware interface"""
        self._interfaces[name] = interface
        logger.info(f"Registered hardware interface: {name}")

    def initialize_interface(self, name: str) -> bool:
        """Initialize and activate a hardware interface"""
        if name not in self._interfaces:
            logger.error(f"Hardware interface not found: {name}")
            return False

        interface = self._interfaces[name]

        if interface.initialize():
            self._active_interface = interface
            logger.info(f"Activated hardware interface: {name}")
            return True
        else:
            logger.error(f"Failed to initialize hardware interface: {name}")
            return False

    def shutdown(self) -> None:
        """Shutdown all hardware interfaces"""
        logger.info("Shutting down all hardware interfaces")

        for name, interface in self._interfaces.items():
            try:
                if interface.is_connected():
                    interface.shutdown()
                    logger.info(f"Shutdown interface: {name}")
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")

        self._active_interface = None

    def set_led(self, color: LEDColor) -> bool:
        """Set LED using active interface"""
        if self._active_interface:
            return self._active_interface.set_led(color)
        return False

    def get_button_state(self) -> bool:
        """Get button state using active interface"""
        if self._active_interface:
            return self._active_interface.get_button_state()
        return False

    def is_connected(self) -> bool:
        """Check if active interface is connected"""
        if self._active_interface:
            return self._active_interface.is_connected()
        return False


# Global hardware manager instance
_hardware_manager = None


def get_hardware_manager() -> HardwareManager:
    """Get global hardware manager instance"""
    global _hardware_manager
    if _hardware_manager is None:
        _hardware_manager = HardwareManager()
        # Register mock interface by default
        _hardware_manager.register_interface("mock", MockHardware())

    return _hardware_manager