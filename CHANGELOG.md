# Changelog - AlignPress

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