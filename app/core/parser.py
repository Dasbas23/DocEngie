import re
from app.config import PROVEEDORES


def analizar_documento(texto_pdf):
    """
    Recibe el texto crudo del PDF.
    1. Busca qué proveedor es (buscando las 'firmas').
    2. Si encuentra proveedor, aplica su regex para sacar el pedido.

    Retorna: Diccionario con resultados
    """
    resultado = {
        "proveedor_detectado": None,
        "numero_pedido": None,
        "confianza": "Baja",
        "log_info": ""
    }

    if not texto_pdf:
        return resultado

    # 1. IDENTIFICACIÓN DEL PROVEEDOR
    proveedor_encontrado = None

    for nombre_prov, reglas in PROVEEDORES.items():
        firmas = reglas.get("firma", [])
        # Buscamos si alguna firma está en el texto
        for firma in firmas:
            if firma.lower() in texto_pdf.lower():
                proveedor_encontrado = nombre_prov
                break  # Dejamos de buscar firmas para este proveedor

        if proveedor_encontrado:
            break  # ¡Encontrado! Dejamos de buscar otros proveedores

    if not proveedor_encontrado:
        resultado["log_info"] = "No se detectó ninguna firma de proveedor conocida."
        return resultado

    # 2. EXTRACCIÓN DE DATOS (Solo si tenemos proveedor)
    resultado["proveedor_detectado"] = proveedor_encontrado
    reglas_activas = PROVEEDORES[proveedor_encontrado]
    patron = reglas_activas.get("patron_pedido")

    match = re.search(patron, texto_pdf, re.IGNORECASE | re.MULTILINE)

    if match:
        # group(1) coge lo que está dentro del paréntesis de la regex ()
        # strip() quita espacios en blanco sobrantes
        pedido_limpio = match.group(1).strip()

        resultado["numero_pedido"] = pedido_limpio
        resultado["confianza"] = "Alta"
        resultado["carpeta_destino"] = reglas_activas.get("carpeta_destino")
    else:
        resultado["log_info"] = f"Proveedor {proveedor_encontrado} identificado, pero falló la Regex del pedido."

    return resultado