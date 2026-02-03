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

# RUTAS DE MOTORES EXTERNOS (OCR)
# Ajusta estos nombres según cómo se llamen tus carpetas dentro de 'bin'
BIN_DIR = os.path.join(BASE_DIR, "bin")



# Ruta a la carpeta 'bin' de Poppler (OJO: pdf2image pide la carpeta, no el exe)
# A veces la carpeta se llama 'Release-24.02.0-0' o similar, ajusta esto:
POPPLER_PATH = os.path.join(BIN_DIR, "poppler", "Library", "bin")
# ^^^ VERIFICA ESTA RUTA EN TU EXPLORADOR DE ARCHIVOS ^^^

# Logs
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")

#Título APP
TITULO_APP ="⚙️ ClassDoc Engine"

#Versión actual
VERSION_ACTUAL = "v2.6 (OCR_Paddle)"