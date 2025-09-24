from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

from alignpress.io.simulated_source import FramePacket, SimulatedSource


@dataclass
class DatasetFrame:
    index: int
    frame_id: str
    timestamp: float
    frame: np.ndarray


class DatasetLoader:
    def __init__(self, path: Path, fps: float = 30.0, loop: bool = False) -> None:
        self.path = path
        self.fps = fps
        self.loop = loop

    def load(self) -> List[DatasetFrame]:
        source = SimulatedSource(self.path, fps=self.fps, loop=False)
        frames: List[DatasetFrame] = []
        for idx, packet in enumerate(source.frames()):
            if not isinstance(packet, FramePacket):
                frame_id = getattr(packet, "frame_id", f"frame_{idx:06d}")
                timestamp = getattr(packet, "timestamp", idx / self.fps)
                frame = getattr(packet, "frame")
            else:
                frame_id = packet.frame_id
                timestamp = packet.timestamp
                frame = packet.frame
            frames.append(DatasetFrame(index=idx, frame_id=frame_id, timestamp=timestamp, frame=frame.copy()))
        return frames
