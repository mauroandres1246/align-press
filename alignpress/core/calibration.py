from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import cv2
import numpy as np

@dataclass
class Calibration:
    mm_per_px: float
    method: str
    meta: Dict[str, Any]

def chessboard_mm_per_px(image, pattern_size=(7,5), square_size_mm=25.0) -> Optional[Calibration]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
    if not ret:
        return None
    # Refina esquinas
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    corners = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
    # Promedia distancias entre esquinas adyacentes en X
    w = pattern_size[0]
    h = pattern_size[1]
    dists = []
    for r in range(h):
        for c in range(w-1):
            i = r*w + c
            j = r*w + c + 1
            d = np.linalg.norm(corners[i,0] - corners[j,0])
            dists.append(d)
    if len(dists) == 0:
        return None
    mean_px_per_square = float(np.mean(dists))
    mm_per_px = square_size_mm / mean_px_per_square
    return Calibration(mm_per_px=mm_per_px, method="chessboard", meta={"pattern_size":pattern_size, "square_size_mm":square_size_mm})

def aruco_mm_per_px(image, marker_length_mm:float=50.0, dictionary_name:str="DICT_5X5_50") -> Optional[Calibration]:
    # ArUco requiere cv2.aruco (opencv-contrib). Si no existe, retornar None
    if not hasattr(cv2, "aruco"):
        return None
    aruco = cv2.aruco
    dict_map = {n:getattr(aruco, n) for n in dir(aruco) if n.startswith("DICT_")}
    if dictionary_name not in dict_map:
        return None
    dictionary = aruco.getPredefinedDictionary(dict_map[dictionary_name])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = aruco.detectMarkers(gray, dictionary)
    if ids is None or len(corners)==0:
        return None
    # Usa el primer marcador detectado
    pts = corners[0][0]  # 4x2
    # largo promedio de lados en pixeles
    side_lengths = [np.linalg.norm(pts[i]-pts[(i+1)%4]) for i in range(4)]
    mean_side_px = float(np.mean(side_lengths))
    mm_per_px = marker_length_mm / mean_side_px
    return Calibration(mm_per_px=mm_per_px, method="aruco", meta={"marker_length_mm":marker_length_mm, "dictionary":dictionary_name})
