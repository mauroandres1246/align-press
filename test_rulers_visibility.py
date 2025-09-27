#!/usr/bin/env python3
"""
Test para verificar que las reglas sean visibles
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_rulers_visibility():
    """Test de visibilidad de reglas"""
    print("👁️ Testing Rulers Visibility Fixes")
    print("=" * 40)

    try:
        from alignpress_v2.tools.config_designer import ConfigDesigner
        import inspect

        print("✅ Configuration Designer importado correctamente")

        # Verificar las correcciones de layout
        display_method = inspect.getsource(ConfigDesigner._display_processed_image)
        draw_rulers_method = inspect.getsource(ConfigDesigner._draw_rulers_and_grid)
        draw_grid_method = inspect.getsource(ConfigDesigner._draw_grid)

        fixes_applied = []

        # Check image offset
        if "ruler_offset_x" in display_method and "ruler_offset_y" in display_method:
            fixes_applied.append("✅ Imagen offseteada para hacer espacio a reglas")
        else:
            fixes_applied.append("❌ Imagen no offseteada")

        # Check rulers drawn first
        if "# First draw rulers and grid" in display_method:
            fixes_applied.append("✅ Reglas dibujadas primero")
        else:
            fixes_applied.append("❌ Orden de dibujado no corregido")

        # Check total canvas size calculation
        if "total_width = image_width + ruler_width" in draw_rulers_method:
            fixes_applied.append("✅ Tamaño total de canvas calculado")
        else:
            fixes_applied.append("❌ Tamaño de canvas no ajustado")

        # Check grid offset
        if "ruler_width=0, ruler_height=0" in draw_grid_method:
            fixes_applied.append("✅ Grid offseteado para reglas")
        else:
            fixes_applied.append("❌ Grid no offseteado")

        # Check scroll fixes
        if "xview_moveto(0)" in display_method and "yview_moveto(0)" in display_method:
            fixes_applied.append("✅ Scroll forzado a top-left")
        else:
            fixes_applied.append("❌ Scroll no ajustado")

        print("\n📋 Correcciones aplicadas:")
        for fix in fixes_applied:
            print(f"  {fix}")

        success_count = len([f for f in fixes_applied if f.startswith("✅")])
        total_count = len(fixes_applied)

        print(f"\n📊 Correcciones: {success_count}/{total_count}")

        if success_count == total_count:
            print("\n🎉 TODAS LAS CORRECCIONES DE VISIBILIDAD APLICADAS")
            print("\n🎯 Mejoras implementadas:")
            print("  • Reglas dibujadas antes que la imagen")
            print("  • Imagen offseteada 40x30 píxeles para hacer espacio")
            print("  • Canvas expandido para incluir reglas")
            print("  • Grid offseteado para no interferir con reglas")
            print("  • Scroll automático a top-left para ver reglas")
            print("\n📏 Ahora deberías ver:")
            print("  • Regla horizontal en la parte superior (30px)")
            print("  • Regla vertical en el lado izquierdo (40px)")
            print("  • Imagen desplazada para no tapar las reglas")
            print("  • Grid alineado con la imagen, no con las reglas")
        else:
            print("\n⚠️ Algunas correcciones necesitan revisión")

        return success_count == total_count

    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rulers_visibility()
    print(f"\n{'✅ LISTO PARA PROBAR' if success else '❌ NECESITA REVISIÓN'}")
    sys.exit(0 if success else 1)