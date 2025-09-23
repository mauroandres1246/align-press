from typing import Optional, Tuple
import cv2

class Camera:
    def __init__(self, index:int=0, resolution:Optional[Tuple[int,int]]=None):
        self.index = index
        self.cap = cv2.VideoCapture(index)
        if resolution:
            w, h = resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("No se pudo leer de la cámara")
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
