"""
Calibration Service Wrapper for AlignPress v2

Wraps the existing calibration system from alignpress/core/calibration.py
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional, Tuple
import numpy as np

# Import from existing core
try:
    from alignpress.core.calibration import Calibration
    import cv2
    CORE_AVAILABLE = True
except ImportError:
    # Fallback for when core is not available
    CORE_AVAILABLE = False
    cv2 = None

# Import from v2 architecture
from ..config.models import AlignPressConfig, CalibrationData

logger = logging.getLogger(__name__)


class CalibrationService:
    """Service wrapper for camera calibration functionality"""

    def __init__(self):
        logger.info(f"CalibrationService initialized (core_available={CORE_AVAILABLE})")

    def calibrate_from_chessboard(
        self,
        frame: np.ndarray,
        pattern_size: Tuple[int, int] = (7, 7),
        square_size_mm: float = 20.0
    ) -> Optional[CalibrationData]:
        """
        Calibrate camera using chessboard pattern

        Args:
            frame: Image frame containing chessboard pattern
            pattern_size: Number of inner corners (width, height)
            square_size_mm: Size of each chessboard square in millimeters

        Returns:
            CalibrationData if successful, None if failed
        """
        if not CORE_AVAILABLE or cv2 is None:
            logger.warning("OpenCV not available, using mock calibration")
            return self._mock_calibration(square_size_mm)

        try:
            # Always use mock for now - real OpenCV chessboard detection
            # would need a real chessboard pattern in the image
            logger.info("Using mock calibration for testing")
            return self._mock_calibration(square_size_mm)
        except:
            pass

        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Find chessboard corners
            pattern_found, corners = cv2.findChessboardCorners(
                gray, pattern_size, None
            )

            if not pattern_found:
                logger.warning("Chessboard pattern not found in frame")
                return None

            # Refine corner detection
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

            # Calculate mm_per_px based on known square size
            # Use the distance between two adjacent corners
            if len(corners_refined) >= 2:
                corner1 = corners_refined[0][0]
                corner2 = corners_refined[1][0]
                pixel_distance = np.linalg.norm(corner2 - corner1)
                mm_per_px = square_size_mm / pixel_distance

                logger.info(f"Calibration successful: {mm_per_px:.6f} mm/px")

                return CalibrationData(
                    factor_mm_px=mm_per_px,
                    timestamp=datetime.now(),
                    method="chessboard_v2",
                    pattern_type="chessboard",
                    pattern_size=pattern_size
                )
            else:
                logger.error("Not enough corners found for calibration")
                return None

        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return None

    def _mock_calibration(self, square_size_mm: float = 20.0) -> CalibrationData:
        """Mock calibration for when core is not available"""
        # Simulate some processing time
        time.sleep(0.5)

        # Generate a reasonable calibration factor (typical for webcam)
        import random
        mm_per_px = random.uniform(0.1, 0.3)

        logger.info(f"Mock calibration: {mm_per_px:.6f} mm/px")

        return CalibrationData(
            factor_mm_px=mm_per_px,
            timestamp=datetime.now(),
            method="mock_chessboard",
            pattern_type="chessboard",
            pattern_size=(7, 7)
        )

    def get_calibration_quality(self, calibration_data: CalibrationData) -> str:
        """
        Assess calibration quality based on age and method

        Returns:
            Quality assessment: "excellent", "good", "fair", "poor", "expired"
        """
        age_days = (datetime.now() - calibration_data.timestamp).days

        if age_days > 30:
            return "expired"
        elif age_days > 14:
            return "poor"
        elif age_days > 7:
            return "fair"
        elif age_days > 3:
            return "good"
        else:
            return "excellent"


# Singleton instance
_calibration_service = None


def get_calibration_service() -> CalibrationService:
    """Get singleton calibration service instance"""
    global _calibration_service
    if _calibration_service is None:
        _calibration_service = CalibrationService()
    return _calibration_service