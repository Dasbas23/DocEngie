import os
import shutil
from app.core.splitter import dividir_pdf_por_proveedor

# --- CONFIGURACIÓN ---
# Ruta a tu PDF Frankenstein
PDF_MASIVO = "lote_masivo_test.pdf"
CARPETA_TEMP = "data/temp_split"

# Limpieza previa (opcional)
if os.path.exists(CARPETA_TEMP):
    shutil.rmtree(CARPETA_TEMP)

print("🧪 --- INICIANDO TEST DE SPLITTER (V2.1) ---")

if not os.path.exists(PDF_MASIVO):
    print(f"❌ No encuentro el archivo {PDF_MASIVO}. Ponlo en la raíz del proyecto.")
    exit()

# 1. EJECUTAR EL CORTE
archivos = dividir_pdf_por_proveedor(PDF_MASIVO, CARPETA_TEMP)

print("\n📦 --- RESULTADOS ---")
if archivos:
    print(f"✅ Se han generado {len(archivos)} documentos individuales:")
    for arch in archivos:
        print(f"   📄 {arch}")

    print("\n💡 AHORA: Si esto fuera la app real, cada uno de estos archivos")
    print("   pasaría por el proceso normal de clasificación (Lectura -> Regex -> Mover).")
else:
    print("⚠️ No se generó ningún archivo. ¿El PDF tiene texto?")