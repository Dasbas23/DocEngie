import re
from app.core.provider_manager import cargar_proveedores


def analizar_documento(texto_pdf):
    """
    1. Identifica proveedor.
    2. Extrae Nº Documento.
    3. Extrae Fecha (limpiando espacios del OCR).
    """
    resultado = {
        "proveedor_detectado": None,
        "id_documento": None,
        "fecha_documento": None,
        "formato_fecha": None,
        "carpeta_destino": None,
        "log_info": ""
    }

    if not texto_pdf:
        return resultado

    diccionario_proveedores = cargar_proveedores()
    proveedor_encontrado = None

    # 1. IDENTIFICACIÓN
    for nombre_prov, reglas in diccionario_proveedores.items():
        firmas = reglas.get("firma", [])
        for firma in firmas:
            if firma.lower() in texto_pdf.lower():
                proveedor_encontrado = nombre_prov
                break
        if proveedor_encontrado: break

    if not proveedor_encontrado:
        resultado["log_info"] = "Proveedor desconocido."
        return resultado

    resultado["proveedor_detectado"] = proveedor_encontrado
    reglas = diccionario_proveedores[proveedor_encontrado]

    # 2. EXTRACCIÓN DOCUMENTO (Albarán/Factura)
    patron_doc = reglas.get("patron_documento")
    if patron_doc:
        match_doc = re.search(patron_doc, texto_pdf, re.IGNORECASE | re.MULTILINE)
        if match_doc:
            raw_doc = match_doc.group(1).strip()
            # [MEJORA] Limpieza: Quitamos espacios intermedios (ej: "49 51 667" -> "4951667")
            resultado["id_documento"] = raw_doc.replace(" ", "").replace(".", "")

    # 3. EXTRACCIÓN FECHA
    patron_fecha = reglas.get("patron_fecha")
    if patron_fecha:
        match_fecha = re.search(patron_fecha, texto_pdf, re.IGNORECASE | re.MULTILINE)
        if match_fecha:
            raw_fecha = match_fecha.group(1).strip()
            # [MEJORA] Limpieza: Quitamos espacios en la fecha (ej: "19/ 01 / 2026" -> "19/01/2026")
            fecha_limpia = raw_fecha.replace(" ", "")

            resultado["fecha_documento"] = fecha_limpia
            resultado["formato_fecha"] = reglas.get("formato_fecha_origen", "%d/%m/%Y")

    resultado["carpeta_destino"] = reglas.get("carpeta_destino")

    return resultado