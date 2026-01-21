# Este script simula lo que hará la app final, pero en consola.
from app.core.pdf_processor import extraer_texto_pdf
from app.core.parser import analizar_documento
import os

# --- PON AQUÍ LA RUTA DE TU PDF REAL ---
RUTA_PDF_PRUEBA = r"C:\Users\marius.ion\Documents\Albaranes_scan\ocr.pdf"
# (Asegúrate de copiar un pdf real a esa carpeta o pon la ruta absoluta)

print(f"--- INICIANDO TEST PARA: {RUTA_PDF_PRUEBA} ---")

# 1. Probar lectura
texto, error = extraer_texto_pdf(RUTA_PDF_PRUEBA)

if error:
    print(f"❌ ERROR DE LECTURA: {error}")
else:
    print("✅ LECTURA EXITOSA. Primeros 200 caracteres:")
    print("-" * 20)
    print(texto[:200])  # Muestra el principio para ver si se lee bien
    print("-" * 20)

    # 2. Probar Análisis
    print("🔍 ANALIZANDO...")
    resultado = analizar_documento(texto)

    print("\n📊 RESULTADOS:")
    print(f"Proveedor: {resultado['proveedor_detectado']}")
    print(f"Pedido:    {resultado['numero_pedido']}")
    print(f"Estado:    {resultado['confianza']}")