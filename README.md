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
    ├── config_designer.py      # Diseñador visual GUI con sistema jerárquico
    ├── calibration_tool.py     # Herramienta de calibración visual mejorada
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

### **Sistema Jerárquico de Configuraciones (Nuevo)**
El Configuration Designer v2 implementa un sistema jerárquico para organizar configuraciones por diseño, talla y parte de prenda:

```
configs/
├── ComunicacionesFutbol/
│   ├── TallaS/
│   │   ├── delantera.json       # Logos de la parte delantera
│   │   ├── trasera.json         # Logos de la parte trasera
│   │   ├── manga_izquierda.json # Logos de manga izquierda
│   │   └── manga_derecha.json   # Logos de manga derecha
│   ├── TallaM/
│   │   ├── delantera.json
│   │   ├── trasera.json
│   │   └── ...
│   └── TallaXL/
│       └── ...
├── BarcelonaCamiseta/
│   ├── TallaS/
│   └── TallaM/
└── ManchesterUnited/
    └── ...
```

**Estructura de archivo de configuración:**
```json
{
  "design": "ComunicacionesFutbol",
  "size": "TallaM",
  "part": "delantera",
  "calibration_factor": 0.3526,
  "logos": [
    {
      "id": "escudo_principal",
      "name": "Escudo Comunicaciones",
      "position_mm": {"x": 150.0, "y": 120.0},
      "roi": {"x": 100.0, "y": 80.0, "width": 100.0, "height": 80.0},
      "tolerance_mm": 5.0,
      "detector": "template_matching"
    },
    {
      "id": "patrocinador",
      "name": "Logo Patrocinador",
      "position_mm": {"x": 150.0, "y": 200.0},
      "roi": {"x": 100.0, "y": 180.0, "width": 100.0, "height": 40.0},
      "tolerance_mm": 3.0,
      "detector": "template_matching"
    }
  ]
}
```

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

### **2. Configuration Designer (Mejorado)**
```bash
python -m alignpress_v2.tools.config_designer
```
**Herramienta GUI avanzada para configuración jerárquica:**

**Características principales:**
- ✅ **UI intuitiva para presets (v2.4.0)**: Configuración jerárquica simplificada
- ✅ **Interactive Preset Loading**: Navegador de archivos para cargar presets existentes con población automática de UI
- ✅ **Visual Logo Editing**: Click en logo de lista para editarlo, arrastra directamente en imagen para reposicionarlo
- ✅ **Smart Dropdown Population**: Dropdowns se llenan automáticamente con opciones existentes en la estructura
- ✅ **Dual Position Control**: Control visual (arrastrar) + control numérico (campos) con sincronización bidireccional
- ✅ **Drag-to-Move Functionality**: Arrastra logos directamente en la imagen para reposicionarlos en tiempo real
- ✅ **Click-to-Edit Workflow**: Click en cualquier logo de la lista para entrar inmediatamente en modo edición
- ✅ **Vista previa de guardado**: Ves exactamente dónde se guardará el preset
- ✅ **Integración con calibración**: Usa factor mm/pixel automáticamente

**Workflow de Preset Intuitivo (v2.4.0 - Actual):**

### **🆕 Crear Preset Nuevo:**
1. **📋 Configuración de Preset**:
   - **Diseño**: [ComunicacionesFutbol ▼] [+ Nuevo]
   - **Talla**: [TallaM ▼] [+ Nueva] ← Se actualiza según diseño
   - **Parte**: [delantera ▼] [+ Nueva] ← Se actualiza según talla
   - **Vista previa**: 💾 Se guardará en: configs/ComunicacionesFutbol/TallaM/delantera.json

2. **🖼️ Recursos**:
   - **Cargar Imagen** → Foto de la parte delantera de talla M
   - **Cargar Calibración** → Factor mm/pixel automático

3. **🎯 Por cada logo**:
   - **📂 Cargar Logo** → Seleccionar PNG/JPG del logo
   - **🎯 Posicionar** → Arrastrar con mouse en imagen
   - **✅ Confirmar Logo** → Logo aparece en lista

4. **💾 Guardar**:
   - **Guardar Preset** → Se crea estructura automáticamente

### **📂 Cargar y Editar Preset Existente:**
1. **🖼️ Cargar imagen de prenda**
2. **📂 Click "Cargar Preset"** → Navegador de archivos se abre
3. **📁 Seleccionar archivo** → Ej: configs/ComunicacionesFutbol/TallaM/delantera.json
4. **⚡ Carga automática**:
   - ✅ Dropdowns se llenan: Diseño=ComunicacionesFutbol, Talla=TallaM, Parte=delantera
   - ✅ Todos los logos aparecen en lista con posiciones exactas
   - ✅ Calibración se restaura automáticamente
5. **✏️ Editar logos**:
   - **Click en logo de lista** → Logo se resalta en naranja para edición
   - **Arrastrar en imagen** → Reposicionamiento visual en tiempo real
   - **Campos numéricos** → Control preciso de X,Y,Ancho,Alto
6. **💾 Guardar cambios** → Preset actualizado

### **🎯 Funcionalidades de Edición Visual:**
- **Click-to-Edit**: Click cualquier logo en lista → Resaltado naranja + modo edición activo
- **Drag-to-Move**: Arrastra logo directamente en imagen → Actualización en tiempo real
- **Dual Control**: Campos numéricos ↔ Posición visual sincronizados bidireccionalmente
- **Visual Feedback**: Logo seleccionado se destaca con líneas naranjas más gruesas

**Características del nuevo flujo:**
- ✅ **Un solo paso**: De 4+ clicks a 1 click para agregar logo
- ✅ **Feedback en tiempo real**: Coordenadas y tamaño visibles durante drag
- ✅ **Auto-confirmación**: Sin botones "Confirmar Logo" manuales
- ✅ **Panel unificado**: "Posición y Tamaño" para todas las operaciones
- ✅ **Cursor crosshair**: Indicación visual clara de modo posicionamiento
- ✅ **Overlay semi-transparente**: Feedback visual durante posicionamiento

**Archivos generados:**
- `configs/ComunicacionesFutbol/TallaM/delantera.json`
- `configs/ComunicacionesFutbol/TallaM/trasera.json`
- etc.

### **3. Visual Calibration Tool (Mejorado)**
```bash
python -m alignpress_v2.tools.calibration_tool
```
**Herramienta de calibración visual con detección robusta:**

**Mejoras implementadas:**
- ✅ **Detección multi-estrategia**: Múltiples algoritmos para mayor precisión
- ✅ **Compatibilidad OpenCV**: Soporte para versiones 4.x y anteriores
- ✅ **Preprocesamiento de imagen**: Mejora de contraste automática
- ✅ **Detección automática de tamaño**: Prueba diferentes configuraciones de patrón
- ✅ **Logging detallado**: Feedback específico para debugging
- ✅ **Guardado mejorado**: Sin errores de serialización JSON

**Tipos de patrones soportados:**
- **Chessboard**: Detección robusta con múltiples tamaños
- **ArUco Markers**: Compatibilidad con múltiples diccionarios

**Problemas solucionados:**
- ❌ Error "pylimage doesn't exist" → ✅ Gestión correcta de referencias
- ❌ Falla detección con iluminación variable → ✅ Múltiples estrategias
- ❌ Error JSON serialization → ✅ Conversión de tipos correcta

### **4. Detection Simulator**
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

### **1. Configuración Inicial con Workflow Directo (v2.3.0)**
1. **Abrir Configuration Designer**: `python -m alignpress_v2.tools.config_designer`
2. **Nueva Configuración**: Crear "TuProyecto/TallaM/delantera"
3. **Cargar imagen**: Foto de la prenda donde van los logos
4. **Cargar calibración**: Factor mm/pixel para medidas exactas
5. **Agregar logos con flujo directo**:
   - Click "Agregar Logo" → Se abre selector de archivo automáticamente
   - Seleccionar PNG/JPG del logo → Logo aparece listo para posicionar
   - Drag & Drop en imagen → Coordenadas en tiempo real en panel
   - Al soltar → Logo confirmado automáticamente en lista
6. **Editar posiciones precisas**: Click en lista → Arrastrar o usar campos numéricos
7. **Guardar configuración**: Archivo JSON con estructura jerárquica

### **2. Desarrollo y Testing**
1. Usar Detection Simulator con imágenes de prueba
2. Ajustar parámetros basándose en resultados de debug
3. Iterar hasta lograr precisión deseada
4. **Flujo optimizado**: De 4+ clicks a 1 click por logo

### **3. Producción**
1. Ejecutar Integration Tests para validar sistema
2. Usar UI principal para operación
3. Monitorear métricas y logs
4. **Workflow directo** permite configuración rápida en producción

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

### **v2.4.0 - UI Intuitiva para Presets Jerárquicos**
- 🎯 **Nueva UI "📋 Configuración de Preset"**: Interfaz simplificada y clara
- ✅ **Dropdowns inteligentes**: Se llenan automáticamente con opciones existentes
- ✅ **Botones "+ Nuevo"**: Crear diseños, tallas y partes fácilmente
- ✅ **Vista previa de ruta**: Ver exactamente dónde se guardará el preset
- ✅ **Carga automática**: Seleccionar preset existente carga logos automáticamente
- ✅ **Validación inteligente**: Confirmación de sobrescritura y creación de directorios
- ✅ **Workflow step-by-step**: Diseño → Talla → Parte → Configurar → Guardar
- ✅ **Retroalimentación visual**: Estados claros con colores (verde=listo, naranja=falta)

### **v2.3.0 - Workflow Simplificado "Cargar Logo"**
- 🎯 **UI minimalista**: Solo "📂 Cargar Logo" + "✅ Confirmar Logo" + Lista
- ✅ **Workflow simplificado**: Cargar → Posicionar → Confirmar → Aparece en lista
- ✅ **Edición por click**: Click en nombre en lista para editar
- ✅ **Sin botones innecesarios**: Eliminados "Agregar", "Eliminar", "Duplicar"
- ✅ **Panel unificado**: "Posición y Tamaño" para todas las operaciones

### **v2.2.0 - Workflow Template-First y UX Mejorado**
- ✅ Template-First workflow revolucionario con separación clara de conceptos
- ✅ UX híbrido visual + numérico con sincronización bidireccional
- ✅ Sistema de estados mejorado y feedback instantáneo
- ✅ Eliminación de sección "Información del Estilo" obsoleta

### **v2.1.0 - Sistema Jerárquico y Calibración Mejorada**
- ✅ Sistema de configuración jerárquico: Diseño/Talla/Parte
- ✅ Visual Calibration Tool con detección multi-estrategia
- ✅ Configuration Designer con template workflow

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