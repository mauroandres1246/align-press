"""Composition service wrapper."""
from __future__ import annotations

from alignpress_v2.domain.models import CompositionPreset


class CompositionService:
    """Generate presets from the design library."""

    def generate_preset(self, platen: str, style: str, variant: str) -> CompositionPreset:
        # Placeholder implementation to be replaced with legacy core integration.
        return CompositionPreset(platen=platen, style=style, variant=variant, offsets={})
