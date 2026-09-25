"""
Inverter - YouTube to MP3 Converter
Punto de entrada de la aplicación de escritorio.
"""
import sys
import os

# Suprimir avisos de deprecación de Tk en macOS
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Asegurar que el directorio del proyecto esté en el sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ui.app import launch

if __name__ == "__main__":
    launch()
