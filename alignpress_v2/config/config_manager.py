"""
Configuration Manager for AlignPress v2

Handles loading, saving, validation and migration of configuration
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .models import AlignPressConfig, create_default_config

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages unified configuration for AlignPress v2"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/alignpress_v2.json")
        self._config: Optional[AlignPressConfig] = None

    def load(self) -> AlignPressConfig:
        """Load configuration from file or create default"""
        if not self.config_path.exists():
            logger.info("No config file found, creating default")
            self._config = create_default_config()
            self.save(self._config)
            return self._config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle migration from old format if needed
            if 'schema_version' in data or 'version' not in data:
                logger.info("Migrating from old configuration format")
                data = self._migrate_from_v1(data)

            self._config = self._dict_to_config(data)
            logger.info(f"Loaded config version {self._config.version}")
            return self._config

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            logger.info("Creating default configuration")
            self._config = create_default_config()
            return self._config

    def save(self, config: AlignPressConfig) -> None:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = self._config_to_dict(config)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            self._config = config
            logger.info(f"Saved config to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def validate(self, config: AlignPressConfig) -> bool:
        """Validate configuration integrity"""
        try:
            # Check version
            if not config.version:
                return False

            # Check active references exist
            if config.session.active_platen_id:
                if not any(p.id == config.session.active_platen_id for p in config.library.platens):
                    return False

            if config.session.active_style_id:
                if not any(s.id == config.session.active_style_id for s in config.library.styles):
                    return False

            if config.session.active_variant_id:
                variant = next((v for v in config.library.variants
                              if v.id == config.session.active_variant_id), None)
                if not variant:
                    return False

                # Check variant references valid style
                if not any(s.id == variant.style_id for s in config.library.styles):
                    return False

            return True

        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False

    def _migrate_from_v1(self, old_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from old v1 configuration format"""
        logger.info("Migrating configuration from v1 to v2")

        # Create basic v2 structure
        migrated = {
            "version": "2.0.0",
            "system": {
                "language": old_data.get("language", "es"),
                "units": old_data.get("units", "mm"),
                "theme": old_data.get("theme", "light")
            },
            "hardware": {
                "camera": {
                    "device_id": 0,
                    "resolution": [1920, 1080],
                    "fps": 30
                },
                "gpio": {"enabled": False},
                "arduino": {"enabled": False}
            },
            "library": {
                "platens": [],
                "styles": [],
                "variants": []
            },
            "session": {
                "active_platen_id": old_data.get("active_platen_id"),
                "active_style_id": old_data.get("active_style_id"),
                "active_variant_id": old_data.get("active_variant_id")
            }
        }

        # Migrate calibration if exists
        if "calibration" in old_data:
            migrated["calibration"] = {
                "factor_mm_px": old_data["calibration"].get("mm_per_px", 1.0),
                "timestamp": old_data["calibration"].get("timestamp", datetime.now().isoformat()),
                "method": "migrated_from_v1"
            }

        logger.info("Migration completed")
        return migrated

    def _config_to_dict(self, config: AlignPressConfig) -> Dict[str, Any]:
        """Convert config object to dictionary for JSON serialization"""
        return {
            "version": config.version,
            "system": {
                "language": config.system.language,
                "units": config.system.units,
                "theme": config.system.theme
            },
            "calibration": {
                "factor_mm_px": config.calibration.factor_mm_px,
                "timestamp": config.calibration.timestamp.isoformat(),
                "method": config.calibration.method,
                "pattern_type": config.calibration.pattern_type,
                "pattern_size": list(config.calibration.pattern_size)
            } if config.calibration else None,
            "hardware": {
                "camera": {
                    "device_id": config.hardware.camera.device_id,
                    "resolution": list(config.hardware.camera.resolution),
                    "fps": config.hardware.camera.fps
                },
                "gpio": {
                    "enabled": config.hardware.gpio.enabled,
                    "led_pin": config.hardware.gpio.led_pin,
                    "button_pin": config.hardware.gpio.button_pin
                },
                "arduino": {
                    "enabled": config.hardware.arduino.enabled,
                    "port": config.hardware.arduino.port,
                    "baudrate": config.hardware.arduino.baudrate
                }
            },
            "library": {
                "platens": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "size_mm": list(p.size_mm)
                    } for p in config.library.platens
                ],
                "styles": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "logos": [
                            {
                                "id": l.id,
                                "name": l.name,
                                "position_mm": {"x": l.position_mm.x, "y": l.position_mm.y},
                                "tolerance_mm": l.tolerance_mm,
                                "detector_type": l.detector_type,
                                "roi": {
                                    "x": l.roi.x,
                                    "y": l.roi.y,
                                    "width": l.roi.width,
                                    "height": l.roi.height
                                },
                                "detector_params": l.detector_params,
                                "instructions": l.instructions
                            } for l in s.logos
                        ]
                    } for s in config.library.styles
                ],
                "variants": [
                    {
                        "id": v.id,
                        "style_id": v.style_id,
                        "size": v.size,
                        "scale_factor": v.scale_factor,
                        "offsets": {
                            logo_id: {"x": offset.x, "y": offset.y}
                            for logo_id, offset in v.offsets.items()
                        }
                    } for v in config.library.variants
                ]
            },
            "session": {
                "active_platen_id": config.session.active_platen_id,
                "active_style_id": config.session.active_style_id,
                "active_variant_id": config.session.active_variant_id,
                "operator_id": config.session.operator_id
            }
        }

    def _dict_to_config(self, data: Dict[str, Any]) -> AlignPressConfig:
        """Convert dictionary to config object"""
        from .models import (
            AlignPressConfig, SystemConfig, CalibrationData, HardwareConfig,
            CameraSettings, GPIOSettings, ArduinoSettings, LibraryData,
            Platen, Style, Logo, Point, Rectangle, Variant, SessionData
        )

        # Parse calibration
        calibration = None
        if data.get("calibration"):
            cal_data = data["calibration"]
            calibration = CalibrationData(
                factor_mm_px=cal_data["factor_mm_px"],
                timestamp=datetime.fromisoformat(cal_data["timestamp"]),
                method=cal_data["method"],
                pattern_type=cal_data.get("pattern_type", "chessboard"),
                pattern_size=tuple(cal_data.get("pattern_size", [7, 7]))
            )

        # Parse hardware
        hw_data = data.get("hardware", {})
        hardware = HardwareConfig(
            camera=CameraSettings(
                device_id=hw_data.get("camera", {}).get("device_id", 0),
                resolution=tuple(hw_data.get("camera", {}).get("resolution", [1920, 1080])),
                fps=hw_data.get("camera", {}).get("fps", 30)
            ),
            gpio=GPIOSettings(
                enabled=hw_data.get("gpio", {}).get("enabled", False),
                led_pin=hw_data.get("gpio", {}).get("led_pin", 18),
                button_pin=hw_data.get("gpio", {}).get("button_pin", 19)
            ),
            arduino=ArduinoSettings(
                enabled=hw_data.get("arduino", {}).get("enabled", False),
                port=hw_data.get("arduino", {}).get("port", "/dev/ttyUSB0"),
                baudrate=hw_data.get("arduino", {}).get("baudrate", 9600)
            )
        )

        # Parse library
        lib_data = data.get("library", {})

        platens = []
        for p_data in lib_data.get("platens", []):
            platens.append(Platen(
                id=p_data["id"],
                name=p_data["name"],
                size_mm=tuple(p_data["size_mm"])
            ))

        styles = []
        for s_data in lib_data.get("styles", []):
            logos = []
            for l_data in s_data.get("logos", []):
                logos.append(Logo(
                    id=l_data["id"],
                    name=l_data["name"],
                    position_mm=Point(
                        x=l_data["position_mm"]["x"],
                        y=l_data["position_mm"]["y"]
                    ),
                    tolerance_mm=l_data["tolerance_mm"],
                    detector_type=l_data["detector_type"],
                    roi=Rectangle(
                        x=l_data["roi"]["x"],
                        y=l_data["roi"]["y"],
                        width=l_data["roi"]["width"],
                        height=l_data["roi"]["height"]
                    ),
                    detector_params=l_data.get("detector_params", {}),
                    instructions=l_data.get("instructions")
                ))

            styles.append(Style(
                id=s_data["id"],
                name=s_data["name"],
                logos=logos
            ))

        variants = []
        for v_data in lib_data.get("variants", []):
            offsets = {}
            for logo_id, offset_data in v_data.get("offsets", {}).items():
                offsets[logo_id] = Point(
                    x=offset_data["x"],
                    y=offset_data["y"]
                )

            variants.append(Variant(
                id=v_data["id"],
                style_id=v_data["style_id"],
                size=v_data["size"],
                scale_factor=v_data.get("scale_factor", 1.0),
                offsets=offsets
            ))

        library = LibraryData(
            platens=platens,
            styles=styles,
            variants=variants
        )

        # Parse session
        session_data = data.get("session", {})
        session = SessionData(
            active_platen_id=session_data.get("active_platen_id"),
            active_style_id=session_data.get("active_style_id"),
            active_variant_id=session_data.get("active_variant_id"),
            operator_id=session_data.get("operator_id")
        )

        # Parse system
        sys_data = data.get("system", {})
        system = SystemConfig(
            language=sys_data.get("language", "es"),
            units=sys_data.get("units", "mm"),
            theme=sys_data.get("theme", "light")
        )

        return AlignPressConfig(
            version=data.get("version", "2.0.0"),
            system=system,
            calibration=calibration,
            hardware=hardware,
            library=library,
            session=session
        )