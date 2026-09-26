"""
Script de construcción para empaquetar la aplicación Inverter con PyInstaller.
Genera un bundle ejecutable independiente (.app en macOS, .exe en Windows).
"""
import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("=" * 60)
    print("🚀 Empaquetando Inverter con PyInstaller")
    print("=" * 60)

    # Prioridad: Inverter.icns / Inverter.ico (nombre oficial)
    icon_path = None
    if sys.platform == "darwin":
        icon_path = os.path.join(BASE_DIR, "assets", "Inverter.icns")
    else:
        icon_path = os.path.join(BASE_DIR, "assets", "Inverter.ico")

    if not os.path.exists(icon_path):
        print(f"⚠️  Ícono no encontrado en: {icon_path}")
        icon_path = None

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Inverter",
        "--noconsole",
        "--clean",
        "--noconfirm",
        "--collect-all=customtkinter",
        "--collect-all=imageio_ffmpeg",
        "--collect-all=yt_dlp",
        "--add-data=assets:assets",
        "--add-data=ui:ui",
    ]

    if icon_path:
        cmd.append(f"--icon={icon_path}")
        print(f"✅ Usando ícono: {icon_path}")

    if sys.platform == "darwin":
        cmd.extend(["--windowed", "--onedir"])
    else:
        cmd.extend(["--windowed", "--onefile"])

    cmd.append(os.path.join(BASE_DIR, "main.py"))

    print(f"\nComando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        if sys.platform == "darwin":
            print(f"✅ App lista en: {os.path.join(BASE_DIR, 'dist', 'Inverter.app')}")
            print("Puedes mover Inverter.app a /Applications")
        else:
            print(f"✅ Ejecutable listo en: {os.path.join(BASE_DIR, 'dist', 'Inverter.exe')}")
        print("=" * 60)
    else:
        print("\n❌ Error durante el empaquetado.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
