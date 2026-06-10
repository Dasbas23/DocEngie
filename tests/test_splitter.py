import os

from pypdf import PdfWriter

from app.core.splitter import dividir_pdf_por_proveedor


def crear_pdf_en_blanco(ruta, paginas=2):
    w = PdfWriter()
    for _ in range(paginas):
        w.add_blank_page(width=200, height=200)
    with open(ruta, "wb") as f:
        w.write(f)


def test_contrato_de_salida(tmp_path):
    pdf = tmp_path / "lote.pdf"
    crear_pdf_en_blanco(str(pdf), paginas=2)

    resultados = dividir_pdf_por_proveedor(str(pdf), str(tmp_path / "tmp"), usar_ocr=False)

    # 2 páginas en blanco sin proveedor -> un único grupo huérfano
    assert len(resultados) == 1
    fragmento = resultados[0]
    assert set(fragmento.keys()) == {"ruta", "texto", "analisis"}
    assert os.path.exists(fragmento["ruta"])
    assert "Desconocido" in os.path.basename(fragmento["ruta"])
    assert fragmento["analisis"]["proveedor_detectado"] is None


def test_pdf_inexistente_devuelve_lista_vacia(tmp_path):
    assert dividir_pdf_por_proveedor(str(tmp_path / "no.pdf"), str(tmp_path)) == []
