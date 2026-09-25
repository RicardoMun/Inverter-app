#!/usr/bin/env bash
cd "$(dirname "$0")"

export TK_SILENCE_DEPRECATION=1

# Si no existe .venv o fue creado con python antiguo, usar Python 3.12 de Homebrew
if [ ! -f ".venv/bin/python3" ]; then
    if [ -f "/opt/homebrew/bin/python3.12" ]; then
        /opt/homebrew/bin/python3.12 -m venv .venv
    else
        python3 -m venv .venv
    fi
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

echo "Iniciando Inverter con Tk nativo..."
.venv/bin/python3 main.py
