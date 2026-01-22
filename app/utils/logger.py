import csv
import os
from datetime import datetime
from app.config import BASE_DIR  # <-- Importamos la ruta base segura

# Construimos la ruta absoluta: .../pdf_classifier_app/data/logs/historial.csv
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "historial_procesos.csv")


def inicializar_csv():
    """Crea el archivo CSV y la cabecera si no existen"""
    # Asegura que la carpeta logs existe
    os.makedirs(LOG_DIR, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Fecha", "Archivo Original", "Proveedor", "Pedido/Doc", "Estado", "Ruta Final"])


def registrar_evento(origen, resultado_analisis, ruta_final, exito_movimiento):
    """Escribe una nueva línea en el CSV"""
    inicializar_csv()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    archivo_orig = os.path.basename(origen)
    prov = resultado_analisis.get("proveedor_detectado", "N/A")
    # Guardamos el ID del documento o el pedido, lo que hayamos encontrado
    doc_id = resultado_analisis.get("id_documento") or resultado_analisis.get("numero_pedido", "N/A")

    if exito_movimiento:
        estado = "OK" if prov != "N/A" else "REVISIÓN MANUAL"
    else:
        estado = "ERROR SISTEMA"

    try:
        with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([fecha, archivo_orig, prov, doc_id, estado, ruta_final])
    except Exception as e:
        print(f"❌ Error crítico escribiendo log: {e}")