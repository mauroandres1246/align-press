from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from alignpress.core.calibration import Calibration, load_calibration
from alignpress.domain.composition import LogoTaskDefinition, compose_logo_presets
from alignpress.domain.platen import PlatenProfile
from alignpress.domain.style import StyleDefinition
from alignpress.domain.variant import SizeVariant
from alignpress.io.config import AppConfig


def list_json_files(directory: Path) -> List[Path]:
    if not directory.exists():
        return []
    return sorted([p for p in directory.glob("*.json") if p.is_file()])


def load_platen(path: Path) -> PlatenProfile:
    return PlatenProfile.from_json(path)


def load_style(path: Path) -> StyleDefinition:
    return StyleDefinition.from_json(path)


def load_variant(path: Path) -> SizeVariant:
    return SizeVariant.from_json(path)


def _calibration_from_config(config: AppConfig, platen: PlatenProfile) -> Calibration:
    # Prefer explicit calibration file if provided, but fall back to platen profile values.
    if config.calibration_path and Path(config.calibration_path).exists():
        try:
            calibration = load_calibration(config.calibration_path)
        except Exception:
            calibration = None
        if calibration is not None:
            calibration.mm_per_px = platen.calibration.mm_per_px
            calibration.meta.update(
                {
                    "pattern_size": list(platen.calibration.pattern_size),
                    "square_size_mm": platen.calibration.square_size_mm,
                }
            )
            return calibration
    return Calibration(
        mm_per_px=platen.calibration.mm_per_px,
        method="profile",
        meta={
            "pattern_size": list(platen.calibration.pattern_size),
            "square_size_mm": platen.calibration.square_size_mm,
            "last_verified": platen.calibration.last_verified.isoformat() if platen.calibration.last_verified else None,
        },
    )


def build_logo_tasks(config: AppConfig) -> Tuple[PlatenProfile, StyleDefinition, SizeVariant | None, Calibration, List[LogoTaskDefinition]]:
    if config.assets is None or config.selection is None:
        raise ValueError("Config assets/selection not defined")
    platen = load_platen(config.selection.platen_path)
    style = load_style(config.selection.style_path)
    variant = None
    variant_path = config.selection.variant_path
    if variant_path and variant_path.exists():
        try:
            variant = load_variant(variant_path)
        except Exception:
            variant = None
    calibration = _calibration_from_config(config, platen)
    logo_tasks = compose_logo_presets(platen, style, variant, calibration)
    return platen, style, variant, calibration, logo_tasks
