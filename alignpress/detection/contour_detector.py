from typing import Optional, Tuple
import cv2
import numpy as np
from alignpress.core.geometry import Pose2D

def detect_logo_contour(frame, roi, params) -> Optional[Pose2D]:
    x,y,w,h = roi
    roi_img = frame[y:y+h, x:x+w]
    # Pre-proc
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    # threshold adaptable
    method = params.get("threshold", "otsu")
    if method == "fixed":
        thr = params.get("thr_value", 120)
        _, bw = cv2.threshold(blur, thr, 255, cv2.THRESH_BINARY_INV)
    else:
        _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bw = cv2.bitwise_not(bw) if params.get("invert", False) else bw
    # morfología
    k = int(params.get("morph_k", 3))
    if k > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k,k))
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)
        bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel, iterations=1)
    # contornos
    cnts, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    cnt = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(cnt) < params.get("min_area", 500):
        return None
    rect = cv2.minAreaRect(cnt)  # ((cx,cy),(w,h),angle)
    (cx,cy),(rw,rh),angle = rect
    # Ajuste: minAreaRect angle range and mapping
    pose = Pose2D(center=(x+cx, y+cy), angle_deg=float(angle), size=(rw, rh))
    return pose
