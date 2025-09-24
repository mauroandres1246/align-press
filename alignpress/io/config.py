from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class DatasetConfig:
    path: Path
    fps: float = 30.0
    loop: bool = False


@dataclass
class LoggingConfig:
    output_dir: Path
    formats: List[str]


@dataclass
class AppConfig:
    schema_version: int
    language: str
    dataset: DatasetConfig
    preset_path: Path
    calibration_path: Path
    logging: LoggingConfig


def _resolve_path(base: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (base / candidate).resolve()
    return candidate


def load_app_config(path: Path) -> AppConfig:
    raw = yaml.safe_load(path.read_text())
    if raw is None:
        raise ValueError("app.yaml está vacío")

    schema_version = int(raw.get("schema_version", 1))
    language = raw.get("language", "es")

    dataset_raw = raw.get("dataset", {})
    dataset_path = _resolve_path(path.parent, dataset_raw.get("path", "."))
    dataset_fps = float(dataset_raw.get("fps", 30.0))
    dataset_loop = bool(dataset_raw.get("loop", False))
    dataset_cfg = DatasetConfig(path=dataset_path, fps=dataset_fps, loop=dataset_loop)

    preset_path = _resolve_path(path.parent, raw["preset_path"])
    calibration_path = _resolve_path(path.parent, raw["calibration_path"])

    logging_raw = raw.get("logging", {})
    formats = logging_raw.get("formats", ["csv"])
    if isinstance(formats, str):
        formats = [formats]
    logging_dir = _resolve_path(path.parent, logging_raw.get("output_dir", "logs"))
    logging_cfg = LoggingConfig(output_dir=logging_dir, formats=list(formats))

    return AppConfig(
        schema_version=schema_version,
        language=language,
        dataset=dataset_cfg,
        preset_path=preset_path,
        calibration_path=calibration_path,
        logging=logging_cfg,
    )
