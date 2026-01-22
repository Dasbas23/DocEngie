import shutil
import os
from datetime import datetime
from app.config import DEFAULT_ERROR_DIR


def mover_y_renombrar(ruta_origen, datos, carpeta_base_salida):
    """
    Renombra a: YYYY-MM-DD_NoDocumento.pdf
    """
    nombre_original = os.path.basename(ruta_origen)

    # CONDICIÓN DE ÉXITO: Tenemos Proveedor + ID Documento
    # (La fecha es opcional, si falla usamos "0000-00-00" o fecha de hoy)
    if datos["proveedor_detectado"] and datos["id_documento"]:

        proveedor = datos["proveedor_detectado"]
        doc_id = datos["id_documento"]
        fecha_raw = datos.get("fecha_documento")
        formato_origen = datos.get("formato_fecha")

        # Procesamiento de Fecha
        fecha_str_final = "0000-00-00"  # Valor por defecto si falla

        if fecha_raw and formato_origen:
            try:
                # Convertimos string a objeto fecha real
                objeto_fecha = datetime.strptime(fecha_raw, formato_origen)
                # Convertimos objeto fecha a string ISO (YYYY-MM-DD)
                fecha_str_final = objeto_fecha.strftime("%Y-%m-%d")
            except ValueError:
                # Si la fecha está mal leída o el formato no cuadra
                fecha_str_final = "FECHA-ERROR"

        # NUEVO NOMBRE: 2026-01-19_4951667.pdf
        nuevo_nombre = f"{fecha_str_final}_{doc_id}.pdf"

        # Ruta destino
        subcarpeta = datos.get("carpeta_destino", proveedor)
        dir_final = os.path.join(carpeta_base_salida, subcarpeta)

    else:
        # Fallo -> Revisión Manual
        dir_final = os.path.join(carpeta_base_salida, "Revision_Manual")
        nuevo_nombre = nombre_original

    # --- LÓGICA DE MOVER (Igual que antes) ---
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