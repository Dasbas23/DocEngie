import csv
import os
from datetime import datetime

LOG_FILE = "data/logs/historial_procesos.csv"


def inicializar_csv():
    """Crea el archivo CSV y la cabecera si no existen"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Fecha", "Archivo Original", "Proveedor", "Pedido", "Estado", "Ruta Final"])


def registrar_evento(origen, resultado_analisis, ruta_final, exito_movimiento):
    """Escribe una nueva línea en el CSV"""
    inicializar_csv()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    archivo_orig = os.path.basename(origen)
    prov = resultado_analisis.get("proveedor_detectado", "N/A")
    pedido = resultado_analisis.get("numero_pedido", "N/A")

    if exito_movimiento:
        estado = "OK" if prov != "N/A" else "REVISIÓN MANUAL"
    else:
        estado = "ERROR SISTEMA"

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([fecha, archivo_orig, prov, pedido, estado, ruta_final])