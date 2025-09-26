"""
State Manager for AlignPress v2

Centralized state management with event notifications
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from ..config.models import AlignPressConfig
from .event_bus import get_event_bus, EventType, ModeChangedData

logger = logging.getLogger(__name__)


class AppMode(Enum):
    """Application operating modes"""
    IDLE = "idle"
    DETECTING = "detecting"
    CALIBRATING = "calibrating"
    CONFIGURING = "configuring"


@dataclass
class DetectionResult:
    """Result of a logo detection"""
    logo_id: str
    success: bool
    position: tuple[float, float]  # x, y in pixels
    angle: float  # degrees
    confidence: float  # 0.0 to 1.0
    error_mm: float
    error_deg: float
    timestamp: float


@dataclass
class HardwareStatus:
    """Hardware component status"""
    camera_connected: bool = False
    gpio_enabled: bool = False
    arduino_connected: bool = False
    last_error: Optional[str] = None


class AppState:
    """Central application state"""

    def __init__(self, config: AlignPressConfig):
        self.config = config
        self.mode = AppMode.IDLE
        self.current_logo_index = 0
        self.detection_results: List[DetectionResult] = []
        self.hardware_status = HardwareStatus()
        self.errors: List[str] = []

        # UI state
        self.ui_visible = True
        self.fullscreen = False
        self.paused = False

    @property
    def current_logos(self) -> List[Any]:
        """Get current logo list from active style"""
        style = self.config.get_active_style()
        return style.logos if style else []

    @property
    def current_logo(self) -> Optional[Any]:
        """Get currently selected logo"""
        logos = self.current_logos
        if 0 <= self.current_logo_index < len(logos):
            return logos[self.current_logo_index]
        return None

    @property
    def is_ready_for_detection(self) -> bool:
        """Check if system is ready to start detection"""
        return (
            self.config.is_ready_for_detection and
            self.hardware_status.camera_connected and
            self.mode == AppMode.IDLE
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary for debugging"""
        return {
            "mode": self.mode.value,
            "current_logo_index": self.current_logo_index,
            "detection_results_count": len(self.detection_results),
            "hardware_status": {
                "camera_connected": self.hardware_status.camera_connected,
                "gpio_enabled": self.hardware_status.gpio_enabled,
                "arduino_connected": self.hardware_status.arduino_connected,
                "last_error": self.hardware_status.last_error
            },
            "ui_state": {
                "visible": self.ui_visible,
                "fullscreen": self.fullscreen,
                "paused": self.paused
            },
            "ready_for_detection": self.is_ready_for_detection,
            "active_platen": self.config.session.active_platen_id,
            "active_style": self.config.session.active_style_id,
            "active_variant": self.config.session.active_variant_id
        }


class StateManager:
    """Manages application state with event notifications"""

    def __init__(self, initial_config: AlignPressConfig):
        self._state = AppState(initial_config)
        self._event_bus = get_event_bus()
        logger.info("StateManager initialized")

    @property
    def state(self) -> AppState:
        """Get current application state (read-only access)"""
        return self._state

    def update_config(self, new_config: AlignPressConfig) -> None:
        """Update configuration and notify listeners"""
        old_config = self._state.config
        self._state.config = new_config

        # Reset logo index if style changed
        old_style_id = old_config.session.active_style_id
        new_style_id = new_config.session.active_style_id
        if old_style_id != new_style_id:
            self._state.current_logo_index = 0

        self._event_bus.emit(
            EventType.CONFIG_CHANGED,
            {"old_config": old_config, "new_config": new_config},
            source="StateManager"
        )
        logger.info(f"Config updated, style: {new_style_id}")

    def set_mode(self, new_mode: AppMode) -> None:
        """Change application mode"""
        if new_mode == self._state.mode:
            return

        old_mode = self._state.mode
        self._state.mode = new_mode

        self._event_bus.emit(
            EventType.MODE_CHANGED,
            ModeChangedData(old_mode=old_mode.value, new_mode=new_mode.value),
            source="StateManager"
        )
        logger.info(f"Mode changed: {old_mode.value} -> {new_mode.value}")

    def select_logo(self, logo_index: int) -> bool:
        """Select a logo by index"""
        logos = self._state.current_logos
        if not (0 <= logo_index < len(logos)):
            logger.warning(f"Invalid logo index: {logo_index}")
            return False

        self._state.current_logo_index = logo_index
        logo = logos[logo_index]

        self._event_bus.emit(
            EventType.LOGO_SELECTED,
            {"logo_id": logo.id, "style_id": self._state.config.session.active_style_id},
            source="StateManager"
        )
        logger.info(f"Selected logo: {logo.id}")
        return True

    def add_detection_result(self, result: DetectionResult) -> None:
        """Add a new detection result"""
        self._state.detection_results.append(result)

        self._event_bus.emit(
            EventType.DETECTION_RESULT,
            {
                "logo_id": result.logo_id,
                "success": result.success,
                "position": result.position,
                "angle": result.angle,
                "confidence": result.confidence,
                "error_mm": result.error_mm,
                "error_deg": result.error_deg
            },
            source="StateManager"
        )

        logger.debug(f"Detection result added for {result.logo_id}: {'success' if result.success else 'failed'}")

    def update_hardware_status(self, **kwargs) -> None:
        """Update hardware status"""
        updated = False

        for key, value in kwargs.items():
            if hasattr(self._state.hardware_status, key):
                old_value = getattr(self._state.hardware_status, key)
                if old_value != value:
                    setattr(self._state.hardware_status, key, value)
                    updated = True
                    logger.debug(f"Hardware status updated: {key} = {value}")

        if updated:
            self._event_bus.emit(
                EventType.HARDWARE_STATUS_CHANGED,
                self._state.hardware_status,
                source="StateManager"
            )

    def add_error(self, message: str, component: str = "unknown") -> None:
        """Add an error message"""
        self._state.errors.append(message)
        self._state.hardware_status.last_error = message

        self._event_bus.emit(
            EventType.ERROR_OCCURRED,
            {"message": message, "component": component},
            source="StateManager"
        )
        logger.error(f"Error added from {component}: {message}")

    def clear_results(self) -> None:
        """Clear all detection results"""
        self._state.detection_results.clear()
        logger.info("Detection results cleared")

    def set_ui_state(self, **kwargs) -> None:
        """Update UI state flags"""
        for key, value in kwargs.items():
            if key == "visible":
                self._state.ui_visible = value
            elif key == "fullscreen":
                self._state.fullscreen = value
            elif key == "paused":
                self._state.paused = value

        logger.debug(f"UI state updated: {kwargs}")

    def get_state_summary(self) -> str:
        """Get human-readable state summary"""
        state_dict = self._state.to_dict()
        return f"Mode: {state_dict['mode']}, Logo: {self._state.current_logo_index + 1}/{len(self._state.current_logos)}, Ready: {state_dict['ready_for_detection']}"