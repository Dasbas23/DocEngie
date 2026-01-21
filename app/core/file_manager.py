import shutil
import os
from app.config import DEFAULT_OUTPUT_DIR, DEFAULT_ERROR_DIR


def mover_y_renombrar(ruta_origen, datos_analisis):
    """
    Toma el archivo original y lo mueve a su destino final
    basado en el análisis (proveedor y pedido).
    """
    nombre_archivo_original = os.path.basename(ruta_origen)

    # CASO 1: Éxito (Tenemos proveedor y pedido)
    if datos_analisis["proveedor_detectado"] and datos_analisis["numero_pedido"]:
        proveedor = datos_analisis["proveedor_detectado"]
        pedido = datos_analisis["numero_pedido"]
        carpeta_destino_config = datos_analisis.get("carpeta_destino", proveedor)

        # Construir ruta: output/Amazon/
        dir_final = os.path.join(DEFAULT_OUTPUT_DIR, carpeta_destino_config)

        # Nuevo nombre: PEDIDO-1234.pdf (o manteniendo extensión original)
        extension = os.path.splitext(nombre_archivo_original)[1]
        nuevo_nombre = f"{pedido}{extension}"

        # Limpiar caracteres ilegales en nombre de archivo (por si acaso el OCR lee barras)
        nuevo_nombre = "".join([c for c in nuevo_nombre if c.isalnum() or c in "._-"])

    # CASO 2: Fallo (Revisión manual)
    else:
        dir_final = DEFAULT_ERROR_DIR
        nuevo_nombre = nombre_archivo_original  # Se queda igual

    # Crear carpeta si no existe
    os.makedirs(dir_final, exist_ok=True)

    ruta_destino_final = os.path.join(dir_final, nuevo_nombre)

    # Evitar sobreescribir si ya existe uno igual
    if os.path.exists(ruta_destino_final):
        base, ext = os.path.splitext(nuevo_nombre)
        ruta_destino_final = os.path.join(dir_final, f"{base}_DUPLICADO{ext}")

    try:
        shutil.move(ruta_origen, ruta_destino_final)
        return True, ruta_destino_final
    except Exception as e:
        return False, str(e)