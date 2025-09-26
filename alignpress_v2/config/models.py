"""
Unified Configuration Models for AlignPress v2

All configuration in a single source of truth
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from pathlib import Path


@dataclass
class Point:
    """2D Point in millimeters"""
    x: float
    y: float


@dataclass
class Rectangle:
    """Rectangle defined by x, y, width, height"""
    x: float
    y: float
    width: float
    height: float


@dataclass
class CalibrationData:
    """Camera calibration data"""
    factor_mm_px: float
    timestamp: datetime
    method: str
    pattern_type: str = "chessboard"
    pattern_size: Tuple[int, int] = (7, 7)

    @property
    def is_expired(self) -> bool:
        """Check if calibration is older than 30 days"""
        return (datetime.now() - self.timestamp).days > 30

    @property
    def needs_reminder(self) -> bool:
        """Check if calibration needs reminder (7+ days)"""
        return (datetime.now() - self.timestamp).days > 7


@dataclass
class CameraSettings:
    """Camera hardware settings"""
    device_id: int = 0
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30


@dataclass
class GPIOSettings:
    """GPIO hardware settings"""
    enabled: bool = False
    led_pin: int = 18
    button_pin: int = 19


@dataclass
class ArduinoSettings:
    """Arduino hardware settings"""
    enabled: bool = False
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600


@dataclass
class HardwareConfig:
    """Hardware configuration"""
    camera: CameraSettings = field(default_factory=CameraSettings)
    gpio: GPIOSettings = field(default_factory=GPIOSettings)
    arduino: ArduinoSettings = field(default_factory=ArduinoSettings)


@dataclass
class SystemConfig:
    """System-wide settings"""
    language: str = "es"
    units: str = "mm"
    theme: str = "light"


@dataclass
class Logo:
    """Logo definition within a style"""
    id: str
    name: str
    position_mm: Point
    tolerance_mm: float
    detector_type: str  # "contour" or "aruco"
    roi: Rectangle
    detector_params: Dict[str, Any] = field(default_factory=dict)
    instructions: Optional[str] = None


@dataclass
class Platen:
    """Printing platen/bed definition"""
    id: str
    name: str
    size_mm: Tuple[float, float]  # width, height


@dataclass
class Style:
    """Style/design definition with logos"""
    id: str
    name: str
    logos: List[Logo] = field(default_factory=list)


@dataclass
class Variant:
    """Size variant with scaling and offsets"""
    id: str
    style_id: str
    size: str  # "XS", "S", "M", "L", "XL"
    scale_factor: float = 1.0
    offsets: Dict[str, Point] = field(default_factory=dict)  # logo_id -> offset


@dataclass
class LibraryData:
    """Library of reusable components"""
    platens: List[Platen] = field(default_factory=list)
    styles: List[Style] = field(default_factory=list)
    variants: List[Variant] = field(default_factory=list)


@dataclass
class SessionData:
    """Current working session state"""
    active_platen_id: Optional[str] = None
    active_style_id: Optional[str] = None
    active_variant_id: Optional[str] = None
    operator_id: Optional[str] = None


@dataclass
class AlignPressConfig:
    """Complete unified configuration"""
    version: str = "2.0.0"
    system: SystemConfig = field(default_factory=SystemConfig)
    calibration: Optional[CalibrationData] = None
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    library: LibraryData = field(default_factory=LibraryData)
    session: SessionData = field(default_factory=SessionData)

    def get_active_platen(self) -> Optional[Platen]:
        """Get currently active platen"""
        if not self.session.active_platen_id:
            return None
        return next((p for p in self.library.platens if p.id == self.session.active_platen_id), None)

    def get_active_style(self) -> Optional[Style]:
        """Get currently active style"""
        if not self.session.active_style_id:
            return None
        return next((s for s in self.library.styles if s.id == self.session.active_style_id), None)

    def get_active_variant(self) -> Optional[Variant]:
        """Get currently active variant"""
        if not self.session.active_variant_id:
            return None
        return next((v for v in self.library.variants if v.id == self.session.active_variant_id), None)

    @property
    def is_ready_for_detection(self) -> bool:
        """Check if all required components are selected"""
        return all([
            self.session.active_platen_id,
            self.session.active_style_id,
            self.calibration and not self.calibration.is_expired
        ])


def create_default_config() -> AlignPressConfig:
    """Create a default configuration for testing"""
    # Default platen
    default_platen = Platen(
        id="default_platen",
        name="Plancha 40x50cm",
        size_mm=(400, 500)
    )

    # Default style with two logos
    chest_logo = Logo(
        id="chest",
        name="Pecho",
        position_mm=Point(200, 150),
        tolerance_mm=2.0,
        detector_type="contour",
        roi=Rectangle(150, 100, 100, 100),
        instructions="Centrar logo en el pecho"
    )

    sleeve_logo = Logo(
        id="sleeve",
        name="Manga",
        position_mm=Point(350, 200),
        tolerance_mm=1.5,
        detector_type="aruco",
        roi=Rectangle(300, 150, 100, 100),
        detector_params={"aruco": {"expected_id": 42}},
        instructions="Alinear con costura de manga"
    )

    default_style = Style(
        id="basic_tshirt",
        name="Camiseta Básica",
        logos=[chest_logo, sleeve_logo]
    )

    # Default variants
    variant_m = Variant(
        id="tshirt_m",
        style_id="basic_tshirt",
        size="M",
        scale_factor=1.0
    )

    variant_l = Variant(
        id="tshirt_l",
        style_id="basic_tshirt",
        size="L",
        scale_factor=1.1,
        offsets={
            "chest": Point(0, 10),  # Move chest logo down 10mm
            "sleeve": Point(5, 5)   # Move sleeve logo slightly
        }
    )

    return AlignPressConfig(
        library=LibraryData(
            platens=[default_platen],
            styles=[default_style],
            variants=[variant_m, variant_l]
        ),
        session=SessionData(
            active_platen_id="default_platen",
            active_style_id="basic_tshirt",
            active_variant_id="tshirt_m"
        )
    )