from pypdf import PdfReader, PdfWriter
from app.core.parser import analizar_documento
from app.config import TESSERACT_CMD, POPPLER_PATH
import os

# Importación condicional para OCR
try:
    import pytesseract
    from pdf2image import convert_from_path

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def dividir_pdf_por_proveedor(ruta_pdf_masivo, carpeta_temporal, usar_ocr=False):
    """
    Recorre un PDF multipágina (Lote).
    Estrategia de Guillotina: Si detecta un proveedor en una página,
    asume que es el inicio de un nuevo documento.

    Soporta OCR si usar_ocr=True y la página no tiene texto nativo.
    """
    if not os.path.exists(ruta_pdf_masivo):
        return []

    try:
        reader = PdfReader(ruta_pdf_masivo)
    except Exception as e:
        print(f"❌ Error abriendo lote PDF: {e}")
        return []

    archivos_generados = []

    writer_actual = None
    proveedor_actual = "Desconocido"
    pagina_inicio_actual = 0

    # Configurar Tesseract si hace falta
    if usar_ocr and OCR_AVAILABLE:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    os.makedirs(carpeta_temporal, exist_ok=True)

    total_paginas = len(reader.pages)
    print(f"🔄 Analizando lote masivo de {total_paginas} páginas (OCR={usar_ocr})...")

    for i, page in enumerate(reader.pages):
        # 1. Intentar extracción nativa (Rápida)
        try:
            text = page.extract_text() or ""
        except:
            text = ""

        # 2. Si no hay texto y el OCR está activado, mirar la imagen (Lento)
        if not text.strip() and usar_ocr and OCR_AVAILABLE:
            try:
                # Convertimos SOLO esta página a imagen (índices 1-based)
                # Esto evita convertir todo el PDF cada vez
                imagenes = convert_from_path(
                    ruta_pdf_masivo,
                    first_page=i + 1,
                    last_page=i + 1,
                    poppler_path=POPPLER_PATH
                )
                for img in imagenes:
                    # Usamos psm 6 como acordamos (bloque de texto)
                    text += pytesseract.image_to_string(img, lang='spa', config='--psm 6')
            except Exception as e:
                print(f"   ⚠️ Fallo OCR en página {i + 1} del splitter: {e}")

        # 3. Analizar: ¿Hay firma de algún proveedor conocido?
        analisis = analizar_documento(text)
        nuevo_proveedor = analisis.get("proveedor_detectado")

        # --- LÓGICA DE GUILLOTINA ---
        if nuevo_proveedor:
            # ¡HAY FIRMA! -> PORTADA
            if writer_actual:
                print(f"   ✂️ Corte en pág {i + 1}. Fin del doc anterior ({proveedor_actual}).")
                ruta = _guardar_fragmento(writer_actual, proveedor_actual, pagina_inicio_actual, carpeta_temporal)
                archivos_generados.append(ruta)

            # Nuevo documento
            writer_actual = PdfWriter()
            writer_actual.add_page(page)
            proveedor_actual = nuevo_proveedor
            pagina_inicio_actual = i

        else:
            # CONTINUACIÓN
            if writer_actual:
                writer_actual.add_page(page)
            else:
                # Documento Huérfano al inicio
                writer_actual = PdfWriter()
                writer_actual.add_page(page)
                proveedor_actual = "Desconocido"
                pagina_inicio_actual = i

    # Guardar último bloque
    if writer_actual:
        ruta = _guardar_fragmento(writer_actual, proveedor_actual, pagina_inicio_actual, carpeta_temporal)
        archivos_generados.append(ruta)
        print(f"   🏁 Guardado bloque final ({proveedor_actual}).")

    return archivos_generados


def _guardar_fragmento(writer, proveedor, indice_pag, carpeta):
    """Escribe el PDF temporal en disco"""
    nombre = f"SPLIT_Pag{indice_pag}_{proveedor}.pdf"
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "wb") as f:
        writer.write(f)
    return ruta