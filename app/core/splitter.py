from pypdf import PdfReader, PdfWriter
from app.core.parser import analizar_documento
from app.core.ocr_utils import extraer_texto_pagina
import os


def agrupar_paginas(analisis_por_pagina):
    """
    Decide los cortes de un lote a partir del análisis de cada página.

    Entrada: [{"proveedor": str|None, "id_documento": str|None}, ...]
    Salida:  [{"paginas": [índices], "proveedor": str, "id_documento": str|None}, ...]

    Reglas:
    - Sin proveedor detectado -> continuación del documento abierto
      (o huérfano "Desconocido" si no hay ninguno abierto).
    - Proveedor distinto al abierto -> corte.
    - Mismo proveedor con nº de documento distinto o ilegible -> corte.
      (Los documentos reales son de 1-2 páginas; cuando la cabecera se
      repite, el nº casi siempre se repite con ella.)
    - Mismo proveedor y mismo nº -> continuación.
    """
    grupos = []
    actual = None

    for i, info in enumerate(analisis_por_pagina):
        proveedor = info.get("proveedor")
        id_doc = info.get("id_documento")

        if proveedor is None:
            if actual is None:
                actual = {"paginas": [i], "proveedor": "Desconocido", "id_documento": None}
            else:
                actual["paginas"].append(i)
            continue

        es_continuacion = (
            actual is not None
            and actual["proveedor"] == proveedor
            and id_doc is not None
            and actual["id_documento"] == id_doc
        )

        if es_continuacion:
            actual["paginas"].append(i)
        else:
            if actual:
                grupos.append(actual)
            actual = {"paginas": [i], "proveedor": proveedor, "id_documento": id_doc}

    if actual:
        grupos.append(actual)

    return grupos


def dividir_pdf_por_proveedor(ruta_pdf_masivo, carpeta_temporal, usar_ocr=False):
    """
    Trocea un PDF multipágina (Lote) en documentos individuales.

    Devuelve: [{"ruta": str, "texto": str, "analisis": dict}, ...]
    El texto extraído aquí se reaprovecha en la clasificación:
    no hay que volver a abrir ni OCR-ear los fragmentos.
    """
    if not os.path.exists(ruta_pdf_masivo):
        return []

    try:
        reader = PdfReader(ruta_pdf_masivo)
    except Exception as e:
        print(f"❌ Error abriendo lote PDF: {e}")
        return []

    os.makedirs(carpeta_temporal, exist_ok=True)

    total_paginas = len(reader.pages)
    print(f"🔄 Analizando lote de {total_paginas} páginas (OCR={usar_ocr})...")

    # 1. Extraer texto y analizar página a página (una sola vez)
    textos = []
    analisis_paginas = []
    for i, page in enumerate(reader.pages):
        texto = extraer_texto_pagina(page, ruta_pdf_masivo, i, usar_ocr)
        textos.append(texto)
        analisis = analizar_documento(texto)
        analisis_paginas.append({
            "proveedor": analisis["proveedor_detectado"],
            "id_documento": analisis["id_documento"],
        })

    # 2. Decidir los cortes
    grupos = agrupar_paginas(analisis_paginas)

    # 3. Escribir cada grupo y devolver texto + análisis del documento completo
    resultados = []
    for grupo in grupos:
        writer = PdfWriter()
        for indice in grupo["paginas"]:
            writer.add_page(reader.pages[indice])

        ruta = _guardar_fragmento(
            writer, grupo["proveedor"], grupo["paginas"][0], carpeta_temporal
        )
        texto_grupo = "\n".join(textos[indice] for indice in grupo["paginas"])
        resultados.append({
            "ruta": ruta,
            "texto": texto_grupo,
            # El análisis del grupo completo extrae también fecha y carpeta destino
            "analisis": analizar_documento(texto_grupo),
        })
        print(f"   ✂️ Documento: {grupo['proveedor']} (págs {grupo['paginas']})")

    return resultados


def _guardar_fragmento(writer, proveedor, indice_pag, carpeta):
    """Escribe el PDF temporal en disco"""
    nombre = f"SPLIT_Pag{indice_pag}_{proveedor}.pdf"
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "wb") as f:
        writer.write(f)
    return ruta
