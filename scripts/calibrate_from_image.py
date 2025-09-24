import argparse
from pathlib import Path

import cv2

from alignpress.core.calibration import (
    Calibration,
    aruco_mm_per_px,
    chessboard_mm_per_px,
    save_calibration,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera un archivo de calibración mm/px desde una imagen.")
    parser.add_argument("--image", required=True, help="Ruta a la imagen para calibrar")
    parser.add_argument(
        "--mode",
        choices=["chessboard", "aruco"],
        default="chessboard",
        help="Método de calibración",
    )
    parser.add_argument("--output", required=True, help="Ruta de salida para guardar calibration.json")
    parser.add_argument("--pattern-size", type=int, nargs=2, metavar=("W", "H"), default=[7, 5], help="Cuadros internos del tablero (solo chessboard)")
    parser.add_argument("--square-mm", type=float, default=25.0, help="Tamaño del cuadro en mm (chessboard)")
    parser.add_argument("--marker-mm", type=float, default=50.0, help="Lado del marcador en mm (ArUco)")
    parser.add_argument("--dictionary", default="DICT_5X5_50", help="Diccionario ArUco")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_path = Path(args.image).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"No se pudo leer la imagen {image_path}")

    calibration: Calibration
    if args.mode == "chessboard":
        calibration = chessboard_mm_per_px(
            image,
            pattern_size=(args.pattern_size[0], args.pattern_size[1]),
            square_size_mm=args.square_mm,
        )
    else:
        calibration = aruco_mm_per_px(
            image,
            marker_length_mm=args.marker_mm,
            dictionary_name=args.dictionary,
        )
    if calibration is None:
        raise RuntimeError("No se pudo estimar mm/px con la imagen indicada")

    calibration.meta = dict(calibration.meta)
    calibration.meta["source_image"] = str(image_path)
    save_calibration(calibration, output_path)
    print(f"Calibración guardada en {output_path} (mm/px={calibration.mm_per_px:.6f})")


if __name__ == "__main__":
    main()
