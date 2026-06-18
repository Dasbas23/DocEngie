# 📂 DocEngie | Intelligent Document Classifier

![Status](https://img.shields.io/badge/Status-Production_Ready-success) ![Python](https://img.shields.io/badge/Python-3.14-blue) ![OCR](https://img.shields.io/badge/OCR-Tesseract%2FNative-orange)

> **Solución de escritorio High-Performance para la automatización administrativa.** Procesa, clasifica y renombra documentación empresarial mediante un pipeline híbrido de OCR y Expresiones Regulares.

## 📖 Descripción del Problema & Solución
En entornos administrativos, la clasificación manual de albaranes consume horas y genera errores humanos. **DocEngie** actúa como un robot ofimático que:
1.  **Ingesta** archivos PDF (nativos o escaneados).
2.  **Aplica OCR/Parsing** para entender el contenido.
3.  **Detecta proveedores** mediante huellas digitales (CIF/NIF/Keywords).
4.  **Renombra y Mueve** los archivos siguiendo el estándar ISO 8601.

## 🚀 Ingeniería y Características Clave (The Flex)

### 🧠 Pipeline Híbrido de Extracción (OCR + Native)
A diferencia de soluciones simples, DocEngie implementa un sistema inteligente de lectura:
* **Intento 1 (Fast-Path):** Intenta extracción nativa ultrarrápida (0.1s) para PDFs digitales.
* **Intento 2 (Deep-Scan):** Si el PDF es una imagen escaneada, activa el motor **OCR** para "leer" los píxeles, garantizando que ningún documento se quede sin procesar.

### 🧵 Arquitectura Concurrente (Non-Blocking UI)
Implementación de **Multithreading** para desacoplar la lógica de procesamiento (CPU Bound) del hilo de la interfaz gráfica (Main Loop).
* *Resultado:* La interfaz `customtkinter` nunca se congela, incluso procesando lotes de 500+ documentos, manteniendo una barra de progreso fluida en tiempo real.

### 🧩 Configuración "Hot-Swap"
Las reglas de negocio no están "hardcodeadas".
* Se utiliza un motor de reglas basado en `JSON` externo.
* Permite añadir nuevos proveedores o cambiar Regex de detección **sin recompilar** ni detener el software.

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Descripción |
| :--- | :--- | :--- |
| **Core** | Python 3.14 | Lógica principal y orquestación. |
| **GUI** | CustomTkinter | Wrapper moderno de Tcl/Tk para Modo Oscuro/Light nativo. |
| **Visión** | Tesseract / PyPDF | Motor de reconocimiento óptico y parsing de estructuras. |
| **Pattern** | Regex Avanzado | Algoritmos de "Doble Ancla" para localizar fechas y CIFs con ruido. |
| **Build** | PyInstaller | Compilación a binario `.exe` standalone (sin dependencias para el cliente). |

## ⚙️ Flujo de Trabajo (Workflow)
1.  **Input:** Selección de carpeta origen (mezcla de imágenes y PDFs).
2.  **Splitting:** Si llega un PDF multipágina, se atomiza en hojas individuales.
3.  **Processing:** * Extracción de metadatos (Proveedor, Nº Albarán, Fecha).
    * *Fallback:* Si falla la fecha, se usa `SysDate` con flag de advertencia.
4.  **Output:** * ✅ Éxito: Renombrado `YYYY-MM-DD_Proveedor_NDoc.pdf` -> Carpeta Destino.
    * ⚠️ Fallo: Carpeta `revisión_manual` para auditoría humana (Logs generados).

## 📂 Estructura del Proyecto (Clean Architecture)
```text
DocEngie/
├── core/                   # Backend Logic
│   ├── engine_ocr.py       # Wrapper de visión artificial
│   ├── regex_parser.py     # Lógica de extracción de datos
│   └── file_manager.py     # Operaciones OS (shutil/pathlib)
├── gui/                    # Frontend Logic
│   ├── workers.py          # Hilos en segundo plano (Background Tasks)
│   └── components.py       # Widgets personalizados
├── data/
│   ├── rules/proveedores.json  # Reglas dinámicas
│   └── logs/               # Registro de operaciones
└── main.py                 # Entry Point 
```
>### \✏️/ Posibles mejoras.
>> - Migrar a UV (sencillo)
>> - Tests reales
>> - Hacer que se utilice aceleración por GPU si está disponible 🚀. 
>>> Es cierto que paddleOCR si admite gpu pero si no está disponible gasta muchos recursos. 
>>> Tesseract es bastante eficiente desde que Fable me hizo los ajustes finos