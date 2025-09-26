# Ejemplo de Uso - Visual Calibration Tool

## 📏 **Herramienta de Calibración Visual**

La herramienta de calibración te permite obtener el factor de conversión mm/pixel usando imágenes estáticas con patrones de calibración.

## 🚀 **Cómo Usar**

### **Opción 1: Launcher Principal**
```bash
python dev_tools_launcher.py
# Seleccionar opción 1: Visual Calibration Tool
```

### **Opción 2: Directo**
```bash
python run_calibration_tool.py
```

### **Opción 3: Con parámetros**
```bash
python dev_tools_launcher.py --calibration
```

## 📋 **Flujo de Trabajo**

### **1. Preparar Patrón de Calibración**

#### **Opción A: Chessboard (Recomendado)**
- Imprime un patrón de chessboard
- Tamaño sugerido: 7x7 esquinas internas
- Cuadros de 25mm x 25mm

#### **Opción B: ArUco Markers**
- Genera marcadores ArUco
- Diccionario sugerido: DICT_6X6_250
- Tamaño: 20mm x 20mm

### **2. Tomar Foto de Calibración**
```
Consejos para buena calibración:
✅ Buena iluminación uniforme
✅ Patrón completamente visible
✅ Sin sombras sobre el patrón
✅ Cámara perpendicular al patrón
✅ Patrón plano (no doblado)
❌ Evitar reflejos
❌ Evitar desenfoque
```

### **3. Usar la Herramienta**

1. **Cargar Imagen**
   - Clic en "Cargar Imagen de Plancha"
   - Seleccionar foto con patrón

2. **Configurar Patrón**
   - **Chessboard**: Esquinas internas (7x7) y tamaño de cuadro (25mm)
   - **ArUco**: Diccionario y tamaño de marcador (20mm)

3. **Detectar Patrón**
   - Clic en "Detectar Patrón"
   - Verificar overlay visual (puntos rojos, líneas azules)

4. **Calcular Calibración**
   - Clic en "Calcular Calibración"
   - Revisar resultados en panel derecho

5. **Guardar Calibración**
   - Clic en "Guardar Calibración"
   - Exportar como JSON para uso posterior

## 📊 **Interpretación de Resultados**

### **Factor mm/pixel típicos:**
- **0.1 - 0.3**: Cámara cerca de plancha (típico)
- **0.05 - 0.1**: Cámara muy cerca (alta resolución)
- **0.3 - 0.5**: Cámara más lejos (menor resolución)

### **Ejemplo de resultado:**
```
Factor de conversión: 0.2645 mm/pixel

Interpretación:
- Cada pixel = 0.2645 mm en la realidad
- 10 mm = 37.8 pixels
- 100 pixels = 26.45 mm
```

## 📁 **Archivos Generados**

### **Calibración JSON**
```json
{
  "factor_mm_px": 0.2645,
  "timestamp": "2024-09-25T15:30:00",
  "method": "chessboard_visual_tool",
  "pattern_type": "chessboard",
  "pattern_size": [7, 7],
  "source_image": "plancha_calibration.jpg"
}
```

### **Reporte de Calibración**
```
ALIGNPRESS v2 - REPORTE DE CALIBRACIÓN
=====================================

INFORMACIÓN GENERAL:
- Fecha: 2024-09-25 15:30:00
- Método: chessboard_visual_tool
- Factor: 0.2645 mm/pixel

EJEMPLOS DE CONVERSIÓN:
- 10 mm = 37.8 pixels
- 25 mm = 94.5 pixels
- 50 mm = 189.0 pixels
```

## 🔧 **Solución de Problemas**

### **Patrón no detectado**
- ✅ Verificar iluminación
- ✅ Ajustar número de esquinas
- ✅ Revisar que el patrón esté completo
- ✅ Probar con otro tipo de patrón

### **Factor muy alto/bajo**
- ✅ Verificar tamaño real del patrón
- ✅ Confirmar distancia de cámara
- ✅ Revisar resolución de imagen

### **Calibración inconsistente**
- ✅ Tomar varias fotos y promediar
- ✅ Verificar que patrón esté plano
- ✅ Mejorar condiciones de iluminación

## 🎯 **Siguiente Paso: Configuration Designer**

Una vez que tengas la calibración:

1. **Usar en Configuration Designer**
   ```bash
   python dev_tools_launcher.py
   # Opción 2: Configuration Designer
   ```

2. **Cargar calibración guardada**
3. **Colocar logos usando coordenadas reales en mm**
4. **Generar configuración completa**

## 📋 **Patrones de Calibración**

### **Generar Chessboard Online**
- Buscar "chessboard pattern generator"
- Configurar: 8x8 cuadros (7x7 esquinas internas)
- Tamaño: 25mm por cuadro
- Imprimir en papel blanco

### **Generar ArUco Online**
- Buscar "aruco marker generator"
- Diccionario: DICT_6X6_250
- IDs: 0, 1, 2, 3
- Tamaño: 20mm

¡Con esta herramienta ya puedes calibrar tu plancha de manera precisa y visual!