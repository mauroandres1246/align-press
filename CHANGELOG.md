# Changelog - AlignPress

## [2.4.0] - 2024-09-26 - UI Intuitiva para Presets Jerárquicos

### 🎯 **NUEVA UI INTUITIVA PARA CONFIGURACIÓN DE PRESETS**

#### **UI Simplificada y Clara**
- ✅ **Panel "📋 Configuración de Preset"** - Título claro y iconos
- ✅ **Dropdowns inteligentes** - Se llenan automáticamente con opciones existentes
- ✅ **Botones "+ Nuevo"** - Crear categorías nuevas fácilmente
- ✅ **Vista previa de ruta** - Ves exactamente dónde se guardará el preset
- ✅ **Workflow step-by-step** - Diseño → Talla → Parte → Guardar

#### **Dropdowns Inteligentes**
```
Diseño:  [ComunicacionesFutbol ▼] [+ Nuevo]
         ↑ Se llena con diseños existentes

Talla:   [TallaM ▼] [+ Nueva]
         ↑ Se actualiza según diseño seleccionado

Parte:   [delantera ▼] [+ Nueva]
         ↑ Se actualiza según talla seleccionada
```

#### **Vista Previa Inteligente**
- 💾 **Falta seleccionar**: Diseño, Talla (naranja)
- 💾 **Se guardará en**: configs/ComunicacionesFutbol/TallaM/delantera.json (verde)

#### **Acciones Simplificadas**
- 📂 **Interactive Preset Loading** - Navegador de archivos para cargar presets con población automática de UI
- 🎯 **Visual Logo Editing** - Click en logo de lista para editarlo + drag-to-move en imagen
- 📊 **Smart Dropdown Population** - Dropdowns se auto-llenan con estructura existente
- 🎮 **Dual Position Control** - Control visual (drag) + numérico (campos) sincronizados
- 📂 **Cargar Preset** - Carga configuración existente automáticamente
- 💾 **Guardar Preset** - Guarda en estructura jerárquica automáticamente

### 🔧 **MEJORAS TÉCNICAS**

#### **Sistema de Escaneado Automático**
- ✅ `_scan_existing_presets()` - Escanea configs/ para opciones disponibles
- ✅ `_update_design_options()` - Actualiza dropdown con diseños existentes
- ✅ `_update_size_options()` - Filtra tallas según diseño seleccionado
- ✅ `_update_part_options()` - Filtra partes según talla seleccionada

#### **Creación de Nuevas Categorías**
- ✅ `_new_design()` - Diálogo para crear nuevo diseño
- ✅ `_new_size()` - Diálogo para crear nueva talla
- ✅ `_new_part()` - Diálogo con partes comunes predefinidas

#### **Gestión de Presets Automática**
- ✅ `_load_preset()` - Carga JSON y puebla logos automáticamente
- ✅ `_save_preset()` - Guarda en estructura jerárquica con validación
- ✅ **Creación de directorios** automática si no existen
- ✅ **Confirmación de sobrescritura** para presets existentes

#### **Sistema de Edición Visual de Logos (v2.4.0)**
- ✅ `_on_logo_selected()` - Click en logo de lista activa modo edición
- ✅ `_on_canvas_drag()` - Arrastrar logos directamente en imagen
- ✅ `_move_logo_to_canvas_position()` - Actualización posición en tiempo real
- ✅ **Highlighting visual** - Logos seleccionados se resaltan en naranja
- ✅ **Sincronización bidireccional** - Campos numéricos ↔ posición visual
- ✅ **Drag-to-move** - Feedback inmediato durante arrastre
- ✅ **Click-to-edit** - Workflow intuitivo de selección

### 🎨 **EXPERIENCIA DE USUARIO MEJORADA**

#### **Workflow Intuitivo**
```
1. 📝 Escribir o seleccionar "ComunicacionesFutbol"
2. 📝 Escribir o seleccionar "TallaM"
3. 📝 Escribir o seleccionar "delantera"
4. 👁️ Ver: "💾 Se guardará en: configs/ComunicacionesFutbol/TallaM/delantera.json"
5. 🖼️ Cargar imagen, calibración, agregar logos...
6. 💾 Click "Guardar Preset" → Se crea estructura automáticamente
```

#### **Retroalimentación Visual**
- 🟢 **Verde**: Ruta completa lista para guardar
- 🟠 **Naranja**: Faltan campos por completar
- ✅ **Estados claros**: "Preset cargado", "Preset guardado"
- 📊 **Contadores**: Muestra cantidad de logos cargados

### 🗂️ **ESTRUCTURA MANTENIDA**

La nueva UI mantiene perfectamente la estructura jerárquica:
```
configs/
├── ComunicacionesFutbol/
│   ├── TallaS/
│   │   ├── delantera.json
│   │   ├── trasera.json
│   │   └── manga_izquierda.json
│   ├── TallaM/
│   └── TallaXL/
└── BarcelonaCamiseta/
    └── ...
```

#### **Partes Predefinidas Comunes**
- ✅ delantera, trasera, manga_izquierda, manga_derecha
- ✅ cuello, dobladillo (opcionales)
- ✅ Personalizada (escribir cualquier nombre)

---

## [2.3.0] - 2024-09-26 - Workflow Directo "Agregar Logo"

### 🚀 **NUEVO WORKFLOW DIRECTO PARA AGREGAR LOGOS**

#### **Flujo Simplificado de Un Solo Paso**
- ✅ **"Agregar Logo"** → Selector de archivo inmediato
- ✅ **Drag & Drop directo** → Sin pasos intermedios
- ✅ **Posicionamiento en tiempo real** → Feedback visual continuo
- ✅ **Auto-confirmación** → Logo aparece automáticamente en lista

#### **Workflow Nuevo vs Anterior**
```
ANTES (Template-First):
1. Click "Agregar Logo"
2. Cargar Template de Logo
3. Posicionar template
4. Confirmar Logo
5. Logo aparece en lista

AHORA (Directo):
1. Click "Agregar Logo" → Logo aparece INMEDIATAMENTE listo para posicionar
2. Drag & Drop → Valores en tiempo real en panel "Posición y Tamaño"
3. Al soltar → Logo confirmado automáticamente en lista
```

#### **Características del Nuevo Flujo**
- ✅ **Selector de archivo integrado**: PNG, JPG, JPEG, BMP, TIFF
- ✅ **Feedback visual en tiempo real**: Overlay semi-transparente durante drag
- ✅ **Panel unificado actualizado**: Coordenadas X,Y y tamaño en tiempo real
- ✅ **Cursor crosshair**: Indicación visual clara de modo posicionamiento
- ✅ **Auto-tamaño inteligente**: Entre 20-50mm según imagen original
- ✅ **Detección automática**: template_matching por defecto
- ✅ **Transición fluida**: De posicionamiento a edición sin interrupciones

### 🎨 **MEJORAS EN UX**

#### **Eliminación de Duplicación de UI**
- ✅ **Panel "Propiedades del Logo" eliminado** completamente
- ✅ **Panel "Posición y Tamaño" unificado** para todos los modos
- ✅ **Estados de edición coherentes**: "template", "logo", "direct_placement", "none"

#### **Feedback Visual Mejorado**
- ✅ **Indicadores dinámicos**: Muestran qué se está editando
- ✅ **Overlay en tiempo real**: Rectangle semi-transparente durante drag
- ✅ **Coordenadas en vivo**: Panel se actualiza mientras se arrastra
- ✅ **Transiciones suaves**: Entre modos de edición

### 🔧 **MEJORAS TÉCNICAS**

#### **Nuevo Sistema de Estados**
- ✅ **`editing_mode: "direct_placement"`**: Nuevo estado para workflow directo
- ✅ **`direct_logo_data`**: Estructura temporal para datos de logo en posicionamiento
- ✅ **Bindings dinámicos**: Canvas eventos se intercambian según modo
- ✅ **Cleanup automático**: Restauración de estado normal post-colocación

#### **Métodos Implementados**
```python
_add_logo()                       # Flujo directo con selector archivo
_start_direct_logo_placement()    # Inicialización de posicionamiento directo
_enable_direct_logo_drag()        # Activación de eventos drag & drop
_on_direct_logo_click/drag/release() # Manejo de eventos de posicionamiento
_update_direct_logo_overlay()     # Feedback visual en tiempo real
_update_position_panel_during_drag() # Actualización panel en vivo
_cleanup_direct_placement()       # Limpieza y restauración estado
_canvas_to_image_coords()         # Conversión coordenadas canvas ↔ imagen
```

#### **Integración con Sistema Unificado**
- ✅ **`_update_unified_position_panel()`**: Soporte para modo direct_placement
- ✅ **`_on_position_changed()`**: Actualizaciones bidireccionales desde campos
- ✅ **`_on_size_changed()`**: Redimensionado en tiempo real durante posicionamiento

### 🐛 **PROBLEMAS SOLUCIONADOS**

| Problema Anterior | Solución Implementada |
|---|---|
| ❌ Workflow de 4+ pasos para agregar logo | ✅ Flujo directo de 1 paso: Agregar → Drag → Listo |
| ❌ Confusión entre templates y logos | ✅ Workflow directo sin conceptos intermedios |
| ❌ Sin feedback visual durante posicionamiento | ✅ Overlay en tiempo real + coordenadas en vivo |
| ❌ Duplicación de paneles UI | ✅ Panel unificado único para todas las operaciones |
| ❌ Pasos manuales de confirmación | ✅ Auto-confirmación al soltar logo |

---

## [2.2.0] - 2024-09-26 - Workflow Template-First y UX Mejorado

### 🎯 **WORKFLOW TEMPLATE-FIRST REVOLUCIONARIO**

#### **Separación Clara de Conceptos**
- ✅ **Template (temporal)**: Herramienta flotante para crear logos
- ✅ **Logo (permanente)**: Elemento confirmado que aparece en lista
- ✅ **Modos distintos**: Creación vs Edición claramente separados

#### **UX Híbrido Visual + Numérico**
- ✅ **Modo Visual**: Drag & drop en tiempo real del template
- ✅ **Modo Preciso**: Campos numéricos con sincronización bidireccional
- ✅ **Feedback instantáneo**: Cambios visuales inmediatos
- ✅ **Estados claros**: Usuario siempre sabe qué está haciendo

### 🎨 **NUEVO WORKFLOW STEP-BY-STEP**

#### **Crear Logo:**
```
1. 📂 Cargar Template → Aparece flotante semi-transparente
2. 🎯 Posicionar → Arrastrar OR escribir coordenadas exactas
3. ✅ Confirmar → Template desaparece, Logo aparece en lista
```

#### **Editar Logo:**
```
1. 📋 Click en lista → Logo se resalta en imagen
2. 📐 Modificar → Campos numéricos O arrastrar en imagen
3. 💾 Cambios automáticos → Sincronización en tiempo real
```

### 🔧 **MEJORAS TÉCNICAS**

#### **Sistema de Estados**
- ✅ **editing_mode**: "template", "logo", "none"
- ✅ **selected_template_id**: Template activo (flotante)
- ✅ **selected_logo_index**: Logo seleccionado de lista
- ✅ **Prevención de conflictos**: Solo un modo activo a la vez

#### **Sincronización Bidireccional**
- ✅ **Drag → Números**: Arrastrar actualiza campos automáticamente
- ✅ **Números → Visual**: Cambiar campos mueve elemento en imagen
- ✅ **Tiempo real**: Sin delay, actualizaciones instantáneas
- ✅ **Anti-recursión**: Sistema previene loops infinitos

#### **UI Simplificada**
- ✅ **Sección obsoleta eliminada**: "Información del Estilo" removida
- ✅ **Panel optimizado**: "➕ Crear Nuevo Logo" enfocado en templates
- ✅ **Instrucciones claras**: Workflow explicado visualmente
- ✅ **Botones contextuales**: Centrar, Confirmar, Cancelar

### 🐛 **BUGS CORREGIDOS**

| Problema | Solución |
|----------|----------|
| ❌ Template vs Logo confuso | ✅ Separación clara de conceptos |
| ❌ Lista no corresponde con imagen | ✅ Sincronización bidireccional |
| ❌ Campos numéricos desconectados | ✅ Actualización en tiempo real |
| ❌ Sin feedback visual claro | ✅ Estados y colores distintivos |
| ❌ Diálogo "Nueva Configuración" cortado | ✅ Tamaño y centrado mejorados |

---

## [2.1.0] - 2024-09-26 - Sistema Jerárquico y Calibración Mejorada

### 🚀 **NUEVAS CARACTERÍSTICAS**

#### **Sistema de Configuración Jerárquico**
- ✅ **Estructura organizada**: `configs/Diseño/Talla/Parte.json`
- ✅ **Configuration Designer mejorado** con selector jerárquico
- ✅ **Templates de logos**: Soporte para PNG transparente como referencia
- ✅ **Configuración por partes**: Delantera, trasera, mangas independientes
- ✅ **Workflow intuitivo**: Cargar template → Posicionar → Confirmar → Guardar

#### **Sistema de Templates Flexibles**
- ✅ **Carga de templates**: PNG transparente del logo exacto
- ✅ **Posicionamiento visual**: Click y drag en la imagen
- ✅ **Reutilización**: Un template por equipo, ajustable por talla
- ✅ **Metadata automática**: Tamaño, posición y ROI generados automáticamente

### 🔧 **MEJORAS TÉCNICAS**

#### **Configuration Designer**
- ✅ **Bug fix arrastre**: Eliminados múltiples puntos en drag
- ✅ **Gestión de imágenes mejorada**: Referencias correctas para evitar "pylimage doesn't exist"
- ✅ **Validación de entrada**: Verificación de imágenes vacías
- ✅ **Feedback mejorado**: Mensajes informativos con resolución y estado

#### **Visual Calibration Tool**
- ✅ **Detección multi-estrategia**: Múltiples algoritmos para mayor precisión
- ✅ **Compatibilidad OpenCV**: Soporte para versiones 4.x y anteriores
- ✅ **Logging detallado**: Feedback específico para debugging
- ✅ **Serialización JSON corregida**: Conversión correcta de tipos NumPy

#### **Launcher de Herramientas**
- ✅ **Bug fix argumentos**: Conflicto `--calibration` resuelto → `--calibration-file`

### 🐛 **BUGS CORREGIDOS**

| Problema | Solución |
|----------|----------|
| ❌ Configuration Designer genera múltiples puntos al arrastrar | ✅ Detección de drag con threshold de distancia |
| ❌ Error "pylimage doesn't exist" al cargar imágenes | ✅ Gestión correcta de referencias PhotoImage |
| ❌ Calibration tool no detecta chessboard | ✅ Múltiples estrategias de detección |
| ❌ Error JSON serialization en calibración | ✅ Conversión explícita de tipos NumPy |
| ❌ Conflicto `--calibration` en launcher | ✅ Renombrado a `--calibration-file` |
| ❌ ArUco detection con OpenCV 4.x | ✅ Compatibilidad con versiones nuevas y viejas |

---

## [2.0.0] - 2024-09-25 - Major Architecture Overhaul

### 🚀 **Nueva Arquitectura CustomTkinter/MVC**
- **BREAKING CHANGE**: Arquitectura principal migrada de PySide6/MVVM a CustomTkinter/MVC
- Nuevo sistema de eventos desacoplado con Event Bus
- Gestión de estado centralizado con StateManager
- Hardware Abstraction Layer (HAL) para múltiples interfaces

### ✨ **Nuevas Funcionalidades**
- **Configuration Designer**: Herramienta GUI para crear configuraciones visualmente
- **Detection Simulator**: Simulador completo para desarrollo sin hardware
- **Multi-logo workflow**: Soporte nativo para prendas con múltiples logos
- **Variant system**: Sistema automático de ajustes por talla
- **Development Tools Launcher**: Menú interactivo para herramientas de desarrollo

### 🛠️ **Configuración Unificada**
- Sistema de configuración unificado con dataclasses
- Migración automática de configuraciones v1 a v2
- Exportación a múltiples formatos (YAML, JSON)
- Validación de esquemas integrada

### 🎨 **Nueva Interfaz de Usuario**
- UI moderna con CustomTkinter
- Viewport con overlays en tiempo real
- Panel de control con métricas dinámicas
- Atajos de teclado mejorados (Space, F11, S, Escape)
- Fallback automático a Tkinter estándar

### 🔧 **Herramientas de Desarrollo**
- Simulador de detección con imágenes estáticas
- Generador automático de imágenes de debug
- Métricas de performance integradas
- Workflow completo de ejemplo (camisola de fútbol)
- Tests de integración automatizados

### 📊 **Casos de Uso Documentados**
- **Camisola de comunicaciones**: Ejemplo completo con 3 logos
- **Variantes de talla**: XS, S, M, L, XL, XXL con ajustes automáticos
- **Flujo de desarrollo**: Configuración → Testing → Producción

### 🏗️ **Arquitectura Técnica**
```
alignpress_v2/
├── config/          # Configuración unificada
├── controller/      # MVC + Event Bus
├── services/        # Lógica de negocio
├── infrastructure/  # Hardware abstraction
├── ui/             # CustomTkinter components
└── tools/          # Development utilities
```

### 📦 **Nuevas Dependencias**
- `customtkinter>=5.2` - UI moderna
- `pillow>=10.0` - Procesamiento de imágenes (opcional)
- Compatibilidad mantenida con `PySide6>=6.7` para UI legacy

### 🚧 **Migración v1 → v2**
- ConfigManager con migración automática
- Comandos de ejecución actualizados
- Documentación completamente reescrita
- Guía de migración incluida

### 📝 **Comandos Actualizados**
```bash
# v2 (Principal)
python run_alignpress_v2.py
python dev_tools_launcher.py
python example_camisola_workflow.py

# v1 (Legacy - compatibilidad)
python -m scripts.run_ui --config config/app.yaml
```

### ✅ **Testing**
- Suite completa de tests de integración
- Validador de arquitectura automático
- Tests de componentes UI
- Simulación sin hardware para desarrollo

---

## [1.x] - Legacy PySide6/MVVM Architecture

### Funcionalidades Legacy (mantenidas para compatibilidad):
- UI PySide6 con wizard de configuración
- Sistema de planchas, estilos y variantes
- Detección con overlay fantasma
- Logging y job cards detallados
- Procesamiento headless de datasets

### Archivos Legacy:
- `alignpress/` - Implementación original
- `scripts/run_ui.py` - Launcher PySide6
- `config/app.yaml` - Configuración v1

---

## Migration Notes

### Para usuarios existentes:
1. **Backup**: Se creó `README_legacy_backup.md` con documentación v1
2. **Compatibilidad**: Los comandos v1 siguen funcionando
3. **Migración**: ConfigManager migra automáticamente configuraciones
4. **Nuevas funcionalidades**: Disponibles solo en v2

### Comandos de migración:
```bash
# Validar arquitectura v2
python validate_v2_architecture.py

# Migrar configuración
python example_camisola_workflow.py

# Probar herramientas nuevas
python dev_tools_launcher.py
```

---

**Nota**: La documentación ha sido completamente actualizada para reflejar la arquitectura v2. El sistema legacy permanece disponible para compatibilidad.