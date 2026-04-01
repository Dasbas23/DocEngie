"""
Módulo centralizado para el motor OCR (PaddleOCR).
Evita inicializar múltiples instancias del modelo en memoria.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    from pdf2image import convert_from_path
    import numpy as np

    # Instancia única: use_angle_cls=True auto-rota texto, lang='es' para español
    ocr_engine = PaddleOCR(use_angle_cls=True, lang='es')
    OCR_AVAILABLE = True
    logger.info("Motor OCR (PaddleOCR) inicializado correctamente.")
except ImportError as e:
    logger.warning(f"Librerías OCR no disponibles: {e}")
    ocr_engine = None
    OCR_AVAILABLE = False
    convert_from_path = None
    np = None
