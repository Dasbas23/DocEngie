from pypdf import PdfReader
import os
import sys

# Intentamos importar librerías de OCR. Si no están, no pasa nada.
try:
    import pytesseract
    from pdf2image import convert_from_path

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extraer_texto_pdf(ruta_archivo, forzar_ocr=False):
    """
    Extrae texto del PDF.
    - Modo Rápido (Default): Usa pypdf (texto nativo).
    - Modo Lento (forzar_ocr=True): Convierte a imagen y usa Tesseract.
    """
    if not os.path.exists(ruta_archivo):
        return None, "Archivo no encontrado"

    # --- MODO 1: OCR (LENTO) ---
    if forzar_ocr:
        if not OCR_AVAILABLE:
            return None, "Librerías OCR no instaladas (pip install pytesseract pdf2image)"

        # Configuración Tesseract (Si tienes el portable, ajusta la ruta aquí)
        # pytesseract.pytesseract.tesseract_cmd = r' ruta/a/tesseract.exe '

        try:
            print("👁️ Iniciando OCR visual (esto tardará)...")
            images = convert_from_path(ruta_archivo)
            texto_completo = ""
            for img in images:
                texto_completo += pytesseract.image_to_string(img)

            if not texto_completo.strip():
                return None, "OCR realizado pero no se detectó texto (imagen vacía?)"

            return texto_completo, None
        except Exception as e:
            # Si falla el OCR (ej: falta poppler), devolvemos error
            return None, f"Fallo en motor OCR: {str(e)}"

    # --- MODO 2: NATIVO (RÁPIDO) ---
    try:
        reader = PdfReader(ruta_archivo)
        texto_completo = ""

        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except:
                return None, "PDF Encriptado"

        for page in reader.pages:
            texto_pagina = page.extract_text()
            if texto_pagina:
                texto_completo += texto_pagina + "\n"

        # Validación: Si hay muy poco texto, sugerimos OCR
        if len(texto_completo.strip()) < 10:
            return None, "PDF parece vacío (¿Es una imagen? Prueba activar OCR)"

        return texto_completo, None

    except Exception as e:
        return None, f"Error crítico leyendo PDF: {str(e)}"