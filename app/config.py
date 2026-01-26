import os
import sys

# ==========================================
# CONFIGURACIÓN DE RUTAS (SISTEMA HÍBRIDO)
# ==========================================

# Detectamos si estamos corriendo como ejecutable compilado (.exe) o como script (.py)
if getattr(sys, 'frozen', False):
    # MODO EXE: La ruta base es la misma carpeta donde está el .exe
    # (PyInstaller descomprime cosas en _MEIPASS, pero nosotros queremos la carpeta del usuario donde está el .exe)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # MODO SCRIPT: La ruta base es subir dos niveles desde este archivo
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- DEFINICIÓN DE RUTAS RELATIVAS ---

# Archivo de base de datos
PROVIDERS_JSON_PATH = os.path.join(BASE_DIR, "data", "proveedores.json")

# Carpetas de trabajo
DEFAULT_INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
DEFAULT_ERROR_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "Revision_Manual")

# Logs
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")