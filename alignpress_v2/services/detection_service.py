"""
Detection Service Wrapper for AlignPress v2

Wraps the existing detection system from alignpress/core/alignment.py
"""
from __future__ import annotations

import logging
import time
from typing import Optional, Dict, Any
import numpy as np

# Import from existing core
try:
    from alignpress.core.alignment import _DETECTORS, DetectionOutcome
    from alignpress.core.geometry import Pose2D, AlignmentEvaluation, evaluate_alignment
    from alignpress.core.presets import Preset
    from alignpress.core.calibration import Calibration
    CORE_AVAILABLE = True
except ImportError:
    # Fallback for when core is not available
    CORE_AVAILABLE = False

# Import from v2 architecture
from ..config.models import Logo, AlignPressConfig
from ..controller.state_manager import DetectionResult

logger = logging.getLogger(__name__)


class DetectionService:
    """Service wrapper for logo detection functionality"""

    def __init__(self):
        if not CORE_AVAILABLE:
            logger.warning("AlignPress core not available, using mock detection")
            self._detectors = {"contour": self._mock_detector, "aruco": self._mock_detector}
        else:
            self._detectors = _DETECTORS.copy()

        logger.info("DetectionService initialized")

    def detect_logo(
        self,
        frame: np.ndarray,
        logo: Logo,
        config: AlignPressConfig
    ) -> DetectionResult:
        """
        Detect a single logo in the given frame

        Args:
            frame: Image frame (BGR format)
            logo: Logo configuration from v2 models
            config: Full application configuration

        Returns:
            DetectionResult with detection outcome
        """
        start_time = time.time()

        try:
            if CORE_AVAILABLE:
                return self._detect_with_core(frame, logo, config, start_time)
            else:
                return self._mock_detection(logo, start_time)

        except Exception as e:
            logger.error(f"Detection failed for logo {logo.id}: {e}")
            return DetectionResult(
                logo_id=logo.id,
                success=False,
                position=(0.0, 0.0),
                angle=0.0,
                confidence=0.0,
                error_mm=999.9,
                error_deg=999.9,
                timestamp=start_time
            )

    def _detect_with_core(self, frame: np.ndarray, logo: Logo, config: AlignPressConfig, start_time: float) -> DetectionResult:
        """Real detection using alignpress core"""
        # Convert v2 logo to v1 preset format
        preset = self._logo_to_preset(logo, config)

        # Perform detection using existing core
        detection_outcome = self._detect_with_preset(frame, preset)

        # Evaluate alignment if detection succeeded
        evaluation = None
        if detection_outcome.pose:
            target_pose = Pose2D(
                center=preset.target_center_px,
                angle_deg=preset.target_angle_deg,
                size=preset.target_size_px
            )

            # Get calibration factor
            calibration_factor = config.calibration.factor_mm_px if config.calibration else 1.0

            evaluation = evaluate_alignment(
                target_pose=target_pose,
                detected_pose=detection_outcome.pose,
                tolerance_mm=preset.tolerance_mm,
                tolerance_deg=preset.tolerance_deg,
                calibration=Calibration(
                    mm_per_px=calibration_factor,
                    method="v2_wrapper",
                    meta={}
                )
            )

        # Convert to v2 DetectionResult
        return self._create_detection_result(
            logo_id=logo.id,
            detection_outcome=detection_outcome,
            evaluation=evaluation,
            timestamp=start_time
        )

    def _mock_detection(self, logo: Logo, start_time: float) -> DetectionResult:
        """Mock detection for when core is not available"""
        # Simulate some processing time
        time.sleep(0.01)

        # Mock a successful detection with some randomness
        import random
        success = random.random() > 0.3  # 70% success rate

        if success:
            # Mock detected position near target
            target_x, target_y = logo.position_mm.x, logo.position_mm.y
            detected_x = target_x + random.uniform(-5, 5)
            detected_y = target_y + random.uniform(-5, 5)
            error_mm = ((detected_x - target_x)**2 + (detected_y - target_y)**2)**0.5

            return DetectionResult(
                logo_id=logo.id,
                success=error_mm <= logo.tolerance_mm,
                position=(detected_x, detected_y),
                angle=random.uniform(-2, 2),
                confidence=random.uniform(0.6, 0.9),
                error_mm=error_mm,
                error_deg=abs(random.uniform(-1, 1)),
                timestamp=start_time
            )
        else:
            return DetectionResult(
                logo_id=logo.id,
                success=False,
                position=(0.0, 0.0),
                angle=0.0,
                confidence=0.0,
                error_mm=999.9,
                error_deg=999.9,
                timestamp=start_time
            )

    def _logo_to_preset(self, logo: Logo, config: AlignPressConfig) -> 'Preset':
        """Convert v2 Logo to v1 Preset format"""
        # Get calibration factor
        calibration_factor = config.calibration.factor_mm_px if config.calibration else 1.0

        # Convert position from mm to pixels
        center_px = (
            logo.position_mm.x / calibration_factor,
            logo.position_mm.y / calibration_factor
        )

        # Convert ROI from mm to pixels
        roi_px = (
            int(logo.roi.x / calibration_factor),
            int(logo.roi.y / calibration_factor),
            int(logo.roi.width / calibration_factor),
            int(logo.roi.height / calibration_factor)
        )

        # Default size (will be updated by detection)
        size_px = (50, 50)

        return Preset(
            name=f"v2_{logo.id}",
            roi=roi_px,
            target_center_px=center_px,
            target_angle_deg=0.0,
            target_size_px=size_px,
            tolerance_mm=logo.tolerance_mm,
            tolerance_deg=5.0,
            detection_mode=logo.detector_type,
            params=logo.detector_params
        )

    def _detect_with_preset(self, frame: np.ndarray, preset: 'Preset') -> 'DetectionOutcome':
        """Perform detection using existing core detectors"""
        detector_fn = self._detectors.get(preset.detection_mode)

        if not detector_fn:
            logger.error(f"Unknown detection mode: {preset.detection_mode}")
            return DetectionOutcome(pose=None, method=None)

        try:
            # Call the detector
            pose = detector_fn(frame, preset.roi, preset.params)

            return DetectionOutcome(
                pose=pose,
                method=preset.detection_mode
            )

        except Exception as e:
            logger.error(f"Detector {preset.detection_mode} failed: {e}")
            return DetectionOutcome(pose=None, method=preset.detection_mode)

    def _create_detection_result(
        self,
        logo_id: str,
        detection_outcome: 'DetectionOutcome',
        evaluation: Optional['AlignmentEvaluation'],
        timestamp: float
    ) -> DetectionResult:
        """Create v2 DetectionResult from v1 detection data"""

        if not detection_outcome.pose:
            return DetectionResult(
                logo_id=logo_id,
                success=False,
                position=(0.0, 0.0),
                angle=0.0,
                confidence=0.0,
                error_mm=999.9,
                error_deg=999.9,
                timestamp=timestamp
            )

        pose = detection_outcome.pose

        # Calculate confidence (simplified)
        confidence = 0.8 if evaluation and evaluation.within_tolerance else 0.3

        # Get error from evaluation
        error_mm = evaluation.distance_mm if evaluation else 999.9
        error_deg = evaluation.angle_diff_deg if evaluation else 999.9

        return DetectionResult(
            logo_id=logo_id,
            success=evaluation.within_tolerance if evaluation else False,
            position=(pose.center[0], pose.center[1]),
            angle=pose.angle_deg,
            confidence=confidence,
            error_mm=error_mm,
            error_deg=abs(error_deg),
            timestamp=timestamp
        )

    def _mock_detector(self, frame: np.ndarray, roi: tuple, params: dict) -> Optional['Pose2D']:
        """Mock detector for fallback"""
        # Simulate detection
        import random
        if random.random() > 0.3:
            x, y, w, h = roi
            center_x = x + w/2 + random.uniform(-10, 10)
            center_y = y + h/2 + random.uniform(-10, 10)

            # Create mock Pose2D-like object if core not available
            if not CORE_AVAILABLE:
                class MockPose2D:
                    def __init__(self, center, angle_deg, size):
                        self.center = center
                        self.angle_deg = angle_deg
                        self.size = size

                return MockPose2D(
                    center=(center_x, center_y),
                    angle_deg=random.uniform(-5, 5),
                    size=(w*0.8, h*0.8)
                )
            else:
                return Pose2D(
                    center=(center_x, center_y),
                    angle_deg=random.uniform(-5, 5),
                    size=(w*0.8, h*0.8)
                )
        return None

    def get_available_detectors(self) -> list[str]:
        """Get list of available detector types"""
        return list(self._detectors.keys())

    def is_detector_available(self, detector_type: str) -> bool:
        """Check if a detector type is available"""
        return detector_type in self._detectors


# Singleton instance
_detection_service = None


def get_detection_service() -> DetectionService:
    """Get singleton detection service instance"""
    global _detection_service
    if _detection_service is None:
        _detection_service = DetectionService()
    return _detection_service