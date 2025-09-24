from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

import cv2
import numpy as np

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


@dataclass
class FramePacket:
    frame_id: str
    timestamp: float
    frame: np.ndarray


class SimulatedSource:
    def __init__(self, path: Path, fps: float = 30.0, loop: bool = False) -> None:
        self.path = path
        self.fps = fps
        self.loop = loop
        if not self.path.exists():
            raise FileNotFoundError(f"Dataset no encontrado: {self.path}")

    def frames(self) -> Iterator[FramePacket]:
        if self.path.is_dir():
            return self._frames_from_directory()
        return self._frames_from_file()

    def _frames_from_directory(self) -> Iterator[FramePacket]:
        items = self._sorted_media(self.path)
        if not items:
            raise FileNotFoundError(f"La carpeta {self.path} no contiene imágenes compatibles")
        index = 0
        while True:
            for item in items:
                frame = cv2.imread(str(item))
                if frame is None:
                    raise RuntimeError(f"No se pudo leer la imagen {item}")
                timestamp = index / self.fps if self.fps > 0 else float(index)
                yield FramePacket(frame_id=item.name, timestamp=timestamp, frame=frame)
                index += 1
            if not self.loop:
                break

    def _frames_from_file(self) -> Iterator[FramePacket]:
        suffix = self.path.suffix.lower()
        if suffix not in _VIDEO_EXTENSIONS:
            if suffix in _IMAGE_EXTENSIONS:
                frame = cv2.imread(str(self.path))
                if frame is None:
                    raise RuntimeError(f"No se pudo leer la imagen {self.path}")
                yield FramePacket(frame_id=self.path.name, timestamp=0.0, frame=frame)
                return
            raise ValueError(f"Formato no soportado: {self.path.suffix}")

        def iterate_video() -> Iterator[FramePacket]:
            cap = cv2.VideoCapture(str(self.path))
            if not cap.isOpened():
                raise RuntimeError(f"No se pudo abrir el video {self.path}")
            index = 0
            try:
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    if timestamp == 0:
                        timestamp = index / self.fps if self.fps > 0 else float(index)
                    yield FramePacket(frame_id=f"{self.path.stem}_{index:06d}", timestamp=timestamp, frame=frame)
                    index += 1
            finally:
                cap.release()

        yield from iterate_video()
        while self.loop:
            yield from iterate_video()

    def _sorted_media(self, directory: Path) -> List[Path]:
        files = [p for p in directory.iterdir() if p.suffix.lower() in _IMAGE_EXTENSIONS]
        files.sort()
        return files
