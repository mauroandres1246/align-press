# AlignPress v2 — Sistema de Detección Visual de Logos

Sistema moderno de detección y alineación de logos con interfaz CustomTkinter, arquitectura MVC y herramientas completas de desarrollo. Diseñado para operación industrial con debugging avanzado y configuración multi-logo.

## 🏗️ Arquitectura

### **Arquitectura v2 (Principal) - CustomTkinter/MVC**
```
alignpress_v2/
├── config/          # Sistema de configuración unificado
│   ├── models.py    # Dataclasses para configuración
│   └── config_manager.py  # Gestión de configuración
├── controller/      # Controladores MVC + Event Bus
│   ├── app_controller.py   # Controlador principal
│   ├── state_manager.py    # Gestión de estado centralizado
│   └── event_bus.py        # Sistema de eventos desacoplado
├── services/        # Servicios de negocio
│   ├── detection_service.py    # Detección de logos
│   ├── calibration_service.py  # Calibración de cámara
│   └── composition_service.py  # Composición de presets
├── infrastructure/ # Abstracción de hardware
│   └── hardware.py          # HAL para GPIO, Arduino, etc.
├── ui/             # Interfaz CustomTkinter moderna
│   ├── main_window.py      # Ventana principal
│   ├── components/         # Componentes reutilizables
│   └── app.py             # Launcher de aplicación
└── tools/          # Herramientas de desarrollo
    ├── config_designer.py  # Diseñador visual GUI
    └── detection_simulator.py  # Simulador para debugging
```

### **Arquitectura Legacy - PySide6/MVVM**
```
alignpress/         # Implementación original (mantenida)
├── domain/         # Modelos de dominio
├── ui/             # Interfaz PySide6
└── core/           # Algoritmos de detección
```

## ⚙️ Configuración

### **Sistema Unificado v2 (Recomendado)**
La configuración v2 usa un solo archivo YAML con toda la configuración:

```yaml
# config/app_v2.yaml
version: "2.0.0"
system:
  language: "es"
  units: "mm"
  theme: "light"

calibration:
  factor_mm_px: 0.2645
  timestamp: "2024-01-15T10:30:00"
  method: "chessboard_auto"

hardware:
  camera:
    device_id: 0
    resolution: [1920, 1080]
    fps: 30
  gpio:
    enabled: true
    led_pin: 18
    button_pin: 19

library:
  styles:
    - id: "comunicaciones_2024"
      name: "Camisola Comunicaciones"
      logos:
        - id: "escudo_principal"
          position_mm: {x: 100.0, y: 80.0}
          tolerance_mm: 3.0
          detector_type: "contour"
          roi: {x: 70, y: 50, width: 60, height: 60}

  variants:
    - id: "comunicaciones_2024_s"
      size: "S"
      scale_factor: 0.90
      offsets:
        escudo_principal: {x: -8.0, y: -5.0}

session:
  active_style_id: "comunicaciones_2024"
  active_variant_id: "comunicaciones_2024_m"
```

### **Configuración Legacy**
```yaml
# config/app.yaml (para compatibilidad)
schema_version: 3
language: es
assets:
  platens_dir: platens
  styles_dir: styles
  variants_dir: variants
```

## 🚀 Ejecución

### **AlignPress v2 (Recomendado)**
```bash
# Aplicación principal con UI moderna
python run_alignpress_v2.py

# Con configuración específica
python run_alignpress_v2.py --config configs/examples/comunicaciones_2024_complete.yaml

# Herramientas de desarrollo (menú interactivo)
python dev_tools_launcher.py

# Ejemplo completo de configuración multi-logo
python example_camisola_workflow.py
```

### **Aplicación Legacy**
```bash
# PySide6 UI (compatibilidad)
python -m scripts.run_ui --config config/app.yaml

# Procesamiento sin interfaz
python scripts/process_dataset.py --config config/app.yaml
```

### **Validación y Testing**
```bash
# Validar arquitectura v2
python validate_v2_architecture.py

# Tests de integración
python test_ui_integration.py

# Tests completos
python -m pytest
```

## 🛠️ Herramientas de Desarrollo

### **1. Launcher Principal**
```bash
python dev_tools_launcher.py
```
Menú interactivo con acceso a todas las herramientas:
- 🎨 Configuration Designer (GUI)
- 🔍 Detection Simulator
- 🎽 Example Workflows
- 🖥️ UI Application
- ✅ Integration Tests

### **2. Configuration Designer**
```bash
python -m alignpress_v2.tools.config_designer
```
**Herramienta GUI para:**
- Cargar imágenes de prendas
- Colocar logos visualmente con el mouse
- Definir ROIs interactivamente
- Generar configuraciones automáticamente
- Exportar a YAML/JSON

### **3. Detection Simulator**
```bash
python dev_tools_launcher.py --simulator --image test.jpg --config config.yaml
```
**Simulador para development sin hardware:**
- Prueba algoritmos con imágenes estáticas
- Genera imágenes de debug con overlays
- Calcula métricas de precisión y velocidad
- Simula variantes de talla automáticamente

### **4. Example Workflows**
```bash
python example_camisola_workflow.py
```
**Ejemplo completo que demuestra:**
- Configuración de camisola con múltiples logos
- Variantes por talla (XS, S, M, L, XL, XXL)
- Flujo completo: configurar → guardar → simular → validar

## 📋 Casos de Uso Documentados

### **Camisola de Fútbol con Múltiples Logos**
```python
# Configuración para camisola con:
# - Escudo principal (centro pecho)
# - Sponsor principal (pecho izquierdo)
# - Sponsor técnico (pecho derecho)
# - 6 variantes de talla con ajustes automáticos

style = Style(
    id="comunicaciones_2024",
    name="Camisola Comunicaciones 2024",
    logos=[
        Logo(id="escudo", position_mm=Point(100, 80), tolerance_mm=3.0),
        Logo(id="sponsor_1", position_mm=Point(50, 120), tolerance_mm=2.5),
        Logo(id="sponsor_2", position_mm=Point(150, 120), tolerance_mm=2.5)
    ]
)
```

Ver `example_camisola_workflow.py` para implementación completa.

## 🖥️ Interfaz de Usuario

### **UI v2 - CustomTkinter (Principal)**
- ✅ **Viewport moderno** con overlays en tiempo real
- ✅ **Panel de control** con métricas y estado del sistema
- ✅ **Event-driven updates** automáticos
- ✅ **Keyboard shortcuts** (Space, F11, S, Escape)
- ✅ **Fallback a Tkinter** si CustomTkinter no disponible

### **UI Legacy - PySide6**
- 📱 Wizard de selección paso a paso
- 📊 Checklist de logos con navegación
- 🎯 Viewport con overlay fantasma y métricas
- 📈 Historial exportable (CSV/JSON)
- 📸 Sistema de snapshots

## 📁 Estructura de Archivos

### **Configuraciones v2**
```
configs/
├── examples/
│   ├── comunicaciones_2024_complete.yaml    # Configuración completa
│   └── comunicaciones_2024_style_only.json  # Solo estilo
├── production/                              # Configuraciones de producción
└── templates/                               # Plantillas reutilizables
```

### **Imágenes de Prueba**
```
test_images/
├── comunicaciones_2024/
│   ├── talla_s/
│   ├── talla_m/
│   └── talla_xl/
└── debug_outputs/                           # Imágenes de debug generadas
```

### **Logs y Resultados**
```
logs/
├── session_*/                               # Sesiones de detección
├── job_cards/                              # Tarjetas de trabajo
└── performance_metrics/                     # Métricas de rendimiento
```

## 🔄 Flujo de Trabajo Recomendado

### **1. Configuración Inicial**
1. Ejecutar `python example_camisola_workflow.py` para ver el patrón
2. Usar Configuration Designer para crear configuración específica
3. Definir logos y sus posiciones visualmente

### **2. Desarrollo y Testing**
1. Usar Detection Simulator con imágenes de prueba
2. Ajustar parámetros basándose en resultados de debug
3. Iterar hasta lograr precisión deseada

### **3. Producción**
1. Ejecutar Integration Tests para validar sistema
2. Usar UI principal para operación
3. Monitorear métricas y logs

## 📦 Dependencias

### **Core Requirements**
```bash
pip install opencv-python>=4.8 customtkinter>=5.2 pyyaml>=6.0 numpy>=1.24
```

### **Development Tools**
```bash
pip install pillow>=10.0  # Para Configuration Designer y simulador
```

### **Legacy Support**
```bash
pip install PySide6>=6.7  # Solo para UI legacy
```

## 🧪 Testing y Validación

### **Tests Automáticos**
```bash
# Arquitectura v2
python -m pytest alignpress_v2/tests/

# Integración completa
python test_ui_integration.py

# Validación de arquitectura
python validate_v2_architecture.py
```

### **Tests Manuales**
1. **Configuration Designer**: Crear configuración con GUI
2. **Detection Simulator**: Probar con imágenes reales
3. **UI Integration**: Workflow completo operador

## 🚧 Migration Guide v1 → v2

### **Migrar Configuración**
```python
# El ConfigManager v2 incluye migración automática
config_manager = ConfigManager("old_config.yaml")
v2_config = config_manager.load()  # Migra automáticamente
```

### **Migrar Flujos de Trabajo**
- ✅ **Detección**: Compatible automáticamente
- ✅ **Calibración**: Migración transparente
- ⚠️ **UI**: Requiere adaptación a nuevos componentes

## 📞 Soporte

### **Logs y Debugging**
- Logs estructurados en `alignpress_v2.log`
- Imágenes de debug automáticas en simulador
- Métricas de performance integradas

### **Herramientas de Diagnóstico**
- `python validate_v2_architecture.py` - Validación completa
- `python test_ui_integration.py` - Tests de integración
- `python dev_tools_launcher.py --tests` - Suite de pruebas

---

## 📝 Notas de Versión

### **v2.0.0 - CustomTkinter/MVC Architecture**
- ✅ Arquitectura MVC moderna con Event Bus
- ✅ UI CustomTkinter con componentes modulares
- ✅ Sistema de configuración unificado
- ✅ Herramientas completas de desarrollo
- ✅ Simulador de detección sin hardware
- ✅ Hardware Abstraction Layer (HAL)
- ✅ Multi-logo workflow documentado

### **v1.x - PySide6/MVVM (Legacy)**
- 📱 UI PySide6 con wizard de configuración
- 📊 Sistema de planchas, estilos y variantes
- 🎯 Detección con overlay fantasma
- 📈 Logging y job cards detallados

---

**El sistema v2 está listo para desarrollo y testing. Para producción en Raspberry Pi, seguir el flujo de trabajo recomendado y usar las herramientas de validación.**