# AlignPress Pro — Sprint 2.1 (Planchas + Estilos + Tallas)

La segunda entrega incorpora la arquitectura completa de planchas, estilos y tallas, además de una UX guiada para operador y técnico. El núcleo de detección del Sprint 1 se reutiliza; ahora se generan presets dinámicamente combinando plancha calibrada + estilo (lista de logos) + variante por talla.

## Arquitectura

### Dominio (`alignpress/domain`)
- **PlatenProfile** (`platen.py`): nombre, tamaño en mm, calibración (mm/px, patrón, última verificación).
- **StyleDefinition** (`style.py`): estilo/diseño con lista de logos, parámetros detector y geometría en mm.
- **SizeVariant** (`variant.py`): offsets/escala por talla respecto al estilo base.
- **Composition** (`composition.py`): combina plancha + estilo + talla → presets `LogoTaskDefinition` listos para el `LogoAligner`.
- **JobCard** (`job.py`): tarjeta de trabajo por prenda procesada (timestamp, plancha, estilo, talla, métricas por logo, snapshot opcional).

### Configuración (`config/app.yaml`)
```yaml
schema_version: 3
language: es
dataset:
  path: datasets/sample_images
  fps: 30.0
  loop: false
logging:
  output_dir: logs
  formats: [csv, json]
ui:
  theme: light
  technical_pin: '2468'
assets:
  platens_dir: platens
  styles_dir: styles
  variants_dir: variants
  job_cards_dir: logs/job_cards
selection:
  platen_path: platens/default_platen.json
  style_path: styles/example_style.json
  variant_path: variants/example_variant.json
calibration_reminder_days: 7
calibration_expire_days: 30
```
- `assets` define directorios donde se guardan los JSON versionados.
- `selection` marca la combinación activa (se actualiza desde el wizard de operador).
- `calibration_reminder_days` / `calibration_expire_days` controlan el chip de calibración.

### Archivos de ejemplo
- `platens/default_platen.json`: plancha 40x50 mm/px calibrada.
- `styles/example_style.json`: estilo con logos “Pecho” y “Manga”, posiciones en mm y parámetros de detector.
- `variants/example_variant.json`: talla L con offsets y escala.

## UI Operador
1. **Wizard de selección**: Paso a paso plancha → estilo → talla. La selección se guarda y se recalculan presets.
2. **Header**: muestra Plancha, Estilo, Talla y Versión activos. Chip de calibración 🟢/🟠/🔴 según antigüedad.
3. **Checklist**: lista de logos pendiente/OK/Ajustar, con navegación manual o auto avance al obtener “OK”.
4. **Viewport**: overlay fantasma del logo, detección actual, flechas, métricas (`dx/dy/θ`). Tooltips de corrección (“Mover 2.1 mm ↓”, “Rotar 1.2° ↻”).
5. **Historial**: tabla con estado por frame/logos. Exportable a CSV/JSON (`Archivo → Exportar resultados`).
6. **Snapshots**: botón y atajo `S` guardan imagen con overlay.
7. **Finalización**: al completar todos los logos se genera un Job Card en `logs/job_cards/job_*.json` con métricas, estados y dataset usado.

Atajos: `Espacio` (Play/Pause), `F11` (Pantalla completa), `S` (Snapshot). El dataset se procesa en modo simulación; cada sesión genera resultados en `logs/session_*/`.

## UI Técnico
La vista técnica ahora tiene tres editores en pestañas:

1. **Planchas**
   - Lista de perfiles (`platens/*.json`).
   - Campos para tamaño (mm), mm/px, patrón, fecha de verificación.
   - Botón “Calibrar…” abre el panel de calibración (`CalibrationPanel`) para calcular mm/px desde un chessboard.
   - Importar/exportar/duplicar/eliminar con guardado directo a JSON.

2. **Estilos**
   - Lista de estilos (`styles/*.json`).
   - Edición de logos: posición objetivo (mm), ROI, detector (contour/ArUco), tolerancias, instrucciones para operador y parámetros JSON del detector.
   - Añadir/duplicar/eliminar logos desde la UI, todo persistente en JSON.

3. **Tallas**
   - Lista de variantes (`variants/*.json`).
   - Asociación con estilo base, factor de escala y overrides por logo (offsets en mm, escala relativa, tolerancias específicas).
   - Importar/exportar, duplicar y guardar.

Al guardar plancha/estilo/talla se emite `dataChanged` → la combinación activa se recalcula automáticamente para el operador.

## Flujo Operador
1. Abrir wizard (botón “Cambiar preset”).
2. Seleccionar plancha/estilo/talla y confirmar.
3. Revisar cada logo hasta obtener checklist ✅.
4. Exportar resultados o guardar snapshot según necesidad.
5. Revisar “job card” generado en `logs/job_cards/` para trazabilidad.

## Flujo Técnico
1. Configurar planchas: definir dimensiones y recalibrar cuando corresponde.
2. Crear/editar estilos agregando logos en mm (coordenadas absolutas sobre la plancha calibrada).
3. Crear variantes por talla, ajustando offsets y escala.
4. Notificar al operador tras guardar (la app recarga la combinación automáticamente).

## Logging & Evidencias
- `logs/session_*`: CSV/JSON por sesión (frame, logo, dx/dy/θ, método, estado). Snapshots opcionales en `logs/session_*/snapshots/`.
- `logs/job_cards/job_*.json`: tarjeta de trabajo por prenda con lista de logos, métricas y estado final.

## Ejecución
```bash
source .venv/bin/activate
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
export LIBGL_ALWAYS_INDIRECT=1
python -m scripts.run_ui --config config/app.yaml
```
*(En Windows nativo o Linux con escritorio no necesitas las variables DISPLAY).* 

UI simplificada (AlignPress v2 prototype):
```bash
python -m scripts.run_ui_v2 --config config/app.yaml
```

Modo headless para validar el core:
```bash
python scripts/process_dataset.py --config config/app.yaml
```

## Pruebas y validación
```bash
.venv/bin/python -m pytest
.venv/bin/python -m compileall alignpress scripts
```
Las pruebas cubren geometría, calibración y detección. El pipeline de composición se valida al ejecutar la app generando presets y job cards.

## Notas
- Todos los JSON poseen `schema_version` para evolucionar el dominio.
- Las rutas en `config/app.yaml` se guardan en relativo; los editores crean directorios automáticamente si no existen.
- El chip de calibración cambia a 🟠 o 🔴 cuando `last_verified` supera los días configurados (7 y 30 por defecto).
- Los parámetros de detector se editan como JSON libre; el operador verá las instrucciones asociadas a cada logo.
