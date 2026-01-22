import json
import os
from app.config import PROVIDERS_JSON_PATH


def cargar_proveedores():
    """
    Lee el archivo JSON y devuelve el diccionario de proveedores.
    Si falla, devuelve un diccionario vacío para no romper la app.
    """
    if not os.path.exists(PROVIDERS_JSON_PATH):
        return {}

    try:
        with open(PROVIDERS_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error crítico cargando proveedores: {e}")
        return {}


def guardar_proveedor(nombre_clave, datos_proveedor):
    """
    Añade o actualiza un proveedor y guarda los cambios en el JSON.
    """
    proveedores = cargar_proveedores()
    proveedores[nombre_clave] = datos_proveedor
    return _escribir_json(proveedores)


def _escribir_json(datos):
    """Función auxiliar privada para escribir en el archivo."""
    try:
        with open(PROVIDERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")
        return False