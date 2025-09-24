# AlignPress Pro — Sprint 2 (UI Operador/Técnico)

Segunda iteración del proyecto AlignPress Pro. Sobre la base del núcleo headless del Sprint 1 ahora contamos con una aplicación de escritorio en PySide6 lista para operadores y técnicos, con simulador integrado, edición de presets y administración básica de hardware (mock).

## Arquitectura resumida
- `alignpress/core/*`: núcleo de detección/calibración/geom entrado en `LogoAligner` (usa detectores OpenCV, presets JSON y calibraciones versionadas).
- `alignpress/io/config.py`: carga/guardado de `config/app.yaml` con secciones `dataset`, `logging`, `ui` (tema, kiosco, PIN, layout cámaras).
- `alignpress/io/logger.py`: logger CSV/JSON por sesión (`session_<timestamp>`).
- `alignpress/ui/application.py`: creación de `QApplication`, administración de tema e internacionalización (`alignpress/ui/i18n.py`).
- `alignpress/ui/controllers/simulator.py`: controlador MVVM del simulador (playback, logging, exportación, historial en memoria).
- `alignpress/ui/views/operator_page.py`: vista Operador (tabs Cámara A/B, overlay, métricas, tabla de historial, snapshots, atajos y controles grandes).
- `alignpress/ui/views/technical_page.py`: vista Técnico (lista de presets, `PresetEditorWidget`, panel de calibración, mock Arduino, cámara dual ready, gestión de PIN/config).
- `alignpress/ui/technical/*`: widgets específicos (editor gráfico de ROI/target, panel de calibración, hardware mock).
- `scripts/run_ui.py`: punto de entrada único para la aplicación PySide6.
- Headless y utilidades siguen disponibles (`scripts/process_dataset.py`, `scripts/calibrate_from_image.py`).

## Instalación
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # incluye PySide6, OpenCV y utilidades
```
En Raspberry Pi puedes seguir usando los paquetes `python3-opencv` / `python3-numpy` del sistema y ejecutar la UI desde escritorio.

## Configuración (`config/app.yaml`)
```yaml
schema_version: 2
language: es
preset_path: ../presets/example_tshirt.json
calibration_path: ../calibrations/chessboard_7x5_25mm.json
dataset:
  path: ../datasets/sample_images
  fps: 30.0
  loop: false
logging:
  output_dir: ../logs
  formats: [csv, json]
ui:
  theme: light
  operator_fullscreen: false
  kiosk_mode: false
  technical_pin: "2468"
  onboarding_completed: false
  camera_layout: single
```
- Las rutas se resuelven relativamente al propio `config/app.yaml`.
- Al cargar dataset/preset/calibración desde la UI se actualiza y persiste este archivo.

## Lanzar la aplicación
```bash
python scripts/run_ui.py --config config/app.yaml
```
La primera ejecución muestra un onboarding breve (3 pasos). Desde la barra de menú puedes alternar tema claro/oscuro, pantalla completa (`F11`) y cambiar dataset/preset/calibración.

## Modo Operador
- **Viewport**: Pestañas Cámara A/B (estructura lista para 2 cámaras). Cámara A muestra imagen con ROI, rectángulo fantasma y resultado detectado.
- **Estado grande**: panel lateral con emoji/colores (`🟢 OK`, `🟠 Ajustar`, `🔴 No detectado`).
- **Métricas**: `dx`, `dy`, `θ` con tolerancias configuradas en el preset. Flechas indican desplazamiento respecto al objetivo.
- **Controles**: botones grandes `⏮`, `Iniciar/Pausar`, `⏭`, combo de velocidad (0.25x…2x), `Capturar`, `Cambiar preset`, `Detener`.
- **Atajos**: `Espacio` (Play/Pause), `S` (snapshot con overlay), `F11` (pantalla completa). 
- **Historial**: tabla inferior con frame, estado, métricas y timestamp. Cada frame procesado se registra y queda disponible para exportar.
- **Exportación**: `Archivo → Exportar resultados` genera CSV/JSON con la corrida actual (valores + nombre de preset + dataset).
- **Snapshots**: se guardan con overlay; se sugiere destino por defecto en `logs/session_*/snapshots/`.

### Logging automático
Cada vez que se carga un dataset se crea `logs/session_<timestamp>/` con `results.csv` y `results.jsonl`. Las filas incluyen `frame_id`, `timestamp`, `status`, `dx/dy/θ`, método de detección, nombre del preset y dataset.

## Modo Técnico
Acceso protegido: `Vista → Modo Técnico` solicita PIN (configurable en `config.ui.technical_pin`).

- **Gestión de presets**: lista lateral (JSON dentro de `presets/`). Botones para crear, duplicar, renombrar, eliminar, importar y exportar.
- **PresetEditorWidget**: vista previa editable con ROI arrastrable, centro objetivo movible, sliders numéricos para tamaño/ángulo/tolerancias y parámetros de detector (contornos/ArUco). Cambios marcan el preset como “pendiente de guardar”.
- **Calibración**: panel para cargar imagen (chessboard o ArUco), detectar esquinas/marcadores, calcular mm/px y guardar JSON (actualiza `config.calibration_path`).
- **Hardware mock**: botones `OK`, `Ajustar`, `Beep` registran eventos a modo de stub para integración con Arduino.
- **Configuración UI**: selector de layout (Single/Dual camera) y actualización del PIN técnico.
- **Reglas visibles**: se listan los estados globales (INIT, IDLE, RUN_SIM, ERROR) para operadores técnicos.

Guardar un preset actualiza automáticamente el pipeline del operador (`LogoAligner` recarga preset/calibración/dataset).

## Simulador headless
Sigue disponible para pruebas en terminal:
```bash
python scripts/process_dataset.py --config config/app.yaml
```
Genera los mismos CSV/JSON por lote en la carpeta configurada.

## Pruebas y calidad
```bash
.venv/bin/python -m pytest            # geometry/calibration/detection
.venv/bin/python -m compileall alignpress scripts
```
Las pruebas que dependen de ArUco se omiten si `cv2.aruco` no está disponible.

## Manual rápido para operador
1. Selecciona dataset/preset/calibración desde el menú (gear icon/Archivo).
2. Verifica el panel lateral: verde = correcto; naranja = ajustar; rojo = no detectado.
3. Usa `Iniciar`/`Espacio` para reproducir el lote; ajusta la velocidad con el combo.
4. Consulta la tabla inferior para ver cada captura (doble clic resalta la fila).
5. Exporta resultados o toma snapshots cuando necesites evidencia.

## Manual rápido para técnico
1. Ingresa al modo técnico (`Vista → Modo Técnico`, PIN por defecto `2468`).
2. Selecciona un preset y edítalo (ROI, objetivo, tolerancias, detector).
3. Guarda cambios para que el operador los reciba inmediatamente.
4. Usa el panel de calibración para generar nuevos perfiles mm/px desde fotos.
5. Mantén actualizado el PIN y el layout de cámaras según la instalación real.

---
Para dudas sobre la arquitectura o nuevos sprints, revisa los módulos descritos arriba: el layout está preparado para escalar a doble cámara y comunicación serial en sprints siguientes.
