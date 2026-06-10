from pypdf import PdfReader
import os
from app.config import POPPLER_PATH
from app.core import ocr_utils

# Importación condicional
try:
    from pdf2image import convert_from_path

    OCR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AVISO DEBUG: Falló la importación de OCR. Causa: {e}")
    OCR_AVAILABLE = False


def extraer_texto_pdf(ruta_archivo, forzar_ocr=False):
    """
    Extrae texto del PDF.
    - Modo Rápido (Default): Usa pypdf.
    - Modo OCR: Usa Tesseract + Pre-procesamiento de imagen.
    """
    if not os.path.exists(ruta_archivo):
        return None, "Archivo no encontrado"

    # ==========================================
    # MODO 1: OCR VISUAL
    # ==========================================
    if forzar_ocr:
        if not OCR_AVAILABLE:
            return None, "Librerías OCR no instaladas."

        if not ocr_utils.ocr_disponible():
            return None, "❌ Falta Tesseract (en Linux: sudo dnf install tesseract tesseract-langpack-spa)"
        if POPPLER_PATH is not None and not os.path.exists(POPPLER_PATH):
            return None, f"❌ Falta Poppler: {POPPLER_PATH}"

        try:
            print(f"   👁️ Motor OCR arrancando... (Procesando imagen)")
            images = convert_from_path(ruta_archivo, poppler_path=POPPLER_PATH)

            texto_completo = ""
            for img in images:
                # Pre-procesado + Tesseract unificados (mismos que el splitter)
                texto_completo += ocr_utils.ocr_imagen(img) + "\n"

            if not texto_completo.strip():
                return None, "OCR: Imagen vacía o ilegible."

            return texto_completo, None

        except Exception as e:
            return None, f"Fallo Crítico Motor OCR: {str(e)}"

    # ==========================================
    # MODO 2: NATIVO
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
            t = page.extract_text()
            if t: texto_completo += t + "\n"

        if len(texto_completo.strip()) < 10:
            return None, "PDF vacío o imagen (Activa OCR)"

        return texto_completo, None

    except Exception as e:
        return None, f"Error lectura nativa: {str(e)}"