import logging
import os
import sys

# ==========================================
# LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

# ==========================================
# CONFIGURACIÓN DE RUTAS (SISTEMA HÍBRIDO)
# ==========================================

# Detectamos si estamos corriendo como ejecutable compilado (.exe) o como script (.py)
if getattr(sys, 'frozen', False):
    # MODO EXE: La ruta base es la misma carpeta donde está el .exe
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

# RUTAS DE MOTORES EXTERNOS (OCR)
BIN_DIR = os.path.join(BASE_DIR, "bin")

# Ruta a la carpeta 'bin' de Poppler (pdf2image pide la carpeta, no el exe)
POPPLER_PATH = os.path.join(BIN_DIR, "poppler", "Library", "bin")

# Logs
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")

# Título APP
TITULO_APP = "ClassDoc Engine"

# Versión actual
VERSION_ACTUAL = "v2.7"
