# AlignPress Pro — Sprint 1 (Core + Simulador)

Primer sprint del programa de alineación asistida AlignPress Pro. El foco es dejar un núcleo headless robusto, calibraciones reproducibles y una fuente simulada que permita validar la lógica en escritorio antes de construir la UI y el stack hardware.

## Arquitectura Sprint 1
- `alignpress/core/geometry.py`: utilidades geométricas (`Pose2D`, diffs, evaluación de tolerancias).
- `alignpress/core/calibration.py`: cálculo mm/px vía chessboard o ArUco + serialización (`schema_version`).
- `alignpress/core/presets.py`: presets con ROI/objetivo, tolerancias y parámetros por detector.
- `alignpress/core/alignment.py`: flujo principal (`LogoAligner`) que combina detección + evaluación.
- `alignpress/detection/*`: detectores por contorno y ArUco (reutilizados por el core headless y la demo interactiva).
- `alignpress/io/config.py`: carga de `config/app.yaml` (dataset, idioma, paths de preset/calibración, logging).
- `alignpress/io/simulated_source.py`: lectura de carpetas de imágenes o videos como frames con timestamp.
- `alignpress/io/logger.py`: logging de resultados a CSV y JSONL.
- `alignpress/app/headless.py`: orquestador del pipeline headless.
- `scripts/process_dataset.py`: CLI para procesar datasets simulados.
- `scripts/calibrate_from_image.py`: genera calibraciones mm/px desde una imagen estática.
- `scripts/main.py`: demo visual (manteniendo la UI básica del prototipo anterior).

## Instalación
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
- En Raspberry Pi puedes usar `sudo apt install python3-opencv python3-numpy` y ejecutar con el intérprete del sistema.
- Para usar ArUco en escritorio instala `opencv-contrib-python` (ya incluido en `requirements.txt`).

## Calibración (mm por pixel)
Genera un archivo `calibration.json` compatible con `schema_version`:
```bash
python scripts/calibrate_from_image.py \
  --image calibrations/chessboard_sample.jpg \
  --mode chessboard \
  --pattern-size 7 5 \
  --square-mm 25.0 \
  --output calibrations/chessboard_7x5_25mm.json
```
- Para ArUco usa `--mode aruco --marker-mm 50 --dictionary DICT_5X5_50`.
- El script añade `source_image` a `meta` y guarda `mm_per_px`, listo para reutilizar.

## Presets y configuración
- Presets (`presets/*.json`) incluyen `schema_version`, ROI, tolerancias y parámetros por detector (`contour`, `aruco`).
- Configuración de la app (`config/app.yaml`):
  ```yaml
  schema_version: 1
  language: es
  preset_path: presets/example_tshirt.json
  calibration_path: calibrations/chessboard_7x5_25mm.json
  dataset:
    path: datasets/sample_images
    fps: 30.0
    loop: false
  logging:
    output_dir: logs/headless_run
    formats: [csv, json]
  ```
- Coloca imágenes o videos de prueba en `datasets/sample_images/`.

## Ejecución headless (simulador)
```bash
python scripts/process_dataset.py --config config/app.yaml
# Limita cantidad de frames (debug)
python scripts/process_dataset.py --config config/app.yaml --max-frames 10
```
- Produce `logs/headless_run/results.csv` y `results.jsonl` con `dx`, `dy`, `dθ`, método de detección y estado (`ok`, `out_of_tolerance`, `not_found`).
- Puedes cambiar `logging.output_dir` por corrida para versionar resultados.

## Demo interactiva (opcional)
```bash
python scripts/main.py --camera 0 \
  --preset presets/example_tshirt.json \
  --calibration calibrations/chessboard_7x5_25mm.json
# o en modo imagen fija
python scripts/main.py --image path/a/imagen.png --preset ... --calibration ...
```
Teclas rápidas: `q` salir, `s` guardar frame (`frame_<ts>.png`).

## Pruebas y calidad
```bash
# Ejecutar tests unitarios (geometría, calibración, detección)
.venv/bin/python -m pytest
# Comprobación rápida de sintaxis
.venv/bin/python -m compileall alignpress scripts
```
Los tests de calibración/detección se omiten automáticamente si no hay `cv2` o `cv2.aruco` disponible.

## Logging y trazabilidad
- CSV listo para Excel / BI con campos `frame_id`, `timestamp`, `dx_mm`, `dy_mm`, `dtheta_deg`, `status`, `detection_method`, centro y tamaño detectado.
- JSONL para análisis posteriores o envío por red.
- Los archivos se guardan en la carpeta indicada por `config/app.yaml`.

## Notas de portabilidad
- Todo el acceso a disco usa `pathlib` y rutas relativas.
- El pipeline headless reutiliza los mismos presets/calibraciones para Windows y Raspberry Pi.
- La detección intenta primero el modo configurado y cae al siguiente detector disponible.
- Preparado para extender a 2 cámaras / Arduino en sprints posteriores (capas separadas: core, io, hw, app).
