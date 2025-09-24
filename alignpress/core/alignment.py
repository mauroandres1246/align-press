from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

import numpy as np

from alignpress.core.calibration import Calibration
from alignpress.core.geometry import AlignmentEvaluation, Pose2D, evaluate_alignment
from alignpress.core.presets import Preset
from alignpress.detection.aruco_detector import detect_logo_aruco
from alignpress.detection.contour_detector import detect_logo_contour

DetectorFn = Callable[[np.ndarray, Tuple[int, int, int, int], Dict[str, object]], Optional[Pose2D]]

_DETECTORS: Dict[str, DetectorFn] = {
    "contour": detect_logo_contour,
    "aruco": detect_logo_aruco,
}


@dataclass
class DetectionOutcome:
    pose: Optional[Pose2D]
    method: Optional[str]


@dataclass
class FrameAnalysis:
    frame_id: str
    timestamp: float
    detection: DetectionOutcome
    evaluation: AlignmentEvaluation

    def to_record(self) -> Dict[str, object]:
        record: Dict[str, object] = {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "status": self.evaluation.status,
            "within_tolerance": self.evaluation.within_tolerance,
            "detection_method": self.detection.method,
        }
        if self.detection.pose:
            record.update(
                {
                    "cx_px": float(self.detection.pose.center[0]),
                    "cy_px": float(self.detection.pose.center[1]),
                    "angle_deg": float(self.detection.pose.angle_deg),
                    "width_px": float(self.detection.pose.size[0]),
                    "height_px": float(self.detection.pose.size[1]),
                }
            )
        if self.evaluation.metrics:
            record.update(
                {
                    "dx_mm": float(self.evaluation.metrics.dx_mm),
                    "dy_mm": float(self.evaluation.metrics.dy_mm),
                    "dtheta_deg": float(self.evaluation.metrics.dtheta_deg),
                }
            )
        else:
            record.update({"dx_mm": None, "dy_mm": None, "dtheta_deg": None})
        return record


class LogoAligner:
    def __init__(self, preset: Preset, calibration: Calibration, detectors: Optional[Dict[str, DetectorFn]] = None) -> None:
        self.preset = preset
        self.calibration = calibration
        self.detectors = detectors or _DETECTORS
        self._target_pose = Pose2D(
            center=self.preset.target_center_px,
            angle_deg=self.preset.target_angle_deg,
            size=self.preset.target_size_px,
        )

    def process_frame(self, frame: np.ndarray, timestamp: float, frame_id: str) -> FrameAnalysis:
        pose, method = self._detect(frame)
        evaluation = evaluate_alignment(
            det_pose=pose,
            target_pose=self._target_pose,
            mm_per_px=self.calibration.mm_per_px,
            tolerance_mm=self.preset.tolerance_mm,
            tolerance_deg=self.preset.tolerance_deg,
        )
        detection = DetectionOutcome(pose=pose, method=method)
        return FrameAnalysis(frame_id=frame_id, timestamp=timestamp, detection=detection, evaluation=evaluation)

    def _detect(self, frame: np.ndarray) -> Tuple[Optional[Pose2D], Optional[str]]:
        order = self._detection_order()
        roi = self.preset.roi
        for mode in order:
            detector = self.detectors.get(mode)
            if detector is None:
                continue
            params = self._detector_params(mode)
            pose = detector(frame, roi, params)
            if pose is not None:
                return pose, mode
        return None, None

    def _detector_params(self, detector_name: str) -> Dict[str, object]:
        params = self.preset.params
        if isinstance(params, dict) and detector_name in params and isinstance(params[detector_name], dict):
            return params[detector_name]
        return params if isinstance(params, dict) else {}

    def _detection_order(self) -> Tuple[str, ...]:
        primary = self.preset.detection_mode
        known = tuple(self.detectors.keys())
        order = [primary]
        order.extend(mode for mode in known if mode != primary)
        return tuple(order)
