"""
Composition Service Wrapper for AlignPress v2

Wraps the existing composition system from alignpress/domain/composition.py
"""
from __future__ import annotations

import logging
from typing import List

# Import from existing core
try:
    from alignpress.domain.composition import compose_logo_presets
    CORE_AVAILABLE = True
except ImportError:
    # Fallback for when core is not available
    CORE_AVAILABLE = False

# Import from v2 architecture
from ..config.models import AlignPressConfig

logger = logging.getLogger(__name__)


class CompositionService:
    """Service wrapper for preset composition functionality"""

    def __init__(self):
        logger.info(f"CompositionService initialized (core_available={CORE_AVAILABLE})")

    def compose_presets(self, config: AlignPressConfig) -> List[dict]:
        """
        Compose logo presets from current configuration

        Args:
            config: Full application configuration

        Returns:
            List of composed preset dictionaries ready for detection
        """
        try:
            if CORE_AVAILABLE:
                return self._compose_with_core(config)
            else:
                return self._mock_compose_presets(config)

        except Exception as e:
            logger.error(f"Preset composition failed: {e}")
            return []

    def _compose_with_core(self, config: AlignPressConfig) -> List[dict]:
        """Compose presets using the existing core system"""
        # This would integrate with the real core composition system
        # For now, fall back to mock
        return self._mock_compose_presets(config)

    def _mock_compose_presets(self, config: AlignPressConfig) -> List[dict]:
        """Mock preset composition for when core is not available"""
        style = config.get_active_style()
        if not style:
            return []

        presets = []
        for logo in style.logos:
            preset = {
                "logo_id": logo.id,
                "display_name": logo.name,
                "instructions": logo.instructions,
                "target_position_mm": (logo.position_mm.x, logo.position_mm.y),
                "tolerance_mm": logo.tolerance_mm,
                "detector_type": logo.detector_type,
                "detector_params": logo.detector_params,
                "roi": {
                    "x": logo.roi.x,
                    "y": logo.roi.y,
                    "width": logo.roi.width,
                    "height": logo.roi.height
                }
            }
            presets.append(preset)

        logger.info(f"Mock composed {len(presets)} presets")
        return presets

    def validate_composition(self, config: AlignPressConfig) -> bool:
        """Validate that composition is possible"""
        return (config.get_active_platen() is not None and
                config.get_active_style() is not None and
                config.calibration is not None and
                not config.calibration.is_expired)


# Singleton instance
_composition_service = None


def get_composition_service() -> CompositionService:
    """Get singleton composition service instance"""
    global _composition_service
    if _composition_service is None:
        _composition_service = CompositionService()
    return _composition_service