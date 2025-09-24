import argparse
import sys
from pathlib import Path

from alignpress.io.config import load_app_config
from alignpress.ui.app_context import AppContext
from alignpress.ui.application import create_qapplication, update_theme
from alignpress.ui.i18n import I18nManager
from alignpress.ui.state import GlobalState, StateStore
from alignpress.ui.views.main_window import MainWindow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AlignPress Pro UI (Sprint 2 prototype)")
    parser.add_argument("--config", default="config/app.yaml", help="Ruta al archivo config/app.yaml")
    return parser.parse_args()


def main(argv: list[str] | None = None) -> int:
    args = parse_args()
    argv = argv or sys.argv

    config_path = Path(args.config).expanduser().resolve()
    config = load_app_config(config_path)

    resources_dir = Path(__file__).resolve().parent.parent / "alignpress" / "resources" / "strings"
    i18n = I18nManager(resources_dir)
    if config.language not in i18n.available_languages():
        config.language = "es"
    i18n.set_language(config.language)

    state_store = StateStore()
    context = AppContext(
        config_path=config_path,
        config=config,
        i18n=i18n,
        state_store=state_store,
    )

    app = create_qapplication(argv, context)

    def _update_theme(theme_name: str) -> None:
        update_theme(app, context, theme_name)

    window = MainWindow(context, update_theme=_update_theme)
    window.show()
    state_store.set_state(GlobalState.IDLE)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
