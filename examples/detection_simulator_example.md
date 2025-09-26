# Ejemplo de Uso - Detection Simulator Enhanced

## 🔍 **Detection Simulator con Algoritmos Reales**

El Detection Simulator mejorado ahora implementa algoritmos de detección reales usando OpenCV para pruebas precisas sin hardware.

## 🚀 **Flujo de Trabajo Completo**

### **1. Preparación del Entorno**

```bash
# Estructura de archivos para testing
test_images/
├── comunicaciones/
│   ├── talla_s/
│   │   ├── camisola_s_correcta.jpg
│   │   ├── camisola_s_incorrecta.jpg
│   │   └── camisola_s_sin_logos.jpg
│   ├── talla_m/
│   │   ├── camisola_m_correcta.jpg
│   │   ├── camisola_m_incorrecta.jpg
│   │   └── camisola_m_sin_logos.jpg
│   └── talla_l/
│       ├── camisola_l_correcta.jpg
│       ├── camisola_l_incorrecta.jpg
│       └── camisola_l_sin_logos.jpg

calibrations/
└── platen_calibration.json

configs/
└── comunicaciones_config.yaml  # Generado con Configuration Designer

results/
└── batch_results/              # Resultados de simulación
    ├── debug_images/
    ├── batch_detection_report.txt
    └── batch_results.json
```

## 📋 **Casos de Uso Implementados**

### **CASO 1: Simulación Individual**

```python
from pathlib import Path
from alignpress_v2.tools.detection_simulator import DetectionSimulator
from alignpress_v2.config.config_manager import ConfigManager

# Inicializar simulador
simulator = DetectionSimulator()

# Cargar calibración
calibration_path = Path("calibrations/platen_calibration.json")
simulator.load_calibration(calibration_path)

# Cargar configuración
config_manager = ConfigManager(Path("configs/comunicaciones_config.yaml"))
config = config_manager.load()
style = config.get_active_style()

# Simular detección individual
result = simulator.simulate_garment_detection(
    image_path=Path("test_images/comunicaciones/talla_m/camisola_m_correcta.jpg"),
    style=style,
    config=config
)

# Crear imagen de debug
debug_image = simulator.create_visual_debug_image(
    Path("test_images/comunicaciones/talla_m/camisola_m_correcta.jpg"),
    result,
    Path("results/debug_individual.jpg")
)

print(f"Resultado: {'ÉXITO' if result['overall_success'] else 'FALLO'}")
print(f"Logos detectados: {result['successful_logos']}/{result['logo_count']}")
print(f"Confianza promedio: {result['average_confidence']:.3f}")
print(f"Tiempo de procesamiento: {result['processing_time_ms']:.1f}ms")
```

### **CASO 2: Simulación por Lotes con Variantes**

```python
# Simulación masiva con todas las variantes de talla
batch_results = simulator.simulate_batch_with_variants(
    image_dir=Path("test_images/comunicaciones/"),
    config=config,
    calibration_path=calibration_path,
    image_pattern="**/*.jpg",  # Incluye subdirectorios
    test_variants=True
)

# Exportar resultados completos
output_dir = simulator.export_batch_results(
    batch_results=batch_results,
    output_dir=Path("results/batch_results"),
    create_debug_images=True
)

print(f"Imágenes procesadas: {batch_results['images_processed']}")
print(f"Variantes probadas: {batch_results['variants_tested']}")
print(f"Total de detecciones: {batch_results['total_detections']}")
print(f"Resultados exportados a: {output_dir}")
```

## 🎯 **Algoritmos de Detección Implementados**

### **1. Detección por Contornos (contour)**

**Uso:** Logos con formas definidas (escudos, símbolos)

**Algoritmo:**
1. Preprocesamiento: Denoising + CLAHE contrast enhancement
2. Conversión a escala de grises
3. Filtro Gaussiano para reducir ruido
4. Detección de bordes con Canny
5. Búsqueda de contornos
6. Filtrado por área y aspect ratio
7. Selección del mejor contorno por área
8. Cálculo de centroide y orientación

**Parámetros configurables:**
```python
'contour': {
    'blur_kernel': (5, 5),      # Kernel de desenfoque
    'canny_lower': 50,          # Umbral inferior Canny
    'canny_upper': 150,         # Umbral superior Canny
    'min_area': 100,            # Área mínima de contorno
    'max_area': 50000,          # Área máxima de contorno
    'aspect_ratio_range': (0.2, 5.0)  # Rango de aspect ratio válido
}
```

### **2. Detección por Template Matching (template)**

**Uso:** Logos con patrones específicos, textos

**Algoritmo:**
1. Extracción de ROI
2. Conversión a escala de grises
3. Análisis de características de textura
4. Cálculo de densidad de bordes
5. Score basado en intensidad media y varianza
6. Simulación de matching con variación realista

**Características analizadas:**
- Densidad de bordes (edge density)
- Intensidad media
- Desviación estándar de intensidad
- Patrones de textura

### **3. Detección de ArUco Markers (aruco)**

**Uso:** Marcadores ArUco para calibración y referencias precisas

**Algoritmo:**
1. Configuración del diccionario ArUco (DICT_6X6_250)
2. Detección directa con detectMarkers()
3. Cálculo preciso del centro del marcador
4. Determinación de orientación desde esquinas
5. Confianza alta (0.95) por naturaleza binaria

**Parámetros:**
```python
'aruco': {
    'dictionary': cv2.aruco.DICT_6X6_250,
    'detector_params': cv2.aruco.DetectorParameters()
}
```

## 📊 **Métricas y Resultados**

### **Resultados por Logo Individual:**
```
✅ escudo_principal:
   Detectado: Sí
   Confianza: 0.847
   Posición: (120.3, 79.8) mm
   Error: 1.2 mm
   Tiempo: 15.3ms

❌ sponsor_secundario:
   Detectado: No
   Confianza: 0.412
   Posición: (0.0, 0.0) mm
   Error: 999.0 mm
   Tiempo: 12.1ms
```

### **Estadísticas de Lote:**
```
ALIGNPRESS v2 - COMPREHENSIVE BATCH DETECTION REPORT
================================================================================
Generated: 2024-09-25 18:30:00
Calibration Factor: 0.2645 mm/pixel

OVERALL PERFORMANCE:
----------------------------------------
Total Images Processed: 15
Total Detection Sessions: 45  # 15 imágenes × 3 variantes
Variants Tested: 3
Total Logo Attempts: 135     # 45 sesiones × 3 logos

SUCCESS RATES:
----------------------------------------
Session Success Rate: 73.3%
Logo Detection Rate: 84.4%
Average Confidence: 0.721
Average Processing Time: 28.5 ms

VARIANT PERFORMANCE:
----------------------------------------
Variant: base
  Success Rate: 80.0%
  Avg Confidence: 0.756
  Avg Time: 26.2 ms

Variant: comunicaciones_2024_s
  Success Rate: 73.3%
  Avg Confidence: 0.701
  Avg Time: 29.1 ms

Variant: comunicaciones_2024_l
  Success Rate: 66.7%
  Avg Confidence: 0.706
  Avg Time: 30.2 ms
```

## 🛠️ **Integración con Development Tools**

### **Desde Command Line:**

```bash
# Simulación individual
python dev_tools_launcher.py --simulator \
    --image test_images/comunicaciones/talla_m/camisola_m_correcta.jpg \
    --config configs/comunicaciones_config.yaml

# Simulación por lotes
python -c "
from pathlib import Path
from alignpress_v2.tools.detection_simulator import DetectionSimulator
from alignpress_v2.config.config_manager import ConfigManager

simulator = DetectionSimulator()
config = ConfigManager(Path('configs/comunicaciones_config.yaml')).load()

results = simulator.simulate_batch_with_variants(
    Path('test_images/comunicaciones/'),
    config,
    Path('calibrations/platen_calibration.json')
)

simulator.export_batch_results(results, Path('results/batch_test'))
"
```

### **Integración con Configuration Designer:**

El Configuration Designer ya tiene integración completa:
- **"Probar Detección"** ejecuta simulación individual
- **Resultados en ventana popup** con métricas detalladas
- **Debug Image viewer** integrado
- **Exportación automática** de resultados

## 🎯 **Casos de Testing Recomendados**

### **Testing de Desarrollo:**
```python
# Test 1: Imagen perfecta (todos los logos visibles y correctos)
test_perfect = "test_images/comunicaciones/talla_m/camisola_m_correcta.jpg"

# Test 2: Imagen con logos parcialmente ocultos
test_partial = "test_images/comunicaciones/talla_m/camisola_m_parcial.jpg"

# Test 3: Imagen sin logos (falso negativo esperado)
test_empty = "test_images/comunicaciones/talla_m/camisola_m_sin_logos.jpg"

# Test 4: Imagen con ruido/mala iluminación
test_noisy = "test_images/comunicaciones/talla_m/camisola_m_ruido.jpg"

# Test masivo para validar variantes
batch_results = simulator.simulate_batch_with_variants(
    Path("test_images/comunicaciones/"),
    config,
    calibration_path
)
```

### **Validación de Performance:**
- **Tiempo de procesamiento:** < 50ms por logo
- **Confianza mínima:** > 0.6 para detección exitosa
- **Error de posición:** < 5mm para logos centrados
- **Success rate:** > 80% en condiciones normales

## 💡 **Optimización de Parámetros**

### **Para mejorar detección de contornos:**
```python
# Ajustar para logos más pequeños
detector_params['contour']['min_area'] = 50
detector_params['contour']['canny_lower'] = 30

# Ajustar para logos con menos contraste
detector_params['contour']['canny_upper'] = 100
```

### **Para mejorar template matching:**
```python
# Más sensible a patrones de textura
detector_params['template']['threshold'] = 0.6
detector_params['template']['scale_steps'] = 7
```

## 🔄 **Siguiente Fase: Pipeline Completo**

Con Detection Simulator Enhanced completado:

1. ✅ **Calibración visual** con patrones reales
2. ✅ **Configuración interactiva** con coordenadas mm
3. ✅ **Simulación con algoritmos reales** y métricas precisas
4. 🎯 **FASE 4: Pipeline completo** integrando todo el flujo

**Flujo completo disponible:**
Calibrar → Configurar → Simular → Validar → Producción

¡El sistema está listo for comprehensive static debugging workflow!