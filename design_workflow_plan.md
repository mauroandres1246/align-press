# AlignPress v2 - Workflow de Configuración y Debugging

## 1. FLUJO DE CONFIGURACIÓN DE GARMENTS COMPLEJOS

### Caso: Camisola de Comunicaciones
- Escudo principal (centro-pecho)
- Sponsor principal (pecho izquierdo)
- Sponsor secundario (pecho derecho)
- Variaciones por talla (S, M, L, XL, XXL)

### Paso a Paso - Configuración:

#### A) Crear el Estilo Base
```python
# 1. Fotografiar camisola talla M (referencia)
# 2. Calibrar cámara con patrón conocido
# 3. Marcar posiciones de cada logo manualmente
# 4. Definir ROIs (regiones de interés) para cada logo
# 5. Configurar parámetros de detección específicos
```

#### B) Configurar Variantes de Talla
```python
# 1. Fotografiar cada talla disponible
# 2. Medir desplazamientos relativos vs talla M
# 3. Calcular factores de escala por talla
# 4. Ajustar offsets específicos si es necesario
```

#### C) Validar y Testear
```python
# 1. Ejecutar detección en modo simulación
# 2. Verificar precisión en todas las tallas
# 3. Ajustar tolerancias según resultados
# 4. Guardar configuración validada
```

## 2. ESTRUCTURA DE DATOS PROPUESTA

### Jerarquía de Configuración:
```
Library/
├── Platens/
│   ├── platen_textil_40x60.yaml
│   └── platen_textil_50x70.yaml
├── Styles/
│   ├── comunicaciones_2024.yaml
│   ├── sponsor_templates.yaml
│   └── escudos_equipos.yaml
└── Variants/
    ├── comunicaciones_s_to_xl.yaml
    └── sizing_offsets.yaml
```

### Ejemplo de Configuración Completa:
```yaml
# comunicaciones_2024.yaml
metadata:
  created: "2024-01-15"
  author: "operador_1"
  description: "Camisola comunicaciones temporada 2024"
  reference_garment: "talla_M"

base_style:
  id: "comunicaciones_2024"
  name: "Camisola Comunicaciones 2024"
  category: "camisolas_futbol"

  # Logos ordenados por prioridad de detección
  logos:
    - id: "escudo_principal"
      name: "Escudo Comunicaciones"
      priority: 1  # Se detecta primero
      position_mm: {x: 100, y: 80}
      tolerance_mm: 3.0
      detector_type: "contour"
      roi: {x: 70, y: 50, width: 60, height: 60}
      detector_params:
        min_area: 500
        max_area: 5000
        threshold_type: "adaptive"

    - id: "sponsor_movistar"
      name: "Logo Movistar"
      priority: 2
      position_mm: {x: 50, y: 120}
      tolerance_mm: 2.5
      detector_type: "template"
      roi: {x: 30, y: 100, width: 40, height: 25}
      detector_params:
        template_path: "templates/movistar_logo.png"
        match_threshold: 0.8

    - id: "sponsor_adidas"
      name: "Logo Adidas"
      priority: 3
      position_mm: {x: 150, y: 120}
      tolerance_mm: 2.5
      detector_type: "contour"
      roi: {x: 130, y: 100, width: 40, height: 25}

# Variantes por talla
size_variants:
  - size: "S"
    scale_factor: 0.85
    offsets:
      escudo_principal: {x: -8, y: -5}
      sponsor_movistar: {x: -5, y: -3}
      sponsor_adidas: {x: 5, y: -3}
    adjustments:
      tolerance_multiplier: 0.9  # Tolerancias más estrictas

  - size: "M"
    scale_factor: 1.0  # Referencia
    offsets: {}  # Sin offsets

  - size: "L"
    scale_factor: 1.1
    offsets:
      escudo_principal: {x: 5, y: 3}
      sponsor_movistar: {x: 3, y: 2}
      sponsor_adidas: {x: -3, y: 2}

  - size: "XL"
    scale_factor: 1.25
    offsets:
      escudo_principal: {x: 12, y: 8}
      sponsor_movistar: {x: 8, y: 5}
      sponsor_adidas: {x: -8, y: 5}
    adjustments:
      tolerance_multiplier: 1.1  # Tolerancias más amplias
```

## 3. ALGORITMO DE DETECCIÓN PROPUESTO

### Flujo de Detección Multi-Logo:
```python
def detect_multi_logo_garment(frame, style_config, variant_config):
    """
    Detecta múltiples logos en una prenda según configuración
    """
    results = []

    # 1. Aplicar calibración de cámara
    frame_calibrated = apply_camera_calibration(frame)

    # 2. Para cada logo (en orden de prioridad)
    for logo in sorted(style_config.logos, key=lambda x: x.priority):

        # 3. Calcular posición ajustada por talla
        adjusted_position = calculate_adjusted_position(
            logo.position_mm,
            variant_config.scale_factor,
            variant_config.offsets.get(logo.id, {})
        )

        # 4. Extraer ROI ajustada
        roi = extract_adjusted_roi(frame_calibrated, logo.roi, variant_config)

        # 5. Ejecutar detector específico
        detection_result = run_detector(
            roi,
            logo.detector_type,
            logo.detector_params
        )

        # 6. Validar resultado contra posición esperada
        if detection_result.found:
            error_mm = calculate_position_error(
                detection_result.position,
                adjusted_position
            )

            success = error_mm <= logo.tolerance_mm

            results.append(DetectionResult(
                logo_id=logo.id,
                success=success,
                position=detection_result.position,
                confidence=detection_result.confidence,
                error_mm=error_mm,
                # ... otros campos
            ))

    return MultiLogoDetectionResult(
        garment_id=style_config.id,
        variant_id=variant_config.id,
        logo_results=results,
        overall_success=all(r.success for r in results)
    )
```

## 4. ENTORNO DE DEBUGGING Y DESARROLLO

### A) Simulación con Imágenes Estáticas
```python
# Directorio de imágenes de prueba
test_images/
├── comunicaciones_2024/
│   ├── talla_s/
│   │   ├── image_001.jpg
│   │   ├── image_002.jpg
│   │   └── image_003.jpg
│   ├── talla_m/
│   │   ├── image_001.jpg
│   │   └── ...
│   └── talla_xl/
│       └── ...
```

### B) Herramientas de Debugging Visual
```python
def debug_detection_visual(image_path, config):
    """
    Herramienta visual para debugging de detección
    """
    # 1. Cargar imagen
    frame = cv2.imread(image_path)

    # 2. Mostrar ROIs configuradas
    show_configured_rois(frame, config)

    # 3. Ejecutar detección paso a paso
    for logo in config.logos:
        roi_result = debug_single_logo(frame, logo)
        show_detection_result(roi_result)

    # 4. Mostrar overlay con resultados
    show_final_overlay(frame, results)

    # 5. Permitir ajustes interactivos
    allow_interactive_adjustment(config)
```

### C) Métricas de Performance
```python
def benchmark_detection_performance(test_dataset, config):
    """
    Benchmark completo de precisión y velocidad
    """
    metrics = {
        'accuracy_by_logo': {},
        'speed_ms_per_detection': 0,
        'false_positive_rate': 0,
        'false_negative_rate': 0,
        'confidence_distribution': {}
    }

    for image_batch in test_dataset:
        # Medir tiempo y precisión
        start_time = time.time()
        results = detect_multi_logo_garment(image_batch, config)
        end_time = time.time()

        # Calcular métricas
        update_metrics(metrics, results, end_time - start_time)

    return metrics
```

## 5. ALMACENAMIENTO Y VERSIONADO

### Estructura de Base de Datos/Archivos:
```
config/
├── library/
│   ├── platens/
│   ├── styles/
│   ├── variants/
│   └── templates/
├── sessions/
│   ├── current_session.yaml
│   └── session_history/
├── calibration/
│   ├── camera_params.yaml
│   └── calibration_history/
└── results/
    ├── detection_logs/
    └── performance_metrics/
```

### Versionado de Configuraciones:
```yaml
# Cada configuración incluye metadata de versión
version_info:
  schema_version: "2.0.0"
  config_version: "1.3.2"
  created_date: "2024-01-15T10:30:00"
  last_modified: "2024-01-20T14:45:00"
  changelog:
    - version: "1.3.2"
      date: "2024-01-20"
      changes: "Ajustados offsets para talla XL"
    - version: "1.3.1"
      date: "2024-01-18"
      changes: "Mejoradas tolerancias para sponsor logos"
```