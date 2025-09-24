import numpy as np
import pytest

from alignpress.core.calibration import Calibration
from alignpress.core.presets import Preset
from alignpress.core.geometry import Pose2D
from alignpress.core.alignment import LogoAligner
from alignpress.domain.composition import compose_logo_presets
from alignpress.domain.platen import CalibrationProfile, PlatenProfile
from alignpress.domain.style import LogoDefinition, StyleDefinition
from alignpress.domain.variant import LogoOverride, SizeVariant


@pytest.mark.parametrize("mm_per_px", [0.1, 0.25, 0.75])
def test_compose_logo_presets_rounds_int_sizes(mm_per_px):
    platen = PlatenProfile(
        name="Plancha",
        size_mm=(400.0, 500.0),
        calibration=CalibrationProfile(mm_per_px=mm_per_px, pattern_size=(7, 5), square_size_mm=25.0),
    )
    style = StyleDefinition(
        name="Estilo",
        version="1.0",
        logos=[
            LogoDefinition(
                logo_id="logo",
                display_name="Logo",
                detector="contour",
                params={"threshold": "otsu"},
                target_center_mm=(200.0, 150.0),
                target_size_mm=(90.2, 60.6),
                roi_size_mm=(201.3, 199.9),
                target_angle_deg=0.0,
                tolerance_mm=3.0,
                tolerance_deg=2.0,
            )
        ],
    )
    calibration = Calibration(mm_per_px=mm_per_px, method="profile", meta={})
    tasks = compose_logo_presets(platen, style, None, calibration)
    preset = tasks[0].preset
    assert isinstance(preset.target_size_px[0], int)
    assert isinstance(preset.target_size_px[1], int)
    assert preset.target_size_px[0] >= 1 and preset.target_size_px[1] >= 1
    x, y, w, h = preset.roi
    assert all(isinstance(v, int) for v in (x, y, w, h))
    assert w >= 10 and h >= 10


def test_compose_variant_style_mismatch_raises():
    platen = PlatenProfile(
        name="Plancha",
        size_mm=(400.0, 500.0),
        calibration=CalibrationProfile(mm_per_px=0.5, pattern_size=(7, 5), square_size_mm=25.0),
    )
    style = StyleDefinition(
        name="Estilo",
        version="1.0",
        logos=[
            LogoDefinition(
                logo_id="logo",
                display_name="Logo",
                detector="contour",
                params={},
                target_center_mm=(200.0, 150.0),
                target_size_mm=(100.0, 80.0),
                roi_size_mm=(200.0, 200.0),
                target_angle_deg=0.0,
                tolerance_mm=3.0,
                tolerance_deg=2.0,
            )
        ],
    )
    variant = SizeVariant(name="Talla X", style_name="Otro", logos=[])
    calibration = Calibration(mm_per_px=0.5, method="profile", meta={})
    with pytest.raises(ValueError):
        compose_logo_presets(platen, style, variant, calibration)


def test_logoaligner_clamps_roi():
    preset = Preset(
        name="test",
        roi=(-50, -30, 500, 500),
        target_center_px=(10.0, 10.0),
        target_angle_deg=0.0,
        target_size_px=(50, 40),
        tolerance_mm=3.0,
        tolerance_deg=2.0,
        detection_mode="contour",
        params={},
    )
    calibration = Calibration(mm_per_px=0.5, method="const", meta={})
    captured = []

    def fake_detector(frame, roi, params):
        captured.append(roi)
        return None

    aligner = LogoAligner(preset, calibration, detectors={"contour": fake_detector})
    frame = np.zeros((100, 120, 3), dtype=np.uint8)
    aligner.process_frame(frame, timestamp=0.0, frame_id="frame")
    assert captured, "Detector should have been called"
    x, y, w, h = captured[0]
    assert x >= 0 and y >= 0
    assert x + w <= frame.shape[1]
    assert y + h <= frame.shape[0]


def test_calibration_from_dict_rejects_non_positive():
    with pytest.raises(ValueError):
        Calibration.from_dict({"mm_per_px": 0.0, "method": "test", "meta": {}})
