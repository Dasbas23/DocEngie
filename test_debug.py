# Este script simula lo que hará la app final, pero en consola.
# Úsalo para probar Regex nuevas sin abrir la interfaz gráfica.

import os
from app.core.pdf_processor import extraer_texto_pdf
from app.core.parser import analizar_documento

# --- CONFIGURACIÓN ---
# Pon aquí la ruta de tu PDF real de prueba
RUTA_PDF_PRUEBA = r"C:\Users\marius.ion\Downloads\test\Volvo_Albaranes\2026-02-02_7360166.pdf"


# Colores para la consola (Opcional, pero mola)
class Colores:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


print(f"{Colores.HEADER}--- INICIANDO DEBUGGER DE CLASIFICACIÓN ---{Colores.ENDC}")
print(f"Archivo objetivo: {Colores.OKCYAN}{RUTA_PDF_PRUEBA}{Colores.ENDC}")

# 1. Probar lectura
texto, error = extraer_texto_pdf(RUTA_PDF_PRUEBA, forzar_ocr=True)


if error:
    print(f"{Colores.FAIL}❌ ERROR DE LECTURA: {error}{Colores.ENDC}")
else:
    print(f"{Colores.OKGREEN}✅ LECTURA EXITOSA.{Colores.ENDC}")
    print("-" * 50)
    # Mostramos todos los caracteres para ver qué ve Python realmente
    print(f"{Colores.OKBLUE}{texto}{Colores.ENDC}")
    print("-" * 50)

    # 2. Probar Análisis
    print(f"\n{Colores.BOLD}🔍 ANALIZANDO CON REGEX...{Colores.ENDC}")
    resultado = analizar_documento(texto)

    print(f"\n{Colores.HEADER}📊 RESULTADOS:{Colores.ENDC}")

    prov = resultado.get('proveedor_detectado')
    if prov:
        print(f"Proveedor: {Colores.OKGREEN}{prov}{Colores.ENDC}")
    else:
        print(f"Proveedor: {Colores.FAIL}NO DETECTADO{Colores.ENDC}")

    # Ahora buscamos las nuevas claves de la V1.1
    doc_id = resultado.get('id_documento')
    fecha = resultado.get('fecha_documento')
    carpeta = resultado.get('carpeta_destino')

    print(f"Documento: {Colores.OKCYAN}{doc_id}{Colores.ENDC}")
    print(f"Fecha:     {Colores.OKCYAN}{fecha}{Colores.ENDC}")
    print(f"Destino:   {carpeta}")

    if resultado.get('log_info'):
        print(f"Log Info:  {Colores.WARNING}{resultado['log_info']}{Colores.ENDC}")

print(f"\n{Colores.HEADER}--- FIN DEL TEST ---{Colores.ENDC}")