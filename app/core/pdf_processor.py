import logging
import os

from pypdf import PdfReader
from app.config import POPPLER_PATH
from app.core.ocr_engine import ocr_engine, OCR_AVAILABLE, convert_from_path, np

logger = logging.getLogger(__name__)


def extraer_texto_pdf(ruta_archivo, forzar_ocr=False):
    """
    Extrae texto del PDF.
    - Modo Rápido (Default): Usa pypdf.
    - Modo OCR: Usa PaddleOCR + Pre-procesamiento de imagen.
    """
    if not os.path.exists(ruta_archivo):
        return None, "Archivo no encontrado"

    # ==========================================
    # MODO 1: OCR DEEP LEARNING (PADDLEOCR)
    # ==========================================
    if forzar_ocr:
        if not OCR_AVAILABLE:
            return None, "Librerías OCR no instaladas."
        if not os.path.exists(POPPLER_PATH):
            return None, f"Falta Poppler: {POPPLER_PATH}"

        try:
            logger.info("Motor Deep Learning arrancando... (Procesando imagen)")
            images = convert_from_path(ruta_archivo, poppler_path=POPPLER_PATH)

            texto_completo = ""
            for img in images:
                # 1. Convertir imagen PIL a Array de Numpy (Formato PaddleOCR)
                img_array = np.array(img)

                # 2. Inferencia (Reconocimiento)
                resultados = ocr_engine.ocr(img_array)

                # 3. Extraer solo el texto (Paddle devuelve coordenadas y confianza)
                if resultados and resultados[0]:
                    for linea in resultados[0]:
                        texto_completo += linea[1][0] + "\n"

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
            except Exception:
                return None, "PDF Encriptado"

        for page in reader.pages:
            t = page.extract_text()
            if t:
                texto_completo += t + "\n"

        if len(texto_completo.strip()) < 10:
            return None, "PDF vacío o imagen (Activa OCR)"

        return texto_completo, None

    except Exception as e:
        return None, f"Error lectura nativa: {str(e)}"
