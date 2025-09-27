#!/usr/bin/env python3
"""
Test para verificar las correcciones del grid y reglas
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_grid_fixes():
    """Test de las correcciones del grid"""
    print("🔧 Testing Grid and Ruler Fixes")
    print("=" * 40)

    try:
        from alignpress_v2.tools.config_designer import ConfigDesigner

        print("✅ Configuration Designer importado correctamente")

        # Verificar que las correcciones están en el código
        import inspect

        # Check _draw_grid method
        grid_method = inspect.getsource(ConfigDesigner._draw_grid)

        fixes_applied = []

        # Check for color fix
        if "#CCCCCC" in grid_method:
            fixes_applied.append("✅ Color del grid corregido (gris sutil)")
        else:
            fixes_applied.append("❌ Color del grid no corregido")

        # Check for spacing check
        if "spacing_px < 5" in grid_method:
            fixes_applied.append("✅ Verificación de espaciado mínimo agregada")
        else:
            fixes_applied.append("❌ Verificación de espaciado faltante")

        # Check for starting position
        if "x = spacing_px" in grid_method:
            fixes_applied.append("✅ Posición inicial del grid corregida")
        else:
            fixes_applied.append("❌ Posición inicial no corregida")

        # Check _draw_rulers_and_grid method
        rulers_method = inspect.getsource(ConfigDesigner._draw_rulers_and_grid)

        if "min_grid_spacing = 20" in rulers_method:
            fixes_applied.append("✅ Espaciado mínimo dinámico implementado")
        else:
            fixes_applied.append("❌ Espaciado dinámico faltante")

        # Check grid spacing default
        init_method = inspect.getsource(ConfigDesigner.__init__)
        if "self.grid_spacing_mm: float = 10.0" in init_method:
            fixes_applied.append("✅ Espaciado por defecto aumentado a 10mm")
        else:
            fixes_applied.append("❌ Espaciado por defecto no actualizado")

        print("\n📋 Correcciones aplicadas:")
        for fix in fixes_applied:
            print(f"  {fix}")

        success_count = len([f for f in fixes_applied if f.startswith("✅")])
        total_count = len(fixes_applied)

        print(f"\n📊 Resumen: {success_count}/{total_count} correcciones aplicadas")

        if success_count == total_count:
            print("\n🎉 TODAS LAS CORRECCIONES APLICADAS CORRECTAMENTE")
            print("\n🎯 Mejoras implementadas:")
            print("  • Color del grid cambiado a gris sutil (#CCCCCC)")
            print("  • Espaciado mínimo de 20 píxeles entre líneas")
            print("  • Espaciado por defecto aumentado a 10mm")
            print("  • Verificación para evitar grids demasiado densos")
            print("  • Posición inicial de líneas corregida")
            print("  • Ajuste dinámico del espaciado según zoom")
        else:
            print("\n⚠️ Algunas correcciones necesitan revisión")

        return success_count == total_count

    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        return False

if __name__ == "__main__":
    success = test_grid_fixes()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)