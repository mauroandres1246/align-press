from typing import Tuple
import cv2
import numpy as np

def draw_ghost_rect(frame, center, size, angle_deg, color=(0,255,0), thickness=1):
    box = _rect_points(center, size, angle_deg)
    cv2.polylines(frame, [box.astype(int)], isClosed=True, color=color, thickness=thickness)

def draw_detected_rect(frame, center, size, angle_deg, color=(0,0,255), thickness=2):
    box = _rect_points(center, size, angle_deg)
    cv2.polylines(frame, [box.astype(int)], isClosed=True, color=color, thickness=thickness)

def draw_arrows(frame, p_from, p_to, color=(255,255,255)):
    cv2.arrowedLine(frame, tuple(np.int32(p_from)), tuple(np.int32(p_to)), color, 2, tipLength=0.2)

def put_hud(frame, text, org=(10,30), color=(0,255,0)):
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)

def _rect_points(center, size, angle_deg):
    cx, cy = center
    w, h = size
    rect = ((cx, cy), (w, h), angle_deg)
    box = cv2.boxPoints(rect)
    return box
