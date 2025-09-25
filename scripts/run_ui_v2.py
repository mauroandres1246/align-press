"""Entry point for running the AlignPress v2 prototype UI."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from tkinter import TclError
except ModuleNotFoundError:  # pragma: no cover - tkinter optional in some envs
    TclError = RuntimeError  # type: ignore

from alignpress_v2.config.config_manager import ConfigManager
from alignpress_v2.controller.app_controller import AppController
from alignpress_v2.controller.state_manager import StateManager
from alignpress_v2.services.calibration_service import CalibrationService
from alignpress_v2.services.composition_service import CompositionService
from alignpress_v2.services.detection_service import DetectionService
from alignpress_v2.ui.main_window import MainWindow


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AlignPress v2 UI runner")
    parser.add_argument(
        "--config",
        default="config/app.yaml",
        help="Ruta al archivo de configuración (JSON o YAML)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config).expanduser().resolve()

    config_manager = ConfigManager(config_path)
    config = config_manager.load()

    state_manager = StateManager()
    state_manager.update_configuration(config)

    controller = AppController(
        state_manager=state_manager,
        detection_service=DetectionService(),
        calibration_service=CalibrationService(),
        composition_service=CompositionService(),
    )

    controller.subscribe_ui_ready(
        lambda: print(
            f"[AlignPress v2] UI lista. Perfil activo: platen={config.active_platen_id} "
            f"style={config.active_style_id} variant={config.active_variant_id}"
        )
    )

    try:
        window = MainWindow(controller)
    except RuntimeError as exc:  # customtkinter ausente
        print(f"[ERROR] {exc}")
        return 1
    except TclError as exc:
        _report_display_error(exc)
        return 1

    try:
        import customtkinter as ctk

        appearance = (config.theme or "system").lower()
        mapping = {"dark": "Dark", "light": "Light", "system": "System"}
        ctk.set_appearance_mode(mapping.get(appearance, "System"))
    except Exception:  # pragma: no cover - apariencia opcional
        pass

    window.bind_on_close(lambda: config_manager.save(controller.state.configuration))
    window.start()
    return 0


def _report_display_error(exc: Exception) -> None:
    print(f"[ERROR] {exc}")
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        print(
            "[HINT] No se encontró un servidor X activo. Inicia un servidor gráfico "
            "(p.ej. VcXsrv, XQuartz) y exporta la variable DISPLAY antes de ejecutar la UI."
        )
    elif sys.platform.startswith("linux"):
        print(
            "[HINT] La variable DISPLAY apunta a un host inaccesible. Verifica que el servidor X "
            "esté corriendo y que la IP sea correcta (ej. `export DISPLAY=$(awk '/nameserver/ {print $2}' /etc/resolv.conf):0`)."
        )


if __name__ == "__main__":
    sys.exit(main())
