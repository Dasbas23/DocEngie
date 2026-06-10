"""
Persistencia de preferencias del usuario en data/settings.json.
Si el archivo no existe o está corrupto, se usan los defaults.
"""
import json
import os

from app.config import BASE_DIR, DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR

SETTINGS_PATH = os.path.join(BASE_DIR, "data", "settings.json")

DEFAULTS = {
    "last_input_dir": DEFAULT_INPUT_DIR,
    "last_output_dir": DEFAULT_OUTPUT_DIR,
    "usar_ocr": True,
    "tema": "Dark",
    # True cuando el usuario eligió carpeta destino a mano:
    # entonces NO se sincroniza automáticamente con la de origen.
    "output_manual": False,
}


def cargar_settings(ruta=None):
    """Devuelve los settings combinados con los defaults (claves extrañas fuera)."""
    ruta = ruta or SETTINGS_PATH
    settings = dict(DEFAULTS)

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            settings.update({k: datos[k] for k in DEFAULTS if k in datos})
    except (OSError, ValueError):
        pass  # sin archivo o corrupto: defaults

    # Carpetas guardadas que ya no existen -> volver al default
    for clave in ("last_input_dir", "last_output_dir"):
        if not os.path.isdir(settings[clave]):
            settings[clave] = DEFAULTS[clave]

    return settings


def guardar_settings(settings, ruta=None):
    """Escribe los settings. Devuelve True/False según éxito.

    Los valores deben ser serializables a JSON.
    """
    ruta = ruta or SETTINGS_PATH
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, TypeError) as e:
        print(f"⚠️ No se pudieron guardar los settings: {e}")
        return False
