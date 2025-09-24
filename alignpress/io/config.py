from dataclasses import dataclass, field
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
class UIConfig:
    theme: str = "light"
    operator_fullscreen: bool = False
    kiosk_mode: bool = False
    technical_pin: str = "1234"
    onboarding_completed: bool = False
    camera_layout: str = "single"  # single | dual


@dataclass
class AppConfig:
    schema_version: int
    language: str
    dataset: DatasetConfig
    preset_path: Path
    calibration_path: Path
    logging: LoggingConfig
    ui: UIConfig = field(default_factory=UIConfig)


def _resolve_path(base: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (base / candidate).resolve()
    return candidate


def _make_relative(base: Path, value: Path) -> str:
    try:
        return str(value.relative_to(base))
    except ValueError:
        return str(value)


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

    ui_raw = raw.get("ui", {})
    ui_cfg = UIConfig(
        theme=ui_raw.get("theme", "light"),
        operator_fullscreen=bool(ui_raw.get("operator_fullscreen", False)),
        kiosk_mode=bool(ui_raw.get("kiosk_mode", False)),
        technical_pin=str(ui_raw.get("technical_pin", "1234")),
        onboarding_completed=bool(ui_raw.get("onboarding_completed", False)),
        camera_layout=ui_raw.get("camera_layout", "single"),
    )

    return AppConfig(
        schema_version=schema_version,
        language=language,
        dataset=dataset_cfg,
        preset_path=preset_path,
        calibration_path=calibration_path,
        logging=logging_cfg,
        ui=ui_cfg,
    )


def save_app_config(config: AppConfig, path: Path) -> None:
    base = path.parent
    data = {
        "schema_version": config.schema_version,
        "language": config.language,
        "preset_path": _make_relative(base, config.preset_path),
        "calibration_path": _make_relative(base, config.calibration_path),
        "dataset": {
            "path": _make_relative(base, config.dataset.path),
            "fps": config.dataset.fps,
            "loop": config.dataset.loop,
        },
        "logging": {
            "output_dir": _make_relative(base, config.logging.output_dir),
            "formats": list(config.logging.formats),
        },
        "ui": {
            "theme": config.ui.theme,
            "operator_fullscreen": config.ui.operator_fullscreen,
            "kiosk_mode": config.ui.kiosk_mode,
            "technical_pin": config.ui.technical_pin,
            "onboarding_completed": config.ui.onboarding_completed,
            "camera_layout": config.ui.camera_layout,
        },
    }
    with path.open("w") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)
