from pypdf import PdfReader, PdfWriter
from app.core.parser import analizar_documento
import os


def dividir_pdf_por_proveedor(ruta_pdf_masivo, carpeta_temporal):
    """
    Recorre un PDF multipágina.
    Estrategia de Guillotina: Si detecta un proveedor en una página,
    asume que es el inicio de un nuevo documento.
    Las páginas sin firma se añaden al documento anterior (continuación).

    Retorna: Lista de rutas de los archivos generados.
    """
    if not os.path.exists(ruta_pdf_masivo):
        return []

    reader = PdfReader(ruta_pdf_masivo)
    archivos_generados = []

    writer_actual = None
    proveedor_actual = "Desconocido"
    pagina_inicio_actual = 0

    # Asegurar que existe la carpeta temporal (ej: data/tmp_split)
    os.makedirs(carpeta_temporal, exist_ok=True)

    print(f"🔄 Analizando archivo masivo de {len(reader.pages)} páginas...")

    for i, page in enumerate(reader.pages):
        # Extraer texto para ver si es una portada de proveedor
        try:
            text = page.extract_text()
        except:
            text = ""

        # Usamos nuestro parser existente solo para identificar proveedor
        analisis = analizar_documento(text)
        nuevo_proveedor = analisis.get("proveedor_detectado")

        # --- LÓGICA DE CORTE ---
        # Si encontramos una firma de proveedor, asumimos que empieza un albarán nuevo.
        if nuevo_proveedor:
            # 1. Si ya teníamos uno abierto, lo cerramos y guardamos
            if writer_actual:
                ruta_guardada = _guardar_fragmento(writer_actual, proveedor_actual, pagina_inicio_actual,
                                                   carpeta_temporal)
                archivos_generados.append(ruta_guardada)
                print(f"   ✂️ Corte detectado en pág {i}. Guardado anterior ({proveedor_actual}).")

            # 2. Empezamos uno nuevo con esta página
            writer_actual = PdfWriter()
            writer_actual.add_page(page)
            proveedor_actual = nuevo_proveedor
            pagina_inicio_actual = i

        else:
            # Si NO detectamos proveedor...
            if writer_actual:
                # ...asumimos que es página 2, 3, etc. del documento actual
                writer_actual.add_page(page)
            else:
                # Caso raro: Las primeras páginas del PDF no tienen firma conocida.
                # Creamos un documento "Huérfano"
                writer_actual = PdfWriter()
                writer_actual.add_page(page)
                proveedor_actual = "Desconocido"
                pagina_inicio_actual = i

    # IMPORTANTE: Guardar el último bloque que queda abierto al salir del bucle
    if writer_actual:
        ruta_guardada = _guardar_fragmento(writer_actual, proveedor_actual, pagina_inicio_actual, carpeta_temporal)
        archivos_generados.append(ruta_guardada)
        print(f"   🏁 Guardado bloque final ({proveedor_actual}).")

    return archivos_generados


def _guardar_fragmento(writer, proveedor, indice_pag, carpeta):
    """Función auxiliar para escribir el archivo en disco"""
    # Nombre temporal: TEMP_Pagina0_CBM.pdf
    nombre = f"TEMP_Pag{indice_pag}_{proveedor}.pdf"
    ruta = os.path.join(carpeta, nombre)

    with open(ruta, "wb") as f:
        writer.write(f)

    return ruta