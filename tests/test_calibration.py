import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from alignpress.core.calibration import (
    Calibration,
    aruco_mm_per_px,
    chessboard_mm_per_px,
    load_calibration,
    save_calibration,
)


def _synthetic_chessboard(pattern_size=(7, 5), square_px=40) -> np.ndarray:
    corners_x, corners_y = pattern_size
    squares_x = corners_x + 1
    squares_y = corners_y + 1
    width = squares_x * square_px
    height = squares_y * square_px
    board = np.zeros((height, width), dtype=np.uint8)
    for row in range(squares_y):
        for col in range(squares_x):
            if (row + col) % 2 == 0:
                x0, y0 = col * square_px, row * square_px
                x1, y1 = x0 + square_px, y0 + square_px
                board[y0:y1, x0:x1] = 255
    board_bgr = cv2.cvtColor(board, cv2.COLOR_GRAY2BGR)
    return board_bgr


def test_chessboard_calibration_consistency(tmp_path):
    pattern = (7, 5)
    square_px = 40
    square_mm = 25.0
    image = _synthetic_chessboard(pattern_size=pattern, square_px=square_px)
    calibration = chessboard_mm_per_px(image, pattern, square_mm)
    assert calibration is not None
    expected_mm_per_px = square_mm / square_px
    assert calibration.method == "chessboard"
    assert calibration.schema_version == 1
    assert calibration.mm_per_px == pytest.approx(expected_mm_per_px, rel=0.01)

    image_blur = cv2.GaussianBlur(image, (5, 5), 0)
    calibration_blur = chessboard_mm_per_px(image_blur, pattern, square_mm)
    assert calibration_blur is not None
    variation = abs(calibration_blur.mm_per_px - calibration.mm_per_px) / calibration.mm_per_px
    assert variation <= 0.03

    output = tmp_path / "cal.json"
    calibration.meta = dict(calibration.meta)
    calibration.meta["source_image"] = "synthetic"
    save_calibration(calibration, output)
    loaded = load_calibration(output)
    assert isinstance(loaded, Calibration)
    assert loaded.mm_per_px == pytest.approx(calibration.mm_per_px, rel=1e-6)
    assert loaded.meta["source_image"] == "synthetic"


@pytest.mark.skipif(not hasattr(cv2, "aruco"), reason="cv2.aruco no disponible")
def test_aruco_calibration(tmp_path):
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)
    marker_id = 7
    side_px = 200
    marker = cv2.aruco.generateImageMarker(dictionary, marker_id, side_px)
    image = np.full((360, 360), 255, dtype=np.uint8)
    start = 80
    image[start:start + side_px, start:start + side_px] = marker
    image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    marker_mm = 50.0
    calibration = aruco_mm_per_px(image_bgr, marker_length_mm=marker_mm, dictionary_name="DICT_5X5_50")
    assert calibration is not None
    expected_mm_per_px = marker_mm / side_px
    assert calibration.mm_per_px == pytest.approx(expected_mm_per_px, rel=0.05)

    output = tmp_path / "aruco_cal.json"
    save_calibration(calibration, output)
    loaded = load_calibration(output)
    assert loaded.method == "aruco"
