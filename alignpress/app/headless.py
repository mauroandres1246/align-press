from pathlib import Path
from typing import List, Optional

from alignpress.core.alignment import FrameAnalysis, LogoAligner
from alignpress.core.calibration import load_calibration
from alignpress.core.presets import load_preset
from alignpress.io.config import AppConfig, load_app_config
from alignpress.io.logger import ResultLogger
from alignpress.io.simulated_source import SimulatedSource


def _load_config(path: Path) -> AppConfig:
    return load_app_config(path)


def run_headless(config_path: Path, max_frames: Optional[int] = None) -> List[FrameAnalysis]:
    cfg = _load_config(config_path)
    preset = load_preset(cfg.preset_path)
    calibration = load_calibration(cfg.calibration_path)
    source = SimulatedSource(cfg.dataset.path, fps=cfg.dataset.fps, loop=cfg.dataset.loop)
    aligner = LogoAligner(preset=preset, calibration=calibration)

    results: List[FrameAnalysis] = []
    with ResultLogger(cfg.logging.output_dir, cfg.logging.formats) as logger:
        for idx, packet in enumerate(source.frames()):
            analysis = aligner.process_frame(packet.frame, packet.timestamp, packet.frame_id)
            logger.log(analysis.to_record())
            results.append(analysis)
            if max_frames is not None and idx + 1 >= max_frames:
                break
    return results
