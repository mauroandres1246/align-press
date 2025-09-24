from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from alignpress.core.calibration import Calibration
from alignpress.core.presets import Preset
from alignpress.domain.platen import PlatenProfile
from alignpress.domain.style import LogoDefinition, StyleDefinition
from alignpress.domain.variant import LogoOverride, SizeVariant


@dataclass
class LogoTaskDefinition:
    logo_id: str
    display_name: str
    instructions: str | None
    preset: Preset


def _apply_override(logo: LogoDefinition, override: Optional[LogoOverride], variant_scale: float) -> Dict[str, object]:
    offset_x, offset_y = override.offset_mm if override else (0.0, 0.0)
    scale = variant_scale * (override.scale if override else 1.0)
    angle = logo.target_angle_deg + (override.angle_offset_deg if override else 0.0)
    tolerance_mm = override.tolerance_mm if override and override.tolerance_mm is not None else logo.tolerance_mm
    tolerance_deg = override.tolerance_deg if override and override.tolerance_deg is not None else logo.tolerance_deg
    center_mm = (
        logo.target_center_mm[0] + offset_x,
        logo.target_center_mm[1] + offset_y,
    )
    size_mm = (
        logo.target_size_mm[0] * scale,
        logo.target_size_mm[1] * scale,
    )
    roi_mm = (
        logo.roi_size_mm[0] * scale,
        logo.roi_size_mm[1] * scale,
    )
    return {
        "center_mm": center_mm,
        "size_mm": size_mm,
        "roi_mm": roi_mm,
        "angle_deg": angle,
        "tolerance_mm": tolerance_mm,
        "tolerance_deg": tolerance_deg,
    }


def _mm_to_px(values: Tuple[float, float], mm_per_px: float) -> Tuple[float, float]:
    return values[0] / mm_per_px, values[1] / mm_per_px


def compose_logo_presets(
    platen: PlatenProfile,
    style: StyleDefinition,
    variant: Optional[SizeVariant],
    calibration: Calibration,
) -> List[LogoTaskDefinition]:
    mm_per_px = calibration.mm_per_px
    overrides: Dict[str, LogoOverride] = {}
    variant_scale = 1.0
    if variant:
        variant_scale = variant.scale
        overrides = {item.logo_id: item for item in variant.logos}

    tasks: List[LogoTaskDefinition] = []
    for logo in style.logos:
        override = overrides.get(logo.logo_id)
        applied = _apply_override(logo, override, variant_scale)
        center_px = _mm_to_px(applied["center_mm"], mm_per_px)
        size_px = _mm_to_px(applied["size_mm"], mm_per_px)
        roi_px = _mm_to_px(applied["roi_mm"], mm_per_px)
        roi_x = int(round(center_px[0] - roi_px[0] / 2.0))
        roi_y = int(round(center_px[1] - roi_px[1] / 2.0))
        roi_w = max(10, int(round(roi_px[0])))
        roi_h = max(10, int(round(roi_px[1])))
        preset = Preset(
            name=f"{style.name}:{logo.logo_id}",
            roi=(roi_x, roi_y, roi_w, roi_h),
            target_center_px=center_px,
            target_angle_deg=applied["angle_deg"],
            target_size_px=size_px,
            tolerance_mm=applied["tolerance_mm"],
            tolerance_deg=applied["tolerance_deg"],
            detection_mode=logo.detector,
            params=logo.params,
        )
        tasks.append(
            LogoTaskDefinition(
                logo_id=logo.logo_id,
                display_name=logo.display_name,
                instructions=logo.instructions,
                preset=preset,
            )
        )
    return tasks
