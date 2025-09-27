#!/usr/bin/env python3
"""
Test script para depurar la visualización de reglas
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_rulers_debug():
    """Test con debugging de las reglas"""
    print("🔍 Testing Rulers Visualization with Debug")
    print("=" * 45)

    try:
        from alignpress_v2.tools.config_designer import ConfigDesigner
        import inspect

        # Verificar que las mejoras de debugging están presentes
        rulers_grid_method = inspect.getsource(ConfigDesigner._draw_rulers_and_grid)
        rulers_method = inspect.getsource(ConfigDesigner._draw_rulers)

        debug_checks = []

        if "print(f\"DEBUG:" in rulers_grid_method:
            debug_checks.append("✅ Debug prints agregados en _draw_rulers_and_grid")
        else:
            debug_checks.append("❌ Debug prints faltantes en _draw_rulers_and_grid")

        if "print(f\"DEBUG:" in rulers_method:
            debug_checks.append("✅ Debug prints agregados en _draw_rulers")
        else:
            debug_checks.append("❌ Debug prints faltantes en _draw_rulers")

        if "fill=\"#E0E0E0\"" in rulers_method:
            debug_checks.append("✅ Color de reglas mejorado (#E0E0E0)")
        else:
            debug_checks.append("❌ Color de reglas no actualizado")

        if "width=2" in rulers_method:
            debug_checks.append("✅ Bordes de reglas más gruesos")
        else:
            debug_checks.append("❌ Bordes de reglas no mejorados")

        if "ruler_height = 30" in rulers_method:
            debug_checks.append("✅ Altura de reglas aumentada (30px)")
        else:
            debug_checks.append("❌ Altura de reglas no aumentada")

        if "ruler_width = 40" in rulers_method:
            debug_checks.append("✅ Ancho de reglas aumentado (40px)")
        else:
            debug_checks.append("❌ Ancho de reglas no aumentado")

        print("📋 Estado de las mejoras:")
        for check in debug_checks:
            print(f"  {check}")

        success_count = len([c for c in debug_checks if c.startswith("✅")])
        total_count = len(debug_checks)

        print(f"\n📊 Mejoras aplicadas: {success_count}/{total_count}")

        if success_count == total_count:
            print("\n🎉 TODAS LAS MEJORAS DE DEBUGGING APLICADAS")
            print("\n🔍 Para debugging:")
            print("  1. Ejecuta el Configuration Designer")
            print("  2. Carga una imagen")
            print("  3. Asegúrate de que 'Reglas' esté marcado")
            print("  4. Revisa la consola para ver los mensajes DEBUG")
            print("\n📏 Mejoras de reglas:")
            print("  • Fondo gris claro (#E0E0E0)")
            print("  • Bordes oscuros (#666666) más gruesos")
            print("  • Tamaño aumentado (30x40 píxeles)")
            print("  • Texto más legible (Arial 10 bold)")
            print("  • Marcas más visibles (#333333)")
        else:
            print("\n⚠️ Algunas mejoras necesitan revisión")

        return success_count == total_count

    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rulers_debug()
    print(f"\n{'✅ SUCCESS - Ready for testing' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)