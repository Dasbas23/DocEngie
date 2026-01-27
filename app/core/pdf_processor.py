from pypdf import PdfReader
import os
import sys
from app.config import TESSERACT_CMD, POPPLER_PATH

# Importación condicional de librerías pesadas
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extraer_texto_pdf(ruta_archivo, forzar_ocr=False):
    """
    Extrae texto del PDF.
    - Modo Rápido (Default): Usa pypdf.
    - Modo OCR (forzar_ocr=True): Usa Tesseract + Poppler locales.
    """
    if not os.path.exists(ruta_archivo):
        return None, "Archivo no encontrado"

    # ==========================================
    # MODO 1: OCR VISUAL (LENTO)
    # ==========================================
    if forzar_ocr:
        if not OCR_AVAILABLE:
            return None, "Librerías OCR no instaladas (pip install pytesseract pdf2image)"

        # 1. Validación de Binarios (Fontanería)
        if not os.path.exists(TESSERACT_CMD):
            return None, f"❌ NO se encuentra Tesseract en: {TESSERACT_CMD}"

        if not os.path.exists(POPPLER_PATH):
            return None, f"❌ NO se encuentra Poppler en: {POPPLER_PATH}"

        # 2. Configuración del motor
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

        try:
            print(f"   👁️ Motor OCR arrancando... (Poppler: {POPPLER_PATH})")

            # Convertimos PDF a lista de imágenes (Página por página)
            # poppler_path es CRÍTICO en Windows
            images = convert_from_path(ruta_archivo, poppler_path=POPPLER_PATH)

            texto_completo = ""
            for i, img in enumerate(images):
                # Leemos la imagen con Tesseract
                # config='--psm 6' asume que es un bloque de texto uniforme (bueno para facturas)
                texto_pagina = pytesseract.image_to_string(img, lang='spa', config='--psm 6')
                texto_completo += texto_pagina + "\n"

            if not texto_completo.strip():
                return None, "OCR finalizado pero no se detectó texto legible."

            return texto_completo, None

        except Exception as e:
            return None, f"Fallo Crítico Motor OCR: {str(e)}"

    # ==========================================
    # MODO 2: NATIVO (RÁPIDO)
    # ==========================================
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
            return None, "PDF parece vacío o es una imagen. (Activa 'Habilitar OCR')"

        return texto_completo, None

    except Exception as e:
        return None, f"Error lectura nativa: {str(e)}"