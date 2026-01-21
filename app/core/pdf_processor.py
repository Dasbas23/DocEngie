from pypdf import PdfReader
import os


def extraer_texto_pdf(ruta_archivo):
    """
    Abre un PDF y extrae todo el texto de todas sus páginas.
    Retorna el texto completo como un string.
    """
    if not os.path.exists(ruta_archivo):
        return None, "Archivo no encontrado"

    texto_completo = ""

    try:
        reader = PdfReader(ruta_archivo)

        # Verificar si está encriptado
        if reader.is_encrypted:
            try:
                reader.decrypt("")  # Intentar desencriptar si no tiene pass
            except:
                return None, "PDF Encriptado/Protegido"

        # Leer páginas
        for page in reader.pages:
            texto_pagina = page.extract_text()
            if texto_pagina:
                texto_completo += texto_pagina + "\n"

        # Validación simple: Si hay muy poco texto, algo va mal (quizás es imagen sin OCR)
        if len(texto_completo.strip()) < 10:
            return None, "PDF parece vacío o es una imagen sin capa de texto"

        return texto_completo, None

    except Exception as e:
        return None, f"Error crítico leyendo PDF: {str(e)}"