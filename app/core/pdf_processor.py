from pypdf import PdfReader
import os
import sys
from app.config import TESSERACT_CMD, POPPLER_PATH

# Importación condicional
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter # <--- NUEVO

    OCR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AVISO DEBUG: Falló la importación de OCR. Causa: {e}")
    OCR_AVAILABLE = False
except Exception as e:
    print(f"⚠️ AVISO DEBUG: Error inesperado importando OCR. Causa: {e}")
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

        if not os.path.exists(TESSERACT_CMD): return None, f"❌ Falta Tesseract: {TESSERACT_CMD}"
        if not os.path.exists(POPPLER_PATH): return None, f"❌ Falta Poppler: {POPPLER_PATH}"

        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

        try:
            print(f"   👁️ Motor OCR arrancando... (Procesando imagen)")
            images = convert_from_path(ruta_archivo, poppler_path=POPPLER_PATH)

            texto_completo = ""
            for img in images:
                # --- FASE DE MEJORA DE IMAGEN ---
                # 1. Convertir a escala de grises
                img = img.convert('L')
                # 2. Aumentar contraste
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2)

                #Filtro imágen en los bordes
                img = img.filter(ImageFilter.SHARPEN)

                # [CRÍTICO] Umbral 10 descubierto en pruebas.
                # Elimina fondos grises (Europart) dejando solo tinta negra fuerte.
                UMBRAL_CORTE = 10
                img = img.point(lambda x: 0 if x < UMBRAL_CORTE else 255, '1')



                # --- LECTURA ---
                # config='--psm 3' (Auto-detectar bloques, bueno para docs torcidos)
                # config='--psm 6' (Bloque uniforme de texto) suele ir mejor para listas/tablas
                # config='--psm 11' (Texto disperso) a veces encuentra cosas perdidas
                # lang='spa' es vital si tienes el paquete español instalado
                texto_pagina = pytesseract.image_to_string(img, lang='spa', config='--psm 3')
                texto_completo += texto_pagina + "\n"

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