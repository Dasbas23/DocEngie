# Diseño: Splitter fiable + Quick wins UX

**Fecha:** 2026-06-10
**Estado:** Aprobado por el usuario

## Contexto y problema

DocEngie clasifica PDFs (albaranes/facturas) por proveedor usando firmas y regex
definidas en `data/proveedores.json`. Los PDFs masivos (lotes multipágina) se
trocean con `app/core/splitter.py` antes de clasificar.

Problemas detectados:

1. **El splitter falla en ambos sentidos** (confirmado por el usuario):
   - *Junta documentos*: solo hace OCR si la página no tiene **nada** de texto
     nativo (`splitter.py`, `if not text.strip()`). Una página escaneada con
     restos de texto digital se salta el OCR, no se detecta la firma y se pega
     al documento anterior.
   - *Corta de más*: el corte se basa solo en detectar firma de proveedor. Si
     un proveedor repite cabecera en todas las páginas, cada página se corta
     como documento nuevo.
   - Inconsistencia de OCR: el splitter usa `--psm 6` sin pre-procesado de
     imagen; el clasificador (`pdf_processor.py`) usa `--psm 3` con
     pre-procesado (grises, contraste, sharpen, umbral 10). La misma página
     "se lee" distinto en cada fase.
2. **Doble OCR**: el splitter OCR-ea páginas para decidir cortes, descarta ese
   texto, y después `extraer_texto_pdf(forzar_ocr=True)` vuelve a OCR-ear el
   fragmento entero. Con el checkbox OCR activado se fuerza OCR incluso en
   PDFs con texto nativo perfecto.
3. **UX**: la app no recuerda carpetas entre sesiones y hay que seleccionar
   destino a mano cada vez; no hay indicador de progreso.

Datos del dominio: los documentos son de 1-2 páginas normalmente; la
repetición de cabecera depende del proveedor.

## Alcance

### Incluido

1. Extracción de texto unificada (nuevo `app/core/ocr_utils.py`).
2. Nueva lógica de corte por nº de documento (función pura + tests).
3. Reaprovechar el texto del splitter en la clasificación (fin del doble OCR).
4. Settings persistentes (`data/settings.json`).
5. Destino = origen por defecto.
6. Indicador de progreso X/Y + barra de progreso.

### Excluido (futuras iteraciones)

- Thread-safety de la UI con `self.after()`.
- Editor de proveedores en la GUI.
- Sugerencia de nuevos proveedores (extracción de CIF en Revision_Manual).
- Modo headless/CLI.

## Diseño

### 1. `app/core/ocr_utils.py` (nuevo)

Única fuente de verdad para extraer texto de una página, usada por splitter y
clasificador:

```python
def extraer_texto_pagina(page, ruta_pdf, indice, usar_ocr) -> str
```

- Intenta texto nativo con pypdf.
- Si `len(texto.strip()) < UMBRAL_TEXTO_NATIVO` (50 caracteres) y
  `usar_ocr=True`: convierte la página con pdf2image y aplica OCR.
- Pre-procesado de imagen único (el actual de `pdf_processor.py`: escala de
  grises, contraste x2, sharpen, umbral binario 10) y un único `--psm`
  (constante `OCR_CONFIG`, valor inicial `--psm 6`).
- Si Tesseract no está disponible (`TESSERACT_CMD` es `None`): avisa una sola
  vez (flag de módulo) y devuelve solo el texto nativo.

`pdf_processor.extraer_texto_pdf` se mantiene para PDFs sueltos pero delega el
OCR por página en `ocr_utils` (mismo pre-procesado y config).

### 2. Lógica de corte: `agrupar_paginas()` (función pura)

```python
def agrupar_paginas(analisis_por_pagina: list[dict]) -> list[dict]
# entrada: [{"proveedor": str|None, "id_documento": str|None}, ...]
# salida:  [{"paginas": [0, 1], "proveedor": str, "id_documento": str|None}, ...]
```

Reglas de decisión por página, comparando con el documento abierto:

| Situación | Decisión |
|---|---|
| Sin proveedor detectado | Continuación (huérfano "Desconocido" si no hay doc abierto) |
| Proveedor distinto al abierto | Corte |
| Mismo proveedor, nº documento distinto | Corte |
| Mismo proveedor, mismo nº documento | Continuación |
| Mismo proveedor, sin nº legible | Corte |

**Decisión de diseño**: "mismo proveedor sin nº legible → corte" se basa en
que los documentos son de 1-2 páginas y en que, cuando la cabecera se repite,
el nº de documento casi siempre se repite con ella. Si en la práctica genera
cortes de más, se invierte la regla en un solo punto (cubierto por tests).

### 3. Splitter sin doble OCR

`dividir_pdf_por_proveedor(ruta, carpeta_temporal, usar_ocr)` pasa a devolver:

```python
[{"ruta": str, "texto": str, "analisis": dict}, ...]
```

- Extrae texto por página con `ocr_utils.extraer_texto_pagina`.
- Analiza cada página con `analizar_documento` (proveedor + nº documento).
- Agrupa con `agrupar_paginas`.
- Escribe cada grupo a PDF (igual que ahora, `SPLIT_PagN_PROVEEDOR.pdf`).
- `texto` = concatenación del texto de las páginas del grupo;
  `analisis` = resultado de `analizar_documento(texto)` del grupo completo
  (para extraer también la fecha, que no se evalúa por página).

`main_window.run_processing` usa `texto`/`analisis` directamente y ya no llama
a `extraer_texto_pdf` para los fragmentos. `analizar_documento` se sigue
llamando una vez por grupo, no por página extra.

Optimización acompañante: `parser.analizar_documento` deja de releer
`proveedores.json` en cada llamada (caché de módulo en `provider_manager`,
invalidable con `guardar_proveedor`).

### 4. Settings persistentes: `app/utils/settings.py` (nuevo)

- Archivo `data/settings.json`:
  ```json
  {"last_input_dir": "...", "last_output_dir": "...",
   "usar_ocr": true, "tema": "Dark", "output_manual": false}
  ```
- `cargar_settings()` con defaults seguros (si el archivo no existe o está
  corrupto, devuelve defaults actuales de `config.py`).
- `guardar_settings(dict)` al cerrar la app (`cerrar_app`) y tras cada cambio
  de carpeta.
- Si una carpeta guardada ya no existe, se cae al default.

### 5. Destino = origen

- Al seleccionar carpeta origen: si el usuario **no** ha elegido destino a
  mano (`output_manual == False`), `output_folder = input_folder`.
- Al usar "Examinar..." del destino: `output_manual = True` y se respeta (y
  persiste) la elección del usuario.

### 6. Progreso

- `lbl_status`: `Procesando 3/12: archivo.pdf`.
- `CTkProgressBar` determinate bajo el botón de inicio, avanza por archivo de
  origen procesado. Se resetea al terminar.

## Manejo de errores

- Tesseract ausente con OCR activado: aviso único en el log de la GUI
  ("OCR no disponible: instala tesseract..."), se continúa en modo nativo.
- Página que falla en OCR: se loguea y se trata como texto vacío (página de
  continuación), igual que ahora.
- `settings.json` corrupto: se ignora y se regenera con defaults.

## Tests

- `tests/test_agrupar_paginas.py` (pytest, función pura, sin I/O):
  - Mismo proveedor, números distintos → 2 documentos.
  - Cabecera repetida con mismo número → 1 documento de 2 páginas.
  - Página sin proveedor entre dos documentos → continuación del primero.
  - Huérfano al inicio → grupo "Desconocido".
  - Mismo proveedor sin nº legible → corte.
  - Lote mixto de varios proveedores.
- `tests/test_settings.py`: defaults, persistencia, archivo corrupto.
- Casos de regresión con textos de albaranes reales: se añadirán cuando el
  usuario aporte ejemplos problemáticos.

## Criterios de éxito

1. Un lote con dos albaranes consecutivos del mismo proveedor se divide en dos
   archivos.
2. Un albarán de 2 páginas con cabecera repetida produce un solo archivo.
3. Con OCR activado, el tiempo de proceso de un lote escaneado baja
   notablemente respecto a la versión actual (sin doble OCR).
4. Al reabrir la app, las carpetas y el checkbox OCR están como se dejaron.
5. `pytest` pasa en local.
