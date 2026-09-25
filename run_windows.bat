@echo off
title Inverter - MP3 Downloader
cd /d "%~dp0"

if not exist ".venv" (
    echo Creando entorno virtual en Windows...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

echo Iniciando Inverter...
python main.py
pause
