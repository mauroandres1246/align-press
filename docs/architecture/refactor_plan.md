# AlignPress v2 Refactor Plan

## 1. Visión Arquitectónica

### 1.1 Problema Actual
- **Complejidad excesiva**: MVVM + PySide6 introduce capas innecesarias para el caso de uso actual.
- **Fragmentación**: Configuración distribuida en múltiples JSONs dificulta la gestión y genera inconsistencias.
- **Performance limitada**: La pila actual es demasiado pesada para ejecutarse con fluidez en Raspberry Pi.
- **UX confusa**: La interfaz con múltiples pestañas y modos oculta información crítica para el operador.

### 1.2 Objetivo de la Nueva Arquitectura
Construir un sistema **simple, visual y eficiente** que un operador pueda usar con mínimo entrenamiento, optimizado desde el inicio para hardware embebido (Raspberry Pi).

### 1.3 Principios de Diseño
1. **KISS (Keep It Simple)**: Mantener la complejidad en el mínimo necesario.
2. **YAGNI (You Aren't Gonna Need It)**: Evitar sobre-diseños y funcionalidades anticipadas.
3. **DRY (Don't Repeat Yourself)**: Reutilizar el core existente evitando duplicación.
4. **Visible State**: Garantizar que todo el estado relevante sea visible en pantalla.
5. **Hardware-First**: Diseñar siempre con Raspberry Pi como plataforma objetivo.

## 2. Decisiones Arquitectónicas Clave

### 2.1 Stack Tecnológico

| Componente | Actual | Propuesto | Justificación |
|------------|--------|-----------|---------------|
| **UI Framework** | PySide6 (Qt) | CustomTkinter | 10x más ligero, nativo en Raspberry Pi, theming moderno incluido |
| **Patrón UI** | MVVM | MVC simple | Menos capas de abstracción, más directo para iterar |
| **Configuración** | Múltiples JSONs | Single Source of Truth (1 JSON) | Gestión simplificada y versionado único |
| **Estado** | Distribuido | Centralizado | Control total del estado desde un único punto |
| **Threading** | QThread complejo | `threading` estándar | Suficiente para la carga actual y más fácil de mantener |

### 2.2 Patrón Arquitectónico General

```
┌─────────────────────────────────────────┐
│           UI Layer (Thin)               │
│        CustomTkinter GUI               │
│     Single Screen, Visual First        │
└────────────────┬────────────────────────┘
                │ Events & Commands
                ▼
┌─────────────────────────────────────────┐
│         Controller Layer                │
│   Estado Central + Orquestación         │
│    - AppController (singleton)          │
│    - StateManager                       │
│    - EventBus                           │
└────────────────┬────────────────────────┘
                │ Calls
                ▼
┌─────────────────────────────────────────┐
│         Business Logic Layer            │
│     (Reutilizar Core Existente)         │
│    - DetectionService                   │
│    - CalibrationService                 │
│    - CompositionService                 │
└────────────────┬────────────────────────┘
                │ Uses
                ▼
┌─────────────────────────────────────────┐
│          Infrastructure Layer           │
│    - ConfigManager (single JSON)        │
│    - HardwareAbstraction (GPIO/Arduino) │
│    - DataPersistence (JobCards)         │
└─────────────────────────────────────────┘
```

### 2.3 Flujo de Datos

```
User Input → UI Event → Controller → Service → Result → State Update → UI Update
                             ↓
                        Side Effects
                     (Hardware, Logs)
```

**Unidireccional**: Los datos fluyen en una dirección clara para facilitar el debugging y evitar loops inesperados.

## 3. Componentes Principales

### 3.1 UI Layer (Nueva, Simplificada)

**Responsabilidades:**
- Renderizar el estado actual.
- Capturar eventos de usuario.
- Mostrar feedback visual inmediato.

**No hace:**
- Lógica de negocio.
- Cálculos complejos.
- Gestión de estado.

**Estructura sugerida:**
```
ui/
├── main_window.py        # Ventana principal
├── components/
│   ├── viewport.py       # Canvas con overlay
│   ├── control_panel.py  # Panel de métricas
│   └── status_bar.py     # Barra de estado
└── dialogs/
    ├── calibration.py    # Diálogo de calibración
    └── config.py         # Diálogo de configuración
```

### 3.2 Controller Layer (Nueva)

**AppController (Singleton)**
- Orquesta toda la aplicación.
- Mantiene el estado centralizado.
- Coordina UI y servicios.

**StateManager**
```python
class AppState:
    # Estado completo en un lugar
    current_mode: str  # "IDLE", "DETECTING", "CALIBRATING"
    current_logo: int
    detection_results: List[DetectionResult]
    configuration: Config
    hardware_status: HardwareStatus
```

**EventBus**
- Comunicación desacoplada entre componentes.
- Eventos tipados (sin strings mágicos).
- Permite extensiones futuras.

### 3.3 Business Logic Layer (Reutilizar)

**Estrategia**: Envolver el core existente en servicios simples.

```python
class DetectionService:
    """Wrapper simplificado del LogoAligner existente"""
    def detect(image, config) -> DetectionResult

class CalibrationService:
    """Wrapper del CalibrationService existente"""
    def calibrate(image) -> CalibrationResult

class CompositionService:
    """Wrapper de Composition existente"""
    def generate_preset(platen, style, variant) -> Preset
```

### 3.4 Infrastructure Layer

**ConfigManager**
```python
class ConfigManager:
    # Punto único de acceso a la configuración
    def load() -> Config
    def save(config: Config)
    def validate(config: Config) -> bool
    def migrate(old_config: dict) -> Config  # Para compatibilidad
```

**HardwareAbstraction**
```python
class HardwareInterface(ABC):
    def set_led(color: str)
    def get_button_state() -> bool

class MockHardware(HardwareInterface)   # Para desarrollo
class GPIOHardware(HardwareInterface)   # Para Raspberry Pi
class ArduinoHardware(HardwareInterface)  # Para Arduino
```

## 4. Modelo de Datos

### 4.1 Configuración Unificada

```yaml
# Estructura conceptual (implementar en JSON)
AlignPressConfig:
  version: str
  system:
    language: str
    units: str
    theme: str

  calibration:
    current:
      factor_mm_px: float
      timestamp: datetime
      method: str
    settings:
      pattern_type: str
      pattern_size: tuple

  hardware:
    camera:
      device_id: int
      resolution: tuple
      fps: int
    gpio:
      enabled: bool
      pins: dict
    arduino:
      enabled: bool
      port: str

  library:  # Biblioteca de elementos reutilizables
    platens: List[Platen]
    styles: List[Style]
    variants: List[Variant]

  session:  # Estado actual de trabajo
    active_platen_id: str
    active_style_id: str
    active_variant_id: str
    operator_id: str
```

### 4.2 Modelo de Dominio (Simplificado)

```python
@dataclass
class Platen:
    id: str
    name: str
    size_mm: Tuple[float, float]

@dataclass
class Logo:
    id: str
    name: str
    position_mm: Point
    tolerance_mm: float
    detector_type: str
    roi: Rectangle

@dataclass
class Style:
    id: str
    name: str
    logos: List[Logo]

@dataclass
class Variant:
    id: str
    style_id: str
    size: str  # "XS", "S", "M", "L", "XL"
    scale_factor: float
    offsets: Dict[str, Point]
```

## 5. Estrategia de Migración

### 5.1 Fases

**Fase 0: Preparación (1 semana)**
- Analizar el core existente.
- Identificar qué reutilizar vs. reescribir.
- Crear adaptadores para el core.
- Definir esquema de configuración unificada.

**Fase 1: Prototipo UI (1 semana)**
- UI minimalista con CustomTkinter.
- Services mock sin core real.
- Validación de UX con usuarios.
- Ajustes según feedback.

**Fase 2: Integración Core (1 semana)**
- Conectar servicios reales.
- Implementar migrador de configuración.
- Testing de integración.
- Validación en diferentes plataformas.

**Fase 3: Hardware (1 semana)**
- Implementar HAL (Hardware Abstraction Layer).
- Testing en Raspberry Pi.
- Integración GPIO/Arduino.
- Optimizaciones de performance.

**Fase 4: Producción (1 semana)**
- Migración de datos existentes.
- Documentación y capacitación.
- Scripts de deployment.
- Monitoreo y métricas.

### 5.2 Estrategia de Coexistencia

Durante la migración, ambas versiones pueden coexistir:

```
align-press/
├── alignpress/         # Core actual (se mantiene)
├── alignpress_v2/      # Nueva arquitectura
│   ├── ui/             # Nueva UI
│   ├── controller/     # Nuevo controller
│   ├── services/       # Wrappers del core
│   └── config/         # Config unificada
├── migration/          # Scripts de migración
└── tests/              # Tests para ambas versiones
```

## 6. Consideraciones de Performance

### 6.1 Optimizaciones para Raspberry Pi
1. **Lazy Loading** de componentes pesados.
2. **Frame Skipping**: procesar cada *N* frames si el FPS cae debajo del objetivo.
3. **ROI Processing**: procesar solo la región de interés.
4. **Caching** de detecciones para imágenes estáticas.
5. **Threading dedicado**: separar UI thread del processing thread.

### 6.2 Métricas Objetivo

| Métrica  | Valor Objetivo | Condición |
|----------|----------------|-----------|
| FPS      | ≥ 25           | En Raspberry Pi 4 |
| RAM      | < 500 MB       | Con dataset activo |
| CPU      | < 60%          | En procesamiento continuo |
| Latencia | < 100 ms       | Detección a feedback |
| Startup  | < 5 s          | Tiempo hasta UI funcional |

## 7. Testing Strategy

### 7.1 Niveles de Testing
1. **Unit Tests**: Services y lógica de negocio.
2. **Integration Tests**: Controller + Services.
3. **UI Tests**: Interacciones de usuario (manual y automatizado limitado).
4. **Hardware Tests**: GPIO/Arduino en hardware real.
5. **Performance Tests**: Benchmarks en Raspberry Pi.

### 7.2 Ambientes de Testing
- **Local (Mac/Linux)**: Desarrollo y unit tests.
- **WSL**: Integration testing en ambiente Linux.
- **Raspberry Pi**: Testing de hardware y performance.
- **CI/CD**: GitHub Actions para tests automáticos.

## 8. Decisiones Pendientes

1. **Modo de operación de logos**: Secuencial vs. simultáneo. Recomendación: secuencial.
2. **Persistencia de datos**: JSON local vs. SQLite vs. cloud. Recomendación: iniciar con JSON y migrar a SQLite si escala.
3. **Configurabilidad UI**: Layout fijo vs. paneles configurables vs. temas personalizables. Recomendación: layout fijo + temas predefinidos.
4. **Estrategia de actualización**: Manual vs. auto-update vs. gestión centralizada. Recomendación: manual inicialmente.

## 9. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Limitaciones de CustomTkinter | Baja | Alto | Plan B con Kivy |
| Performance insuficiente en Raspberry Pi | Media | Alto | Optimizaciones desde el día 1 |
| Resistencia al cambio | Media | Medio | Involucrar operadores en el proceso |
| Bugs en migración | Alta | Bajo | Tests exhaustivos y plan de rollback |

## 10. Próximos Pasos

### Inmediatos (Esta semana)
1. ✅ Validar plan con el equipo.
2. ⬜ Definir decisiones pendientes.
3. ⬜ Crear repositorio/branch para v2.
4. ⬜ Definir esquema JSON final.

### Próxima semana
1. ⬜ Mockups detallados de la UI.
2. ⬜ Implementar prototipo visual (CustomTkinter).
3. ⬜ Validar con ≥3 usuarios reales.
4. ⬜ Iterar según feedback.

### En 2 semanas
1. ⬜ Integrar core real.
2. ⬜ Testing multiplataforma.
3. ⬜ Documentación técnica.

---

**Nota**: Documento vivo que se actualizará conforme el equipo avance en la implementación de AlignPress v2.
