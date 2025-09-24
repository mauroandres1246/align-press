import argparse
from pathlib import Path

from alignpress.app.headless import run_headless
from alignpress.io.config import load_app_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Procesa un dataset con el core headless de AlignPress.")
    parser.add_argument("--config", required=True, help="Ruta a config/app.yaml")
    parser.add_argument("--max-frames", type=int, default=None, help="Número máximo de frames a procesar")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    cfg = load_app_config(config_path)
    results = run_headless(config_path, max_frames=args.max_frames)
    total = len(results)
    ok = sum(1 for r in results if r.evaluation.status == "ok")
    out_tol = sum(1 for r in results if r.evaluation.status == "out_of_tolerance")
    not_found = sum(1 for r in results if r.evaluation.status == "not_found")
    print(
        f"Procesadas {total} capturas: OK={ok}, Fuera de tolerancia={out_tol}, No detectado={not_found}. "
        f"Logs guardados en {cfg.logging.output_dir}"
    )


if __name__ == "__main__":
    main()
