#!/usr/bin/env python3
"""
Development Tools Launcher for AlignPress v2

Provides easy access to all development and debugging tools
"""
import sys
import os
import argparse
from pathlib import Path

# Add alignpress_v2 to Python path
sys.path.insert(0, os.path.abspath('.'))


def launch_config_designer():
    """Launch the configuration designer"""
    try:
        from alignpress_v2.tools.config_designer import ConfigDesigner
        app = ConfigDesigner()
        app.run()
    except ImportError as e:
        print(f"❌ Error: GUI dependencies not available: {e}")
        print("   Instala: pip install opencv-python pillow")
    except Exception as e:
        print(f"❌ Error launching config designer: {e}")


def launch_detection_simulator(image_path=None, config_path=None):
    """Launch detection simulator"""
    try:
        from alignpress_v2.tools.detection_simulator import DetectionSimulator
        from alignpress_v2.config.config_manager import ConfigManager
        from alignpress_v2.config.models import create_default_config

        simulator = DetectionSimulator()

        if config_path:
            print(f"📖 Loading config from: {config_path}")
            config_manager = ConfigManager(Path(config_path))
            config = config_manager.load()
        else:
            print("📖 Using default configuration")
            config = create_default_config()

        style = config.get_active_style()
        if not style:
            print("❌ No active style found in configuration")
            return

        if image_path:
            print(f"🎯 Simulating detection on: {image_path}")
            result = simulator.simulate_garment_detection(
                Path(image_path), style, config
            )

            # Print results
            success_status = "✅" if result.get('overall_success') else "❌"
            print(f"\n{success_status} Detection Result:")
            print(f"   Logos detected: {result.get('successful_logos', 0)}/{result.get('logo_count', 0)}")
            print(f"   Processing time: {result.get('processing_time_ms', 0):.1f}ms")
            print(f"   Average confidence: {result.get('average_confidence', 0):.3f}")

            # Create debug image
            debug_path = simulator.create_visual_debug_image(Path(image_path), result)
            if debug_path:
                print(f"🖼️  Debug image created: {debug_path}")

        else:
            print("ℹ️  No image specified. Use --image to test detection.")

    except ImportError as e:
        print(f"❌ Error: Dependencies not available: {e}")
        print("   Instala: pip install opencv-python pillow")
    except Exception as e:
        print(f"❌ Error in simulator: {e}")


def run_example_workflow():
    """Run the complete example workflow"""
    try:
        import example_camisola_workflow
        return example_camisola_workflow.main()
    except Exception as e:
        print(f"❌ Error running example workflow: {e}")
        return 1


def launch_ui_app(config_path=None):
    """Launch the main UI application"""
    try:
        from alignpress_v2.ui import main

        args = []
        if config_path:
            args.extend(['--config', config_path])

        # Override sys.argv for the UI main function
        original_argv = sys.argv.copy()
        sys.argv = ['alignpress_v2'] + args

        try:
            main()
        finally:
            sys.argv = original_argv

    except Exception as e:
        print(f"❌ Error launching UI: {e}")


def run_integration_tests():
    """Run integration tests"""
    try:
        import test_ui_integration
        return test_ui_integration.main()
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return 1


def show_menu():
    """Show interactive menu"""
    while True:
        print("\n" + "=" * 50)
        print("🛠️  ALIGNPRESS v2 - DEVELOPMENT TOOLS")
        print("=" * 50)
        print("1. 🎨 Configuration Designer (GUI)")
        print("2. 🔍 Detection Simulator")
        print("3. 🎽 Example: Camisola Workflow")
        print("4. 🖥️  Launch Main UI Application")
        print("5. ✅ Run Integration Tests")
        print("6. ❓ Show Help")
        print("0. 🚪 Exit")
        print("-" * 50)

        try:
            choice = input("Selecciona una opción (0-6): ").strip()

            if choice == "0":
                print("👋 ¡Hasta luego!")
                break

            elif choice == "1":
                print("\n🎨 Launching Configuration Designer...")
                launch_config_designer()

            elif choice == "2":
                print("\n🔍 Detection Simulator Options:")
                image_path = input("Image path (optional): ").strip()
                config_path = input("Config path (optional): ").strip()

                if image_path and not Path(image_path).exists():
                    print(f"❌ Image not found: {image_path}")
                    continue

                if config_path and not Path(config_path).exists():
                    print(f"❌ Config not found: {config_path}")
                    continue

                launch_detection_simulator(
                    image_path if image_path else None,
                    config_path if config_path else None
                )

            elif choice == "3":
                print("\n🎽 Running Example Workflow...")
                run_example_workflow()

            elif choice == "4":
                print("\n🖥️  UI Application Options:")
                config_path = input("Config path (optional): ").strip()

                if config_path and not Path(config_path).exists():
                    print(f"❌ Config not found: {config_path}")
                    continue

                launch_ui_app(config_path if config_path else None)

            elif choice == "5":
                print("\n✅ Running Integration Tests...")
                result = run_integration_tests()
                if result == 0:
                    print("🎉 All tests passed!")
                else:
                    print("💥 Some tests failed!")

            elif choice == "6":
                show_help()

            else:
                print("❌ Invalid option. Please try again.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

        input("\n📱 Press Enter to continue...")


def show_help():
    """Show help information"""
    help_text = """
🛠️  ALIGNPRESS v2 - DEVELOPMENT TOOLS HELP

HERRAMIENTAS DISPONIBLES:

1. 🎨 Configuration Designer
   - Herramienta GUI interactiva para crear configuraciones
   - Permite colocar logos visualmente en imágenes
   - Genera automáticamente ROIs y posiciones
   - Exporta configuraciones en YAML/JSON

2. 🔍 Detection Simulator
   - Simula algoritmos de detección sin hardware
   - Prueba configuraciones con imágenes estáticas
   - Genera imágenes de debug con resultados
   - Calcula métricas de rendimiento

3. 🎽 Example Workflow
   - Ejemplo completo de configuración para camisola de fútbol
   - Demuestra múltiples logos y variantes de talla
   - Muestra flujo completo de configuración → almacenamiento → detección

4. 🖥️  Main UI Application
   - Interfaz principal de AlignPress v2 con CustomTkinter
   - Viewport de cámara con overlays
   - Panel de control con métricas en tiempo real
   - Integración completa con el sistema de eventos

5. ✅ Integration Tests
   - Prueba todos los componentes funcionando juntos
   - Valida la arquitectura completa
   - Verificación automática de funcionalidades

FLUJO DE DESARROLLO RECOMENDADO:

1. Crear configuración inicial:
   → Ejecutar "Example Workflow" para ver el patrón
   → Usar "Configuration Designer" para crear tu configuración específica

2. Probar algoritmos de detección:
   → Usar "Detection Simulator" con imágenes de prueba
   → Ajustar parámetros basándose en resultados
   → Iterar hasta obtener precisión deseada

3. Validar integración:
   → Ejecutar "Integration Tests" para verificar arquitectura
   → Usar "Main UI Application" para pruebas de usuario final

4. Debugging y optimización:
   → Usar imágenes de debug del simulador
   → Revisar logs de detección
   → Ajustar ROIs y tolerancias según necesidad

ESTRUCTURA DE ARCHIVOS SUGERIDA:

test_images/
├── comunicaciones_2024/
│   ├── talla_s/
│   ├── talla_m/
│   └── talla_xl/
configs/
├── examples/
└── production/
templates/
├── logos/
└── patterns/

DEPENDENCIES OPCIONALES:

Para herramientas GUI:
pip install opencv-python pillow

Para funcionalidad completa:
pip install customtkinter pyyaml numpy

"""
    print(help_text)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AlignPress v2 Development Tools Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dev_tools_launcher.py                    # Interactive menu
  python dev_tools_launcher.py --config-designer  # Launch config designer
  python dev_tools_launcher.py --simulator --image test.jpg
  python dev_tools_launcher.py --example          # Run example workflow
  python dev_tools_launcher.py --ui --config config.yaml
  python dev_tools_launcher.py --tests            # Run integration tests
        """
    )

    parser.add_argument('--config-designer', action='store_true',
                       help='Launch configuration designer')
    parser.add_argument('--simulator', action='store_true',
                       help='Launch detection simulator')
    parser.add_argument('--example', action='store_true',
                       help='Run example workflow')
    parser.add_argument('--ui', action='store_true',
                       help='Launch main UI application')
    parser.add_argument('--tests', action='store_true',
                       help='Run integration tests')
    parser.add_argument('--image', type=str,
                       help='Image path for simulator')
    parser.add_argument('--config', type=str,
                       help='Configuration file path')

    args = parser.parse_args()

    # Check if any specific tool was requested
    if args.config_designer:
        launch_config_designer()
    elif args.simulator:
        launch_detection_simulator(args.image, args.config)
    elif args.example:
        return run_example_workflow()
    elif args.ui:
        launch_ui_app(args.config)
    elif args.tests:
        return run_integration_tests()
    else:
        # No specific tool requested, show interactive menu
        show_menu()

    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
        exit(0)