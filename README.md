# 📂 DocEngie | Intelligent Document Classifier

![Status](https://img.shields.io/badge/Status-Production_Ready-success) ![Python](https://img.shields.io/badge/Python-3.14-blue) ![OCR](https://img.shields.io/badge/OCR-Tesseract%2FNative-orange) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

> **Solución de escritorio High-Performance para la automatización administrativa.** Procesa, clasifica y renombra documentación empresarial (albaranes y facturas) mediante un pipeline híbrido de OCR y Expresiones Regulares.

## 📖 Descripción del Problema & Solución

En entornos administrativos, la clasificación manual de albaranes consume horas y genera errores humanos. **DocEngie** actúa como un robot ofimático que:

1. **Ingesta** archivos PDF (nativos o escaneados).
2. **Atomiza** lotes multipágina en sub-documentos por proveedor (estrategia "Guillotina").
3. **Aplica OCR/Parsing** para entender el contenido.
4. **Detecta proveedores** mediante huellas digitales (CIF/NIF/Keywords).
5. **Renombra y Mueve** los archivos siguiendo el estándar ISO 8601 a su carpeta destino.

## 🚀 Ingeniería y Características Clave (The Flex)

### 🧠 Pipeline Híbrido de Extracción (OCR + Native)

A diferencia de soluciones simples, DocEngie implementa un sistema inteligente de lectura:

* **Intento 1 (Fast-Path):** Extracción nativa con `pypdf` (sub-segundo) para PDFs digitales.
* **Intento 2 (Deep-Scan):** Si el PDF es una imagen escaneada, activa el motor **Tesseract** con un pre-procesado agresivo (grises → contraste ×2 → SHARPEN → binarización con umbral 10) para "leer" los píxeles incluso sobre fondos grises problemáticos.

### ✂️ Splitter "Guillotina" (Lote → Sub-documentos)

Los escáneres de oficina suelen entregar **un solo PDF** con N albaranes de N proveedores apilados. El splitter trata cada página cuya firma coincide con un proveedor conocido como **inicio de un documento nuevo**, y agrupa las páginas siguientes sin firma como continuación. Resultado: un lote escaneado se convierte automáticamente en sub-PDFs limpios, uno por albarán.

### 🧵 Arquitectura Concurrente (Non-Blocking UI)

Implementación de **Multithreading** (worker `daemon=True`) para desacoplar la lógica de procesamiento (CPU-bound) del hilo principal de la interfaz gráfica.

* *Resultado:* La interfaz `customtkinter` permanece responsiva durante todo el proceso, registrando eventos en tiempo real en una consola embebida.

### 🧩 Configuración "Hot-Swap"

Las reglas de negocio no están "hardcodeadas":

* Motor de reglas basado en `JSON` externo (`data/proveedores.json`).
* Permite añadir nuevos proveedores o ajustar Regex de detección **sin recompilar** ni redistribuir el binario.

### 📝 Trazabilidad (Audit Trail)

Cada sub-documento procesado se registra en `data/logs/historial_procesos.csv` con fecha, archivo origen, proveedor, número de documento, estado y ruta final — listo para auditoría.

## 🛠️ Stack Tecnológico

| Capa        | Tecnología       | Descripción                                                       |
| :---------- | :--------------- | :---------------------------------------------------------------- |
| **Core**    | Python 3.14      | Lógica principal y orquestación.                                  |
| **GUI**     | CustomTkinter    | Wrapper moderno de Tcl/Tk con tema oscuro/claro nativo.           |
| **Visión**  | Tesseract OCR    | Motor de reconocimiento óptico (lang `spa`, PSM 3).               |
| **PDF**     | pypdf + pdf2image| Lectura nativa y rasterización (vía Poppler) para el modo OCR.    |
| **Pattern** | Regex avanzado   | Patrones tolerantes a ruido OCR (`\s*` entre dígitos, doble ancla)|
| **Build**   | PyInstaller      | Compilación a binario `.exe` standalone para el cliente final.    |

## ⚡ Quickstart

```bash
# 1. Clonar el repo
git clone https://github.com/Dasbas23/DocEngie.git
cd DocEngie

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. (Solo si vas a usar OCR) Colocar binarios externos — ver sección siguiente

# 4. Lanzar la app
python main.py
```

## 📦 Dependencias Externas (Tesseract + Poppler)

OCR **no es pip-installable**: `pytesseract` y `pdf2image` son wrappers que invocan ejecutables nativos. DocEngie los busca en una carpeta `bin/` adyacente al ejecutable (modo `.exe`) o a la raíz del repo (modo script):

```text
DocEngie/
└── bin/
    ├── Tesseract-OCR/
    │   ├── tesseract.exe
    │   └── tessdata/
    │       └── spa.traineddata        ← OBLIGATORIO (idioma español)
    └── poppler/
        └── Library/
            └── bin/                   ← pdf2image apunta AQUÍ (carpeta, no .exe)
```

Las rutas exactas se configuran en `app/config.py`. Si `spa.traineddata` falta, el OCR se romperá en runtime — no hay preflight check.

## ⚙️ Flujo de Trabajo (Workflow)

```
folder ─► splitter ─► pdf_processor ─► parser ─► file_manager ─► logger
         (Guillotina)  (native|OCR)    (regex)   (rename+move)   (CSV)
```

1. **Input:** Carpeta origen con PDFs (nativos o escaneados; mezcla permitida).
2. **Splitting:** Cada PDF se atomiza por firma de proveedor en `<output>/_TEMP_SPLIT/`.
3. **Processing:** Para cada sub-PDF se extraen proveedor, nº de documento y fecha.
4. **Fallback de fecha:** Si el regex de fecha falla, se usa `os.path.getmtime` del archivo origen. Último recurso: `0000-00-00`.
5. **Output:**
   * ✅ **Éxito** (proveedor + nº doc detectados): renombrado a `YYYY-MM-DD_NDoc.pdf` y movido a `<output>/<Carpeta_Proveedor>/`. Las colisiones se resuelven con sufijo `_DUPLICADO_xxxx`.
   * ⚠️ **Fallo** (sin proveedor o sin nº doc): el archivo se mueve a `<output>/Revision_Manual/` **conservando el nombre original** para triaje humano.

## 📂 Estructura del Proyecto

```text
DocEngie/
├── main.py                         # Entry point + parche Windows (subprocess hide-console)
├── requirements.txt
├── app/
│   ├── config.py                   # Rutas BASE_DIR (script vs PyInstaller frozen)
│   ├── core/
│   │   ├── splitter.py             # Guillotina: separa lotes por firma de proveedor
│   │   ├── pdf_processor.py        # Extracción híbrida native (pypdf) | OCR (Tesseract)
│   │   ├── parser.py               # Identificación de proveedor + extracción de campos
│   │   ├── provider_manager.py     # Lectura/escritura del JSON de reglas
│   │   └── file_manager.py         # Renombrado, fallback de fecha, movimiento
│   ├── gui/
│   │   ├── main_window.py          # Ventana principal + worker thread
│   │   └── components.py           # (reservado para widgets custom)
│   └── utils/
│       └── logger.py               # CSV append-only en data/logs/
├── data/
│   ├── proveedores.json            # Reglas hot-swap (CIF, regex, carpeta destino)
│   └── logs/
│       └── historial_procesos.csv  # Audit trail
├── test_debug.py                   # Script: prueba OCR + parser sobre un PDF
├── test_splitter.py                # Script: prueba el splitter sobre un lote
└── test_vision.py                  # Script: dump de imágenes para tunear umbral OCR
```

## 🏢 Proveedores Soportados

| Slug interno    | Identificadores (firma)                          | Carpeta destino           |
| :-------------- | :----------------------------------------------- | :------------------------ |
| `CBM_IBERICA`   | CIF `ESB85631083`, "CBM Iberica"                 | `CBM_Albaranes`           |
| `EUROPART`      | CIF `A96598917`, "EUROPART HISPANO-ALEMANA"      | `Europart_Albaranes`      |
| `VOLVO_TRUCKS`  | CIF `B80354962`, "Volvo Truck Center", "VOLVO"   | `Volvo_Albaranes`         |
| `HNTOOLS`       | CIF `B-50741040`, tel. `976465540`, "HNTOOLS"    | `HnTools_Albaranes`       |
| `GLOBAL_PARTS`  | CIF `B85930147`, tel. `91 675 71 52`, dominio    | `GlobalParts_Albaranes`   |
| `RS_TURIA`      | "RSTURIA", "TURIA"                               | `RsTuria_Albaranes`       |
| `WURTH`         | CIF `A08472276`, tel. `938629500`, "WURTH"       | `Wurth_Albaranes`         |

## ➕ Añadir un Proveedor Nuevo

El loop de iteración es siempre el mismo:

1. **Conseguir un PDF de muestra** del proveedor.
2. **Editar `data/proveedores.json`** añadiendo una nueva entrada:
   ```json
   "NUEVO_PROVEEDOR": {
     "firma":                ["CIF_OR_KEYWORD", "OtraPalabraClave"],
     "patron_documento":     "regex con grupo de captura (1)",
     "patron_fecha":         "regex con grupo de captura (1)",
     "formato_fecha_origen": "%d/%m/%Y",
     "carpeta_destino":      "MiProveedor_Albaranes"
   }
   ```
3. **Editar `RUTA_PDF_PRUEBA`** en `test_debug.py` apuntando al PDF de muestra.
4. **Ejecutar `python test_debug.py`** — imprimirá el texto OCR crudo y los campos parseados.
5. **Ajustar el regex** tolerando los espacios espurios típicos del OCR (`\s*` entre dígitos). Los patrones existentes son una buena referencia.

> 💡 **Consejo de visión por computador:** si el OCR no lee bien un proveedor con fondos grises, edita `RUTA_PDF` en `test_vision.py` y ejecútalo. Generará varias binarizaciones con distintos umbrales — elige aquella donde el fondo desaparezca y la tinta siga negra (el valor productivo actual es `UMBRAL_CORTE = 10`).

## 🧪 Scripts de Debug

Los `test_*.py` de la raíz **no son tests de pytest** — son scripts interactivos para iterar sobre OCR y regex. Cada uno tiene una constante de ruta hardcodeada al inicio que **debes editar** antes de ejecutar:

| Script             | Para qué sirve                                                                            |
| :----------------- | :---------------------------------------------------------------------------------------- |
| `test_debug.py`    | Probar OCR + parser sobre un PDF concreto. Imprime texto crudo y campos extraídos.        |
| `test_splitter.py` | Probar el splitter sobre un lote "Frankenstein" (varios proveedores en un solo PDF).      |
| `test_vision.py`   | Dump de imágenes pre-procesadas con varios umbrales de binarización. Útil para tuning OCR.|

## 📦 Build (PyInstaller)

DocEngie está pensado para entregarse como un `.exe` standalone. En modo `frozen`, `app/config.py` busca `bin/` y `data/` **junto al ejecutable**, no dentro del bundle de PyInstaller. Para empaquetar:

```bash
pyinstaller --noconfirm --windowed --name DocEngie main.py
# Luego copia las carpetas bin/ y data/ al lado del .exe generado
```

## 🪟 Notas específicas de Windows

* `main.py` aplica un monkey-patch global a `subprocess.Popen` añadiendo `STARTF_USESHOWWINDOW | SW_HIDE`. Esto suprime el parpadeo de consolas negras que Tesseract/Poppler generarían en cada página. **No quitar este parche.**
* El paquete de idioma OCR debe ser `spa` (Spanish). Sin `spa.traineddata` en `tessdata/`, el OCR fallará en runtime.
* En Linux/macOS la app arranca pero las rutas a `tesseract.exe` no resolverán; solo funcionará el modo de extracción nativa.
