"""
App Controller for AlignPress v2

Main controller that orchestrates the entire application
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..config.config_manager import ConfigManager
from ..config.models import AlignPressConfig
from .state_manager import StateManager, AppMode, DetectionResult
from .event_bus import get_event_bus, EventType, Event

logger = logging.getLogger(__name__)


class AppController:
    """Main application controller - orchestrates all services and state"""

    def __init__(self, config_path: Optional[Path] = None):
        logger.info("Initializing AppController")

        # Initialize configuration
        self.config_manager = ConfigManager(config_path)
        initial_config = self.config_manager.load()

        # Initialize state management
        self.state_manager = StateManager(initial_config)

        # Initialize event bus and subscribe to events
        self.event_bus = get_event_bus()
        self._setup_event_handlers()

        logger.info("AppController initialized successfully")

    @property
    def config(self) -> AlignPressConfig:
        """Get current configuration"""
        return self.state_manager.state.config

    @property
    def state(self):
        """Get current application state"""
        return self.state_manager.state

    def _setup_event_handlers(self):
        """Setup event handlers for controller"""
        # Subscribe to all events for logging
        self.event_bus.subscribe_all(self._log_event)

        # Subscribe to specific events
        self.event_bus.subscribe(EventType.CONFIG_CHANGED, self._on_config_changed)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._on_error_occurred)

    def _log_event(self, event: Event):
        """Log all events for debugging"""
        logger.debug(f"Event: {event.type.value} from {event.source}")

    def _on_config_changed(self, event: Event):
        """Handle configuration changes"""
        logger.info("Configuration changed, saving to file")
        try:
            self.config_manager.save(event.data["new_config"])
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            self.state_manager.add_error(f"Failed to save config: {e}", "AppController")

    def _on_error_occurred(self, event: Event):
        """Handle application errors"""
        error_data = event.data
        logger.error(f"Application error in {error_data['component']}: {error_data['message']}")

    # Configuration Management

    def update_platen(self, platen_id: str) -> bool:
        """Update active platen"""
        config = self.config
        if not any(p.id == platen_id for p in config.library.platens):
            self.state_manager.add_error(f"Platen not found: {platen_id}", "AppController")
            return False

        config.session.active_platen_id = platen_id
        self.state_manager.update_config(config)
        return True

    def update_style(self, style_id: str) -> bool:
        """Update active style"""
        config = self.config
        if not any(s.id == style_id for s in config.library.styles):
            self.state_manager.add_error(f"Style not found: {style_id}", "AppController")
            return False

        config.session.active_style_id = style_id
        # Reset variant if it doesn't match the new style
        if config.session.active_variant_id:
            variant = config.get_active_variant()
            if variant and variant.style_id != style_id:
                config.session.active_variant_id = None

        self.state_manager.update_config(config)
        return True

    def update_variant(self, variant_id: Optional[str]) -> bool:
        """Update active variant"""
        config = self.config
        if variant_id and not any(v.id == variant_id for v in config.library.variants):
            self.state_manager.add_error(f"Variant not found: {variant_id}", "AppController")
            return False

        # Verify variant matches active style
        if variant_id:
            variant = next((v for v in config.library.variants if v.id == variant_id), None)
            if variant and variant.style_id != config.session.active_style_id:
                self.state_manager.add_error("Variant doesn't match active style", "AppController")
                return False

        config.session.active_variant_id = variant_id
        self.state_manager.update_config(config)
        return True

    # Detection Management

    def start_detection(self) -> bool:
        """Start logo detection process"""
        if not self.state.is_ready_for_detection:
            self.state_manager.add_error("System not ready for detection", "AppController")
            return False

        try:
            self.state_manager.set_mode(AppMode.DETECTING)
            self.state_manager.clear_results()

            # Start detection for current logo
            logo = self.state.current_logo
            if logo:
                logger.info(f"Starting detection for logo: {logo.id}")
                self.event_bus.emit(EventType.DETECTION_STARTED, {"logo_id": logo.id}, "AppController")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to start detection: {e}")
            self.state_manager.add_error(f"Detection start failed: {e}", "AppController")
            self.state_manager.set_mode(AppMode.IDLE)
            return False

    def stop_detection(self) -> None:
        """Stop logo detection process"""
        logger.info("Stopping detection")
        self.state_manager.set_mode(AppMode.IDLE)
        self.event_bus.emit(EventType.DETECTION_STOPPED, None, "AppController")

    def select_logo(self, logo_index: int) -> bool:
        """Select a logo for detection"""
        return self.state_manager.select_logo(logo_index)

    # Hardware Management

    def initialize_hardware(self) -> bool:
        """Initialize hardware components"""
        try:
            logger.info("Initializing hardware")
            # Mock hardware initialization
            self.state_manager.update_hardware_status(camera_connected=True)

            if self.config.hardware.gpio.enabled:
                self.state_manager.update_hardware_status(gpio_enabled=True)

            return True

        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            self.state_manager.add_error(f"Hardware init failed: {e}", "AppController")
            return False

    def startup(self) -> bool:
        """Complete application startup sequence"""
        logger.info("Starting up AlignPress v2")

        try:
            if not self.initialize_hardware():
                logger.warning("Hardware initialization failed, continuing anyway")

            if not self.config_manager.validate(self.config):
                logger.warning("Configuration validation failed")

            self.event_bus.emit(EventType.CONFIG_LOADED, self.config, "AppController")
            logger.info("AlignPress v2 startup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            self.state_manager.add_error(f"Startup failed: {e}", "AppController")
            return False

    def shutdown(self) -> None:
        """Clean shutdown of the application"""
        logger.info("Shutting down AlignPress v2")
        try:
            if self.state.mode == AppMode.DETECTING:
                self.stop_detection()
            self.config_manager.save(self.config)
            logger.info("AlignPress v2 shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")