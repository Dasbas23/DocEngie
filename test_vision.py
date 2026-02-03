from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
import os
from app.config import POPPLER_PATH

# --- CONFIGURACIÓN ---
# Pon aquí el PDF de Europart que te da problemas
RUTA_PDF = r"C:\Users\Marius\Downloads\test10p\SVIMPRESION19_ZARAGOZA_OFICINA TECNICA_1312_001.pdf"
CARPETA_SALIDA = os.path.join(os.path.dirname(os.path.abspath(RUTA_PDF)),"debug_vision")

if not os.path.exists(RUTA_PDF):
    print(f"❌ No encuentro el archivo: {RUTA_PDF}")
    exit()

os.makedirs(CARPETA_SALIDA, exist_ok=True)

print(f"🔬 INICIANDO DIAGNÓSTICO DE VISIÓN")
print(f"Objetivo: {RUTA_PDF}")

try:
    # 1. Convertir PDF a Imagen (Igual que hace la app)
    images = convert_from_path(RUTA_PDF, poppler_path=POPPLER_PATH, first_page=1, last_page=1)
    img_original = images[0]

    # Guardamos la original para comparar
    img_original.save(os.path.join(CARPETA_SALIDA, "1_original.png"))
    print("✅ Guardada: 1_original.png")

    # --- SIMULACIÓN DE TU PROCESO ACTUAL ---
    # Paso 1: Escala de grises
    img_gray = img_original.convert('L')
    img_gray.save(os.path.join(CARPETA_SALIDA, "2_grises.png"))

    # Paso 2: Contraste
    enhancer = ImageEnhance.Contrast(img_gray)
    img_contrast = enhancer.enhance(2)  # Tu valor actual
    img_contrast.save(os.path.join(CARPETA_SALIDA, "3_contraste.png"))

    # Paso 3: Binarización (El culpable probable)
    # Tu valor actual es 200. Probamos varios para que elijas el mejor.
    umbrales = [10,150,180,250]

    print("\n🧪 Generando pruebas de umbralización...")
    for umbral in umbrales:
        # Si el pixel es menor que el umbral -> Negro (0), si no -> Blanco (255)
        fn_thresh = lambda x: 0 if x < umbral else 255
        img_bin = img_contrast.point(fn_thresh, '1')

        nombre = f"4_binarizado_umbral_{umbral}.png"
        img_bin.save(os.path.join(CARPETA_SALIDA, nombre))
        print(f"   📸 Generada prueba: {nombre}")

    print(f"\n🏁 DIAGNÓSTICO FINALIZADO.")
    print(f"Ve a la carpeta '{CARPETA_SALIDA}' y mira las imágenes.")
    print("Busca aquella donde el fondo gris haya desaparecido (blanco) y las letras sigan negras.")

except Exception as e:
    print(f"💥 Error: {e}")