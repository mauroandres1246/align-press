#!/usr/bin/env python3
"""
Setup script para AlignPress v2 - Cross-platform environment setup
Ejecutar: python setup_env.py
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

def run_command(cmd, description):
    print(f"🔧 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} completado")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        return False
    return True

def main():
    print("🚀 AlignPress v2 - Environment Setup")
    print("=" * 50)

    # Detect platform
    system = platform.system()
    print(f"📱 Sistema detectado: {system}")

    # Create virtual environment
    if not Path(".venv").exists():
        print("🐍 Creando virtual environment...")
        if system == "Windows":
            run_command("python -m venv .venv", "Virtual environment")
            activate_cmd = ".venv\\Scripts\\activate"
        else:
            run_command("python3 -m venv .venv", "Virtual environment")
            activate_cmd = "source .venv/bin/activate"

    # Install requirements
    pip_cmd = ".venv/bin/pip" if system != "Windows" else ".venv\\Scripts\\pip"
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrade pip")

    if Path("requirements-v2.txt").exists():
        run_command(f"{pip_cmd} install -r requirements-v2.txt", "Install requirements")

    # Platform-specific setup
    if system == "Darwin":  # macOS
        print("🍎 Configuración específica para macOS...")
        run_command("brew install opencv", "Install OpenCV via Homebrew")
    elif system == "Linux":
        print("🐧 Configuración específica para Linux...")
        run_command("sudo apt-get update && sudo apt-get install -y python3-opencv", "Install OpenCV")

    print("\n✅ Setup completado!")
    print(f"Para activar el environment: {activate_cmd}")
    print("Para ejecutar: python main.py")

if __name__ == "__main__":
    main()