"""
Módulo centralizado para el motor OCR (PaddleOCR).
Evita inicializar múltiples instancias del modelo en memoria.
"""
import logging
import os

# Workaround: PaddlePaddle 3.3.0 tiene un bug en la conversión PIR-to-oneDNN
# que causa "ConvertPirAttribute2RuntimeAttribute not support" en CPU.
# Desactivar oneDNN evita el crash. Debe estar ANTES de importar paddle.
# Ref: https://github.com/PaddlePaddle/Paddle/issues/77340
os.environ.setdefault("FLAGS_use_mkldnn", "0")

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
