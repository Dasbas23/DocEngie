import json
import logging
import os
import re

from app.config import PROVIDERS_JSON_PATH

logger = logging.getLogger(__name__)

_cache = None


def cargar_proveedores(force_reload=False):
    """
    Lee el archivo JSON y devuelve el diccionario de proveedores.
    Usa caché en memoria para evitar lecturas repetidas de disco.
    Si falla, devuelve un diccionario vacío para no romper la app.
    """
    global _cache
    if _cache is not None and not force_reload:
        return _cache

    if not os.path.exists(PROVIDERS_JSON_PATH):
        return {}

    try:
        with open(PROVIDERS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validar que los patrones regex compilen correctamente
        for nombre, reglas in data.items():
            for key in ["patron_documento", "patron_fecha"]:
                patron = reglas.get(key, "")
                if patron:
                    try:
                        re.compile(patron)
                    except re.error as e:
                        logger.error(f"Regex inválido en {nombre}.{key}: {e}")

        _cache = data
        return _cache
    except Exception as e:
        logger.error(f"Error crítico cargando proveedores: {e}")
        return {}


def guardar_proveedor(nombre_clave, datos_proveedor):
    """
    Añade o actualiza un proveedor y guarda los cambios en el JSON.
    """
    global _cache
    proveedores = cargar_proveedores(force_reload=True)
    proveedores[nombre_clave] = datos_proveedor
    result = _escribir_json(proveedores)
    if result:
        _cache = proveedores  # Actualizar caché tras guardar
    return result


def _escribir_json(datos):
    """Función auxiliar privada para escribir en el archivo."""
    try:
        with open(PROVIDERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error guardando JSON: {e}")
        return False
