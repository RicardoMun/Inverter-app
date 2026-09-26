@echo off
title Empaquetar Inverter para Windows
cd /d "%~dp0"

echo ======================================================
echo  Empaquetando Inverter en un UNICO archivo Inverter.exe
echo ======================================================

if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

echo.
echo Ejecutando PyInstaller...
pyinstaller --name="Inverter" ^
    --windowed ^
    --onefile ^
    --clean ^
    --noconfirm ^
    --icon="assets/Inverter.ico" ^
    --collect-all=customtkinter ^
    --collect-all=imageio_ffmpeg ^
    --collect-all=yt_dlp ^
    --add-data="assets;assets" ^
    --add-data="ui;ui" ^
    main.py

echo.
if exist "dist\Inverter.exe" (
    echo ======================================================
    echo  LISTO: dist\Inverter.exe
    echo  Puedes compartir ese archivo directamente.
    echo ======================================================
) else (
    echo ERROR: No se generó el ejecutable.
)
pause
