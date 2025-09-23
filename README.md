# AlignPress Pro — Fase 1 (Prototipo 1 cámara, Raspberry Pi 3)

Sistema de alineación asistida para planchas de doble paleta. Este prototipo usa **1 cámara** y verifica la colocación del **logo** en prenda con visión computarizada.

## Módulos incluidos
- `alignpress/core/camera.py`: captura de video (OpenCV VideoCapture).
- `alignpress/core/calibration.py`: calibración px→mm usando **chessboard A4** o **ArUco** (opcional).
- `alignpress/detection/contour_detector.py`: detección simple por umbral + contornos.
- `alignpress/detection/aruco_detector.py`: detección por marcador ArUco (si `cv2.aruco` disponible).
- `alignpress/core/geometry.py`: cálculo de dx, dy y rotación θ vs preset.
- `alignpress/core/presets.py`: carga/validación de presets JSON.
- `alignpress/gui/overlay.py`: overlay con rectángulo fantasma, flechas y estados.
- `scripts/main.py`: loop principal de demo.

## Instalación rápida (WSL/Linux dev)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# Si falla opencv-contrib en WSL, puedes omitirlo: pip install opencv-python
```

## Instalación en Raspberry Pi 3 (Raspberry Pi OS Bookworm)
**Sugerido (más liviano y estable en Pi):**
```bash
sudo apt update
sudo apt install -y python3-opencv python3-numpy
# Verifica:
python3 -c "import cv2, numpy as np; print('OpenCV', cv2.__version__)"
```

**Opcional (si quieres pip):**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install numpy==1.24.*  # versiones más viejas pueden ser necesarias según arch
pip install opencv-python==4.8.*
# Para ArUco en Pi, lo más estable suele ser apt (python3-opencv ya lo trae en muchos builds)
```

## Uso
1. Imprime un **chessboard** para A4 (por ejemplo 7x5 cuadros internos, tamaño de cuadro 25 mm).
2. Genera la calibración (ejemplo incluido en `calibrations/chessboard_7x5_25mm.json`). Ajusta `square_size_mm` si imprimes otro tamaño.
3. Conecta la cámara y ejecuta:
```bash
python scripts/main.py --camera 0 --preset presets/example_tshirt.json --calibration calibrations/chessboard_7x5_25mm.json
```
4. Teclas:
   - `q` → salir
   - `s` → guardar frame (debug)
   - `c` → forzar reintento de calibración en vivo (si `mode="chessboard_live"`)

## Notas de portabilidad (WSL → Raspberry)
- Evita rutas absolutas; usa `Path` relativo al proyecto.
- Parametriza índices de cámara y resoluciones (no asumas 1920x1080 en Pi 3).
- Evita dependencias GUI pesadas. Este demo usa `cv2.imshow`; en Raspberry usa escritorio (X11/Wayland).
- Si corres headless en Pi, desactiva GUI y guarda imágenes/estados a disco o por TCP.
- Marca dependencias opcionales de ArUco; si no está `cv2.aruco`, el sistema cae a contornos automáticamente.
