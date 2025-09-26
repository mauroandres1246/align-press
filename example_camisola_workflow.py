#!/usr/bin/env python3
"""
Ejemplo Completo: Configuración de Camisola de Comunicaciones

Demuestra el flujo completo de configuración, almacenamiento y detección
para una camisola de fútbol con múltiples logos y variantes de talla.
"""
import sys
import os
from pathlib import Path

# Add alignpress_v2 to Python path
sys.path.insert(0, os.path.abspath('.'))

from alignpress_v2.config.models import (
    AlignPressConfig, Style, Logo, Variant, Point, Rectangle,
    LibraryData, SessionData, SystemConfig, HardwareConfig,
    CalibrationData, CameraSettings, GPIOSettings, ArduinoSettings
)
from alignpress_v2.config.config_manager import ConfigManager
from alignpress_v2.tools.detection_simulator import DetectionSimulator
from datetime import datetime
import json


def create_comunicaciones_config():
    """Crear configuración completa para camisola de comunicaciones"""

    print("🎽 Creando configuración para Camisola de Comunicaciones...")

    # 1. Crear logos individuales
    escudo_principal = Logo(
        id="escudo_comunicaciones",
        name="Escudo Comunicaciones F.C.",
        position_mm=Point(100.0, 80.0),  # Centro-pecho
        tolerance_mm=3.0,
        detector_type="contour",
        roi=Rectangle(70, 50, 60, 60),
        detector_params={
            "min_area": 800,
            "max_area": 4000,
            "threshold_type": "adaptive",
            "contour_mode": "external"
        },
        instructions="Escudo principal del equipo - centro del pecho"
    )

    sponsor_movistar = Logo(
        id="sponsor_movistar",
        name="Logo Movistar",
        position_mm=Point(50.0, 120.0),  # Pecho izquierdo
        tolerance_mm=2.5,
        detector_type="template",
        roi=Rectangle(30, 100, 40, 25),
        detector_params={
            "template_path": "templates/movistar_logo.png",
            "match_threshold": 0.75,
            "method": "cv2.TM_CCOEFF_NORMED"
        },
        instructions="Sponsor principal - pecho izquierdo"
    )

    sponsor_adidas = Logo(
        id="sponsor_adidas",
        name="Logo Adidas",
        position_mm=Point(150.0, 120.0),  # Pecho derecho
        tolerance_mm=2.5,
        detector_type="contour",
        roi=Rectangle(130, 100, 40, 25),
        detector_params={
            "min_area": 300,
            "max_area": 1500,
            "aspect_ratio_min": 1.2,
            "aspect_ratio_max": 2.5
        },
        instructions="Sponsor técnico - pecho derecho"
    )

    # 2. Crear el estilo base (talla M como referencia)
    comunicaciones_style = Style(
        id="comunicaciones_2024",
        name="Camisola Comunicaciones Temporada 2024",
        logos=[escudo_principal, sponsor_movistar, sponsor_adidas]
    )

    # 3. Crear variantes por talla
    variantes_talla = [
        Variant(
            id="comunicaciones_2024_xs",
            style_id="comunicaciones_2024",
            size="XS",
            scale_factor=0.80,
            offsets={
                "escudo_comunicaciones": Point(-12.0, -8.0),
                "sponsor_movistar": Point(-8.0, -5.0),
                "sponsor_adidas": Point(8.0, -5.0)
            }
        ),
        Variant(
            id="comunicaciones_2024_s",
            style_id="comunicaciones_2024",
            size="S",
            scale_factor=0.90,
            offsets={
                "escudo_comunicaciones": Point(-8.0, -5.0),
                "sponsor_movistar": Point(-5.0, -3.0),
                "sponsor_adidas": Point(5.0, -3.0)
            }
        ),
        Variant(
            id="comunicaciones_2024_m",
            style_id="comunicaciones_2024",
            size="M",
            scale_factor=1.00,
            offsets={}  # Talla de referencia
        ),
        Variant(
            id="comunicaciones_2024_l",
            style_id="comunicaciones_2024",
            size="L",
            scale_factor=1.10,
            offsets={
                "escudo_comunicaciones": Point(5.0, 3.0),
                "sponsor_movistar": Point(3.0, 2.0),
                "sponsor_adidas": Point(-3.0, 2.0)
            }
        ),
        Variant(
            id="comunicaciones_2024_xl",
            style_id="comunicaciones_2024",
            size="XL",
            scale_factor=1.25,
            offsets={
                "escudo_comunicaciones": Point(12.0, 8.0),
                "sponsor_movistar": Point(8.0, 5.0),
                "sponsor_adidas": Point(-8.0, 5.0)
            }
        ),
        Variant(
            id="comunicaciones_2024_xxl",
            style_id="comunicaciones_2024",
            size="XXL",
            scale_factor=1.40,
            offsets={
                "escudo_comunicaciones": Point(18.0, 12.0),
                "sponsor_movistar": Point(12.0, 8.0),
                "sponsor_adidas": Point(-12.0, 8.0)
            }
        )
    ]

    # 4. Crear configuración completa del sistema
    config = AlignPressConfig(
        version="2.0.0",

        system=SystemConfig(
            language="es",
            units="mm",
            theme="light"
        ),

        calibration=CalibrationData(
            factor_mm_px=0.2645,  # Ejemplo: calibrado para cámara específica
            timestamp=datetime.now(),
            method="chessboard_auto",
            pattern_type="chessboard",
            pattern_size=(7, 7)
        ),

        hardware=HardwareConfig(
            camera=CameraSettings(
                device_id=0,
                resolution=(1920, 1080),
                fps=30
            ),
            gpio=GPIOSettings(
                enabled=True,
                led_pin=18,
                button_pin=19
            ),
            arduino=ArduinoSettings(
                enabled=False,  # No necesario para este setup
                port="",
                baudrate=9600
            )
        ),

        library=LibraryData(
            platens=[],  # Se agregarían según necesidad
            styles=[comunicaciones_style],
            variants=variantes_talla
        ),

        session=SessionData(
            active_platen_id=None,
            active_style_id="comunicaciones_2024",
            active_variant_id="comunicaciones_2024_m",  # Empezar con talla M
            operator_id="operador_produccion"
        )
    )

    print(f"✅ Configuración creada:")
    print(f"   - Estilo: {comunicaciones_style.name}")
    print(f"   - Logos: {len(comunicaciones_style.logos)}")
    print(f"   - Variantes de talla: {len(variantes_talla)}")

    return config


def save_configuration_example(config: AlignPressConfig):
    """Ejemplo de cómo guardar la configuración"""
    print("\n💾 Guardando configuración...")

    # Crear directorio si no existe
    config_dir = Path("configs/examples")
    config_dir.mkdir(parents=True, exist_ok=True)

    # Guardar configuración principal
    config_path = config_dir / "comunicaciones_2024_complete.yaml"
    config_manager = ConfigManager(config_path)
    config_manager.save(config)

    print(f"✅ Configuración guardada en: {config_path}")

    # También guardar solo el estilo como ejemplo
    style_path = config_dir / "comunicaciones_2024_style_only.json"
    style_data = {
        "style": {
            "id": config.library.styles[0].id,
            "name": config.library.styles[0].name,
            "logos": [
                {
                    "id": logo.id,
                    "name": logo.name,
                    "position_mm": {"x": logo.position_mm.x, "y": logo.position_mm.y},
                    "tolerance_mm": logo.tolerance_mm,
                    "detector_type": logo.detector_type,
                    "roi": {
                        "x": logo.roi.x, "y": logo.roi.y,
                        "width": logo.roi.width, "height": logo.roi.height
                    }
                }
                for logo in config.library.styles[0].logos
            ]
        },
        "variants": [
            {
                "id": variant.id,
                "size": variant.size,
                "scale_factor": variant.scale_factor,
                "offsets": {
                    logo_id: {"x": offset.x, "y": offset.y}
                    for logo_id, offset in variant.offsets.items()
                }
            }
            for variant in config.library.variants
        ]
    }

    with open(style_path, 'w', encoding='utf-8') as f:
        json.dump(style_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Estilo exportado como JSON: {style_path}")

    return config_path


def load_and_test_configuration(config_path: Path):
    """Ejemplo de cómo cargar y probar la configuración"""
    print(f"\n📖 Cargando configuración desde: {config_path}")

    # Cargar configuración
    config_manager = ConfigManager(config_path)
    loaded_config = config_manager.load()

    print("✅ Configuración cargada correctamente")
    print(f"   - Versión: {loaded_config.version}")
    print(f"   - Idioma: {loaded_config.system.language}")
    print(f"   - Calibración: {'Disponible' if loaded_config.calibration else 'No disponible'}")
    print(f"   - Estilos disponibles: {len(loaded_config.library.styles)}")
    print(f"   - Variantes disponibles: {len(loaded_config.library.variants)}")

    # Mostrar detalles del estilo activo
    active_style = loaded_config.get_active_style()
    if active_style:
        print(f"\n👕 Estilo activo: {active_style.name}")
        print("   Logos configurados:")
        for i, logo in enumerate(active_style.logos, 1):
            print(f"   {i}. {logo.name}")
            print(f"      - Posición: ({logo.position_mm.x:.1f}, {logo.position_mm.y:.1f}) mm")
            print(f"      - Tolerancia: ±{logo.tolerance_mm} mm")
            print(f"      - Detector: {logo.detector_type}")

    # Mostrar variantes disponibles
    print(f"\n👔 Variantes de talla disponibles:")
    for variant in loaded_config.library.variants:
        offset_count = len(variant.offsets)
        print(f"   - {variant.size}: escala {variant.scale_factor:.2f}, "
              f"{offset_count} ajustes de posición")

    return loaded_config


def simulate_detection_workflow(config: AlignPressConfig):
    """Simular el flujo de detección completo"""
    print(f"\n🔍 Simulando flujo de detección...")

    try:
        # Crear simulador
        simulator = DetectionSimulator()
        print("✅ Simulador de detección inicializado")

        # Obtener estilo activo
        active_style = config.get_active_style()
        if not active_style:
            print("❌ No hay estilo activo configurado")
            return

        # Crear directorio de imágenes de prueba si no existe
        test_images_dir = Path("test_images/comunicaciones_2024")
        test_images_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Para probar la detección, coloca imágenes de camisolas en:")
        print(f"   {test_images_dir.absolute()}")
        print(f"   Formatos soportados: .jpg, .jpeg, .png")

        # Buscar imágenes de prueba
        test_images = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.png"))

        if test_images:
            print(f"🖼️  Encontradas {len(test_images)} imágenes de prueba")

            # Simular detección en la primera imagen
            first_image = test_images[0]
            print(f"🎯 Probando detección en: {first_image.name}")

            # Probar con diferentes tallas
            for variant in config.library.variants[:3]:  # Solo primeras 3 para el ejemplo
                print(f"\n   Probando talla {variant.size}...")

                result = simulator.simulate_garment_detection(
                    first_image,
                    active_style,
                    config,
                    variant_id=variant.id
                )

                success_status = "✅" if result.get('overall_success') else "❌"
                processing_time = result.get('processing_time_ms', 0)
                successful_logos = result.get('successful_logos', 0)
                total_logos = result.get('logo_count', 0)

                print(f"   {success_status} Resultado: {successful_logos}/{total_logos} logos "
                      f"detectados en {processing_time:.1f}ms")

                # Crear imagen de debug para la primera talla
                if variant.size == "M":
                    debug_path = simulator.create_visual_debug_image(first_image, result)
                    if debug_path:
                        print(f"   🖼️  Imagen de debug creada: {debug_path}")

        else:
            print("ℹ️  No se encontraron imágenes de prueba")
            print("   Para probar la detección, agrega imágenes .jpg o .png al directorio de arriba")

    except ImportError:
        print("⚠️  Simulador no disponible (requiere OpenCV y PIL)")
        print("   Para instalar: pip install opencv-python pillow")
    except Exception as e:
        print(f"❌ Error en simulación: {e}")


def demonstrate_variant_calculation():
    """Demostrar cálculos de variantes de talla"""
    print(f"\n📐 Ejemplo de cálculos de variantes:")

    # Posición base (talla M)
    base_position = Point(100.0, 80.0)  # Escudo en talla M
    print(f"   Posición base (M): ({base_position.x}, {base_position.y}) mm")

    # Simular ajustes por talla
    variants_demo = [
        ("S", 0.90, Point(-8.0, -5.0)),
        ("M", 1.00, Point(0.0, 0.0)),
        ("L", 1.10, Point(5.0, 3.0)),
        ("XL", 1.25, Point(12.0, 8.0))
    ]

    print(f"   Ajustes calculados:")
    for size, scale, offset in variants_demo:
        # Calcular posición final
        final_x = (base_position.x * scale) + offset.x
        final_y = (base_position.y * scale) + offset.y

        print(f"   - Talla {size}: ({final_x:.1f}, {final_y:.1f}) mm "
              f"[escala: {scale:.2f}, offset: ({offset.x:+.1f}, {offset.y:+.1f})]")


def main():
    """Función principal del ejemplo"""
    print("=" * 70)
    print("🎽 ALIGNPRESS v2 - EJEMPLO DE CONFIGURACIÓN DE CAMISOLA")
    print("=" * 70)

    try:
        # 1. Crear configuración
        config = create_comunicaciones_config()

        # 2. Guardar configuración
        config_path = save_configuration_example(config)

        # 3. Cargar y verificar configuración
        loaded_config = load_and_test_configuration(config_path)

        # 4. Demostrar cálculos de variantes
        demonstrate_variant_calculation()

        # 5. Simular flujo de detección
        simulate_detection_workflow(loaded_config)

        print(f"\n" + "=" * 70)
        print("🎉 EJEMPLO COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f"\n📝 PRÓXIMOS PASOS SUGERIDOS:")
        print(f"   1. Ejecuta el Configuration Designer:")
        print(f"      python -m alignpress_v2.tools.config_designer")
        print(f"   2. Coloca imágenes de prueba en test_images/comunicaciones_2024/")
        print(f"   3. Ejecuta la UI completa:")
        print(f"      python run_alignpress_v2.py --config {config_path}")
        print(f"   4. Para desarrollo sin hardware, usa el simulador")

    except Exception as e:
        print(f"❌ Error en ejemplo: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())