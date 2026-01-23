import os

# ==========================================
# CONFIGURACIÓN DE RUTAS SISTEMA
# ==========================================

# Detectamos la ruta base del proyecto para no tener errores de "archivo no encontrado"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta al archivo JSON de base de datos
PROVIDERS_JSON_PATH = os.path.join(BASE_DIR, "data", "proveedores.json")

# Rutas por defecto para archivos
DEFAULT_INPUT_DIR = os.path.join(BASE_DIR, "data", "output") #cambiar a futuro, Ahora es para hacer pruebas
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
DEFAULT_ERROR_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "Revision_Manual")