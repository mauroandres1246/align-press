import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from alignpress.detection.contour_detector import detect_logo_contour
from alignpress.detection.aruco_detector import detect_logo_aruco


def test_detect_logo_contour_returns_pose():
    image = np.full((400, 400, 3), 255, dtype=np.uint8)
    cv2.rectangle(image, (150, 150), (250, 250), (0, 0, 0), thickness=-1)
    roi = (100, 100, 200, 200)
    params = {"threshold": "otsu", "invert": True, "morph_k": 0, "min_area": 1000}
    pose = detect_logo_contour(image, roi, params)
    assert pose is not None
    assert abs(pose.center[0] - 200.0) < 1.5
    assert abs(pose.center[1] - 200.0) < 1.5
    angle = abs(pose.angle_deg)
    assert angle < 1.0 or abs(angle - 90.0) < 1.0


@pytest.mark.skipif(not hasattr(cv2, "aruco"), reason="cv2.aruco no disponible")
def test_detect_logo_aruco_returns_pose():
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)
    marker = cv2.aruco.generateImageMarker(dictionary, 10, 200)
    image = np.full((480, 480), 255, dtype=np.uint8)
    start = 140
    image[start:start + 200, start:start + 200] = marker
    image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    roi = (80, 80, 320, 320)
    params = {"dictionary": "DICT_5X5_50"}
    pose = detect_logo_aruco(image_bgr, roi, params)
    assert pose is not None
    assert abs(pose.center[0] - 240.0) < 2.0
    assert abs(pose.center[1] - 240.0) < 2.0
