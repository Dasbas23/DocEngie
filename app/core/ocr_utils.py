"""
Única fuente de verdad para extraer texto de una página de PDF.
La usan el splitter y el clasificador para que ambos "vean" el mismo texto.
"""
import os

from app.config import TESSERACT_CMD, POPPLER_PATH

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import ImageEnhance, ImageFilter

    OCR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AVISO: Falló la importación de OCR. Causa: {e}")
    OCR_AVAILABLE = False

# Si el texto nativo de una página no llega a este nº de caracteres,
# se considera escaneada y se intenta OCR. (Antes solo se OCR-eaba si
# estaba 100% vacía, y páginas con restos de texto digital se colaban.)
UMBRAL_TEXTO_NATIVO = 50

# Configuración única de Tesseract para TODAS las fases.
OCR_CONFIG = '--psm 6'
OCR_LANG = 'spa'

# [CRÍTICO] Umbral 10 descubierto en pruebas.
# Elimina fondos grises (Europart) dejando solo tinta negra fuerte.
UMBRAL_BINARIO = 10

_aviso_tesseract_emitido = False


def ocr_disponible():
    """True si las librerías Python y el binario de Tesseract están listos."""
    return OCR_AVAILABLE and TESSERACT_CMD is not None and os.path.exists(TESSERACT_CMD)


def preprocesar_imagen(img):
    """Pre-procesado único: grises, contraste x2, sharpen, umbral binario."""
    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(2)
    img = img.filter(ImageFilter.SHARPEN)
    return img.point(lambda x: 0 if x < UMBRAL_BINARIO else 255, '1')


def ocr_imagen(img):
    """Aplica pre-procesado + Tesseract a una imagen PIL. Devuelve el texto."""
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    return pytesseract.image_to_string(
        preprocesar_imagen(img), lang=OCR_LANG, config=OCR_CONFIG
    )


def extraer_texto_pagina(page, ruta_pdf, indice, usar_ocr):
    """
    Extrae el texto de una página.

    page: objeto página de pypdf (reader.pages[indice])
    ruta_pdf: ruta del PDF original (pdf2image necesita el archivo)
    indice: índice 0-based de la página
    usar_ocr: si True y el texto nativo es escaso, intenta OCR
    """
    global _aviso_tesseract_emitido

    try:
        texto = page.extract_text() or ""
    except Exception:
        texto = ""

    if len(texto.strip()) >= UMBRAL_TEXTO_NATIVO or not usar_ocr:
        return texto

    if not ocr_disponible():
        if not _aviso_tesseract_emitido:
            print("⚠️ OCR no disponible (falta Tesseract). Continuando en modo nativo.")
            _aviso_tesseract_emitido = True
        return texto

    try:
        imagenes = convert_from_path(
            ruta_pdf,
            first_page=indice + 1,
            last_page=indice + 1,
            poppler_path=POPPLER_PATH,
        )
        for img in imagenes:
            texto += "\n" + ocr_imagen(img)
    except Exception as e:
        print(f"   ⚠️ Fallo OCR en página {indice + 1}: {e}")

    return texto
