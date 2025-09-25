"""Hardware abstraction layer for AlignPress."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class HardwareInterface(ABC):
    """Define the contract for interacting with physical devices."""

    @abstractmethod
    def set_led(self, color: str) -> None:
        ...

    @abstractmethod
    def get_button_state(self) -> bool:
        ...


class MockHardware(HardwareInterface):
    """No-op hardware interface for development and tests."""

    def __init__(self) -> None:
        self.last_color = "#000000"
        self.button_pressed = False

    def set_led(self, color: str) -> None:
        self.last_color = color

    def get_button_state(self) -> bool:
        return self.button_pressed


class GPIOHardware(HardwareInterface):
    """GPIO-backed hardware implementation for Raspberry Pi."""

    def __init__(self, pin_map: Dict[str, int]) -> None:
        self._pin_map = pin_map

    def set_led(self, color: str) -> None:  # pragma: no cover - hardware integration
        # Placeholder for real GPIO code.
        del color

    def get_button_state(self) -> bool:  # pragma: no cover - hardware integration
        return False
