# Ejemplo de Uso - Configuration Designer Enhanced

## 🎨 **Configuration Designer con Calibración Visual**

El Configuration Designer mejorado permite crear configuraciones de logos usando datos de calibración reales para colocación precisa en milímetros.

## 🚀 **Flujo de Trabajo Completo**

### **1. Preparación de Archivos**

```bash
# Estructura recomendada
test_images/
├── calibration_platen.jpg      # Imagen de plancha con patrón
├── comunicaciones_m.jpg        # Imagen de prenda talla M
├── comunicaciones_s.jpg        # Imagen de prenda talla S
└── comunicaciones_l.jpg        # Imagen de prenda talla L

calibrations/
└── platen_calibration.json     # Archivo de calibración generado

configs/
└── comunicaciones_config.yaml  # Configuración final
```

### **2. PASO 1: Calibrar Plancha**

```bash
# Abrir herramienta de calibración
python dev_tools_launcher.py --calibration

# O directamente
python run_calibration_tool.py
```

**Proceso de Calibración:**
1. Cargar imagen de plancha con patrón (chessboard o ArUco)
2. Detectar patrón automáticamente
3. Calcular factor mm/pixel
4. Guardar calibración como JSON

**Resultado esperado:**
```json
{
  "factor_mm_px": 0.2645,
  "timestamp": "2024-09-25T15:30:00",
  "method": "chessboard_visual_tool",
  "pattern_type": "chessboard",
  "pattern_size": [7, 7],
  "source_image": "calibration_platen.jpg"
}
```

### **3. PASO 2: Diseñar Configuración**

```bash
# Abrir Configuration Designer
python dev_tools_launcher.py --config-designer
```

**Flujo en Configuration Designer:**

#### **A. Cargar Calibración**
1. `Archivo → Cargar Calibración`
2. Seleccionar `platen_calibration.json`
3. Verificar estado: **"Calibrado ✓"** con factor mm/pixel

#### **B. Cargar Imagen de Prenda**
1. `Archivo → Cargar Imagen de Prenda`
2. Seleccionar `comunicaciones_m.jpg` (talla M como base)
3. Imagen se ajusta automáticamente al canvas

#### **C. Crear Estilo Base**
1. Completar información del estilo:
   - **ID:** `comunicaciones_2024`
   - **Nombre:** `Camisola de Comunicaciones 2024`

#### **D. Agregar Logos**

**Logo 1: Escudo Principal**
```
ID: escudo_principal
Nombre: Escudo del Club
Posición X: 120.0 mm (centro del pecho)
Posición Y: 80.0 mm (altura del pecho)
Tolerancia: 5.0 mm
Detector: contour
```

**Logo 2: Sponsor Principal**
```
ID: sponsor_principal
Nombre: Sponsor Principal
Posición X: 120.0 mm
Posición Y: 140.0 mm (debajo del escudo)
Tolerancia: 3.0 mm
Detector: template
```

**Logo 3: Sponsor Secundario**
```
ID: sponsor_manga
Nombre: Sponsor Manga
Posición X: 180.0 mm (manga derecha)
Posición Y: 100.0 mm
Tolerancia: 4.0 mm
Detector: contour
```

#### **E. Colocación Visual**
1. Seleccionar logo en lista
2. **Hacer clic en la imagen** donde debe ir el logo
3. El sistema convierte pixels → mm automáticamente
4. ROI se ajusta automáticamente alrededor de la posición
5. Ver **marcadores rojos** para logo seleccionado, **azules** para otros

### **4. PASO 3: Generar Variantes de Talla**

1. `Herramientas → Generar Variantes de Talla`
2. Seleccionar tallas: **S, M, L, XL**
3. Ajustar factores de escala:
   - S: 0.92 (logos 8% más pequeños/cerca)
   - M: 1.00 (talla base)
   - L: 1.08 (logos 8% más grandes/separados)
   - XL: 1.15 (logos 15% más grandes/separados)
4. **Generar** → Crea 4 variantes automáticamente

### **5. PASO 4: Validar y Probar**

#### **Vista Previa de ROIs**
```
Herramientas → Vista Previa de ROIs
```
- Muestra todas las ROIs superpuestas en la imagen
- Verificar que no se solapan
- Confirmar posiciones correctas

#### **Probar Detección**
```
Herramientas → Probar Detección
```
- Ejecuta simulación de detección en tiempo real
- Muestra resultados por logo:
  - ✅/❌ Detectado
  - Confianza (0.0-1.0)
  - Posición encontrada vs esperada
- **Ver Debug Image** con overlays de detección

#### **Exportar Debug Image**
```
Herramientas → Exportar Debug Image
```
- Genera imagen con ROIs y marcadores dibujados
- Útil para documentación y verificación visual
- Formato: JPG/PNG con overlays OpenCV

### **6. PASO 5: Guardar Configuración**

```
Archivo → Guardar Configuración → comunicaciones_config.yaml
```

**Estructura generada:**
```yaml
version: "2.0"
active_style_id: "comunicaciones_2024"

library:
  styles:
    - id: "comunicaciones_2024"
      name: "Camisola de Comunicaciones 2024"
      logos:
        - id: "escudo_principal"
          name: "Escudo del Club"
          position_mm: {x: 120.0, y: 80.0}
          tolerance_mm: 5.0
          detector_type: "contour"
          roi: {x: 100.0, y: 60.0, width: 40.0, height: 40.0}

  variants:
    - id: "comunicaciones_2024_s"
      name: "Camisola de Comunicaciones 2024 - S"
      base_style_id: "comunicaciones_2024"
      size_category: "s"
      logos: [...] # Logos escalados con factor 0.92
```

## 📊 **Funcionalidades Avanzadas**

### **Calibración Integrada**
- **Factor mm/pixel automático:** Convierte clicks en coordenadas reales
- **Indicador visual:** Estado de calibración siempre visible
- **Múltiples formatos:** Chessboard y ArUco soportados

### **Colocación Interactiva**
- **Click-to-place:** Clic en imagen actualiza posición en mm
- **ROI automático:** Se centra en posición del logo
- **Visualización en tiempo real:** Marcadores de colores diferenciados

### **Variantes Inteligentes**
- **Escalado proporcional:** Logos y ROIs ajustados automáticamente
- **Factores personalizables:** Control fino por talla
- **Generación masiva:** Múltiples tallas en una operación

### **Testing Integrado**
- **Simulación inmediata:** Probar sin hardware
- **Métricas detalladas:** Confianza, tiempo, posición
- **Debug visual:** Imágenes con overlays de detección

## 🎯 **Siguiente Paso: Producción**

Una vez validada la configuración:

```bash
# Usar en el simulador principal
python dev_tools_launcher.py --simulator --config comunicaciones_config.yaml --image test_images/comunicaciones_s.jpg

# O integrar en aplicación principal
python run_alignpress_v2.py --config comunicaciones_config.yaml
```

## 💡 **Consejos de Uso**

### **Para Mejores Resultados:**
- ✅ Usar imagen de prenda **bien iluminada** y **plana**
- ✅ Calibrar con **la misma cámara** que usarás en producción
- ✅ Colocar logos con **márgenes suficientes** entre ROIs
- ✅ Probar con **múltiples imágenes** antes de producción
- ✅ Guardar **backups de calibración** para diferentes setups

### **Flujo de Trabajo Recomendado:**
1. **Calibración una vez** por setup de cámara
2. **Configuración base** con talla M
3. **Variantes automáticas** para otras tallas
4. **Testing exhaustivo** con imágenes reales
5. **Ajuste fino** basado en resultados de testing

¡Con este flujo ya puedes crear configuraciones precisas y testearlas completamente antes de implementar en hardware!