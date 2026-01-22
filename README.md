📂 Clasificador Inteligente de Albaranes (PDF Auto-Classifier)

Proyecto Final DAM | Automatización de procesos administrativos mediante Python, Regex y Procesamiento de Documentos.

📖 Descripción

Esta aplicación de escritorio automatiza la tediosa tarea de clasificar cientos de albaranes y facturas escaneadas.
El sistema lee PDFs nativos, identifica al proveedor mediante huellas digitales únicas (CIF/NIF), extrae metadatos clave (Nº Documento y Fecha) y renombra los archivos siguiendo el estándar ISO 8601, moviéndolos a su carpeta correspondiente.

Problema que resuelve: Elimina el error humano y reduce horas de trabajo manual en departamentos de logística/contabilidad.

🚀 Características Clave (Technical Highlights)

⚡ Motor Ligero (Zero-Binary Dependency): Migrado de OCR pesado (Tesseract) a extracción nativa con pypdf, reduciendo el tiempo de proceso de 3s a 0.1s por archivo.

🧠 Configuración Dinámica (Hot-Swap): Las reglas de negocio (Regex de proveedores) están desacopladas en data/proveedores.json. Se pueden añadir nuevos proveedores sin tocar el código fuente.

🧵 Interfaz Reactiva: Implementación de Threading para separar la carga de trabajo (Backend) del hilo de la interfaz (Frontend), evitando congelamientos (UI Freezing).

🛡️ Estrategia de Parsing "Doble Ancla": Algoritmo robusto que localiza datos basándose en la estructura tabular y fechas, limpiando "ruido" típico de OCR (espacios fantasma, puntos extra).

🛠️ Stack Tecnológico

Lenguaje: Python 3.14

Interfaz (GUI): customtkinter (Wrapper moderno de Tcl/Tk)

Procesamiento PDF: pypdf

Lógica de Negocio: Expresiones Regulares (Regex) avanzadas.

Gestión de Archivos: shutil, os, pathlib.

📂 Arquitectura del Proyecto

El proyecto sigue una arquitectura modular (Clean Architecture simplificada) para facilitar la escalabilidad y el mantenimiento:

pdf_classifier_app/
├── app/
│   ├── core/           # Lógica de Negocio Pura (Backend)
│   │   ├── parser.py           # Motor de análisis Regex
│   │   ├── pdf_processor.py    # Extracción de texto raw
│   │   └── provider_manager.py # CRUD de reglas JSON
│   ├── gui/            # Interfaz de Usuario (Frontend)
│   │   └── main_window.py      # Lógica de la ventana principal
│   └── utils/          # Herramientas transversales (Logger, CSV)
├── data/               # Persistencia y Configuración
│   ├── input/          # Bandeja de entrada (simulada)
│   ├── output/         # Salida clasificada
│   └── proveedores.json # Base de datos de reglas
└── main.py             # Punto de entrada (Entry Point)


⚙️ Instalación y Uso

Clonar el repositorio:

git clone [https://github.com/tu-usuario/pdf-classifier.git](https://github.com/tu-usuario/pdf-classifier.git)
cd pdf-classifier


Instalar dependencias:

pip install -r requirements.txt


Ejecutar:

python main.py


Configuración de Proveedores:
Edita el archivo data/proveedores.json para añadir nuevas reglas de regex para tus facturas.

📈 Roadmap

[x] v1.0: MVP con Tesseract (Deprecated).

[x] v1.1: Migración a pypdf y Configuración JSON externa.

[ ] v2.0: Compilación a .EXE portable y Editor Visual de Reglas.

Autor: Marius Ion
Desarrollado como parte del Grado Superior en Desarrollo de Aplicaciones Multiplataforma (DAM).