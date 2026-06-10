import json
import os
from app.config import PROVIDERS_JSON_PATH

# Caché de módulo: el JSON solo se relee tras invalidar_cache()
_cache_proveedores = None


def cargar_proveedores():
    """
    Lee el archivo JSON y devuelve el diccionario de proveedores.
    Usa caché en memoria. Si falla, devuelve un diccionario vacío
    (sin cachear el fallo) para no romper la app.
    """
    global _cache_proveedores
    if _cache_proveedores is not None:
        return _cache_proveedores

    if not os.path.exists(PROVIDERS_JSON_PATH):
        return {}

    try:
        with open(PROVIDERS_JSON_PATH, 'r', encoding='utf-8') as f:
            _cache_proveedores = json.load(f)
            return _cache_proveedores
    except Exception as e:
        print(f"❌ Error crítico cargando proveedores: {e}")
        return {}


def invalidar_cache():
    """Fuerza relectura del JSON en la próxima llamada a cargar_proveedores()."""
    global _cache_proveedores
    _cache_proveedores = None


def guardar_proveedor(nombre_clave, datos_proveedor):
    """
    Añade o actualiza un proveedor y guarda los cambios en el JSON.
    """
    proveedores = dict(cargar_proveedores())
    proveedores[nombre_clave] = datos_proveedor
    resultado = _escribir_json(proveedores)
    invalidar_cache()
    return resultado


def _escribir_json(datos):
    """Función auxiliar privada para escribir en el archivo."""
    try:
        with open(PROVIDERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")
        return False