from app.core import ocr_utils
from app.core.ocr_utils import extraer_texto_pagina, UMBRAL_TEXTO_NATIVO


class PaginaFalsa:
    """Simula una página de pypdf."""

    def __init__(self, texto):
        self._texto = texto

    def extract_text(self):
        return self._texto


class PaginaRota:
    def extract_text(self):
        raise RuntimeError("pdf corrupto")


def test_texto_nativo_suficiente_no_intenta_ocr():
    # Si intentara OCR petaría: la ruta no existe
    texto = "x" * (UMBRAL_TEXTO_NATIVO + 10)
    resultado = extraer_texto_pagina(PaginaFalsa(texto), "/no/existe.pdf", 0, usar_ocr=True)
    assert resultado == texto


def test_usar_ocr_false_devuelve_nativo_aunque_sea_corto():
    resultado = extraer_texto_pagina(PaginaFalsa("corto"), "/no/existe.pdf", 0, usar_ocr=False)
    assert resultado == "corto"


def test_ocr_no_disponible_devuelve_nativo(monkeypatch):
    monkeypatch.setattr(ocr_utils, "ocr_disponible", lambda: False)
    resultado = extraer_texto_pagina(PaginaFalsa("corto"), "/no/existe.pdf", 0, usar_ocr=True)
    assert resultado == "corto"


def test_pagina_rota_devuelve_vacio(monkeypatch):
    monkeypatch.setattr(ocr_utils, "ocr_disponible", lambda: False)
    resultado = extraer_texto_pagina(PaginaRota(), "/no/existe.pdf", 0, usar_ocr=True)
    assert resultado == ""
