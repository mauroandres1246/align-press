from typing import Optional, Tuple
import cv2
import numpy as np
from alignpress.core.geometry import Pose2D

def detect_logo_aruco(frame, roi, params) -> Optional[Pose2D]:
    if not hasattr(cv2, "aruco"):
        return None
    x,y,w,h = roi
    roi_img = frame[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    aruco = cv2.aruco
    dict_name = params.get("dictionary", "DICT_5X5_50")
    dict_map = {n:getattr(aruco, n) for n in dir(aruco) if n.startswith("DICT_")}
    if dict_name not in dict_map:
        return None
    dictionary = aruco.getPredefinedDictionary(dict_map[dict_name])
    corners, ids, _ = aruco.detectMarkers(gray, dictionary)
    if ids is None or len(corners)==0:
        return None
    pts = corners[0][0]
    center = pts.mean(axis=0)
    # orientacion: usa PCA o vector entre dos esquinas
    v = pts[1] - pts[0]
    angle = np.degrees(np.arctan2(v[1], v[0]))
    # tamaño aproximado
    side_lengths = [np.linalg.norm(pts[i]-pts[(i+1)%4]) for i in range(4)]
    size = (float(np.mean(side_lengths)), float(np.mean(side_lengths)))
    return Pose2D(center=(x+float(center[0]), y+float(center[1])), angle_deg=float(angle), size=size)
