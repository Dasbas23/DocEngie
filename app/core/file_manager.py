import shutil
import os
from datetime import datetime
from app.config import DEFAULT_ERROR_DIR


def obtener_fecha_creacion_archivo(ruta_archivo):
    """
    Intenta sacar la fecha de creación/modificación de los metadatos del archivo
    si el OCR ha fallado leyendo la fecha impresa.
    Retorna string: "YYYY-MM-DD"
    """
    try:
        # timestamp de la última modificación
        timestamp = os.path.getmtime(ruta_archivo)
        fecha_obj = datetime.fromtimestamp(timestamp)
        return fecha_obj.strftime("%Y-%m-%d")
    except:
        return "0000-00-00"


def mover_y_renombrar(ruta_origen, datos, carpeta_base_salida):
    """
    Renombra a: YYYY-MM-DD_NoDocumento.pdf
    Soporta fallback de fecha si el OCR falla.
    """
    nombre_original = os.path.basename(ruta_origen)

    # CONDICIÓN DE ÉXITO: Basta con tener Proveedor + ID Documento
    if datos["proveedor_detectado"] and datos["id_documento"]:

        proveedor = datos["proveedor_detectado"]
        doc_id = datos["id_documento"]
        fecha_raw = datos.get("fecha_documento")
        formato_origen = datos.get("formato_fecha")

        # --- LÓGICA DE FECHA (MEJORADA) ---
        fecha_str_final = None

        # 1. Intento: Fecha leída del PDF (Regex)
        if fecha_raw and formato_origen:
            try:
                objeto_fecha = datetime.strptime(fecha_raw, formato_origen)
                fecha_str_final = objeto_fecha.strftime("%Y-%m-%d")
            except ValueError:
                pass  # Falló el formato, pasamos al plan B

        # 2. Intento: Plan B (Metadatos del archivo)
        # Si no leímos fecha en el papel, usamos la fecha del archivo digital
        if not fecha_str_final:
            fecha_str_final = obtener_fecha_creacion_archivo(ruta_origen)
            # Añadimos una marca visual para saber que esta fecha es "estimada"
            # Opcional: podrías añadir un sufijo "_SCAN" si quisieras diferenciarla

        # NUEVO NOMBRE
        nuevo_nombre = f"{fecha_str_final}_{doc_id}.pdf"

        # Ruta destino
        subcarpeta = datos.get("carpeta_destino", proveedor)
        dir_final = os.path.join(carpeta_base_salida, subcarpeta)

    else:
        # Fallo Crítico (Falta proveedor o ID) -> Revisión Manual
        dir_final = os.path.join(carpeta_base_salida, "Revision_Manual")
        nuevo_nombre = nombre_original

    # --- LÓGICA DE MOVER ---
    os.makedirs(dir_final, exist_ok=True)
    ruta_destino = os.path.join(dir_final, nuevo_nombre)

    # Evitar duplicados
    if os.path.exists(ruta_destino):
        base, ext = os.path.splitext(nuevo_nombre)
        ruta_destino = os.path.join(dir_final, f"{base}_DUPLICADO_{os.urandom(2).hex()}{ext}")

    try:
        shutil.move(ruta_origen, ruta_destino)
        return True, ruta_destino
    except Exception as e:
        return False, str(e)