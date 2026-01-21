import re

# ==========================================
# CONFIGURACIÓN DE RUTAS Y REGLAS
# ==========================================

# Aquí definimos las estrategias para cada proveedor.
# - 'firma': Una palabra o frase ÚNICA que solo aparece en los documentos de este proveedor (ej: su CIF, nombre empresa).
# - 'patron_pedido': Una Expresión Regular (Regex) para cazar el número.

PROVEEDORES = {
    "AMAZON_EJEMPLO": {
        "firma": ["Amazon EU S.a.r.l", "amzn"], # Lista de posibles firmas
        "patron_pedido": r"Orden de compra:\s*(\d{3}-\d{7}-\d{7})", # Ej: 404-1234567-1234567
        "carpeta_destino": "Amazon_Invoices"
    },
    "IKEA_EJEMPLO": {
        "firma": ["IKEA IBERICA", "Inter IKEA"],
        "patron_pedido": r"Ref\.\s*Pedido:\s*([A-Z]{2}-\d{4,6})", # Ej: Ref. Pedido: ES-9900
        "carpeta_destino": "Ikea_Orders"
    },
    # --- AÑADE AQUÍ TU PRIMER PROVEEDOR REAL PARA PROBAR ---
    "MI_PROVEEDOR_TEST": {
        "firma": ["NOMBRE_EMPRESA_REAL"],
        "patron_pedido": r"Nº\s*Albarán:\s*(\d+)", # Busca "Nº Albarán:" seguido de números
        "carpeta_destino": "Proveedor_Test"
    }
}

# Rutas por defecto (se pueden sobreescribir desde la GUI)
DEFAULT_INPUT_DIR = "./data/input"
DEFAULT_OUTPUT_DIR = "./data/output"
DEFAULT_ERROR_DIR = "./data/output/Revision_Manual"