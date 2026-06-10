# Splitter fiable + Quick wins UX — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Arreglar los dos modos de fallo del splitter (junta y corta de más), eliminar el doble OCR, y añadir settings persistentes + destino=origen + barra de progreso.

**Architecture:** Se centraliza la extracción de texto por página en un módulo nuevo `ocr_utils` (umbral de 50 caracteres para decidir OCR, pre-procesado y `--psm` únicos). La decisión de corte pasa a ser una función pura `agrupar_paginas()` basada en (proveedor, nº documento), testeada con pytest. El splitter devuelve `[{ruta, texto, analisis}]` para que la GUI no vuelva a extraer texto. Settings en `data/settings.json`.

**Tech Stack:** Python 3.14, pypdf, pytesseract, pdf2image, Pillow, customtkinter, pytest.

**Spec:** `docs/superpowers/specs/2026-06-10-splitter-fiable-y-ux-design.md`

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `pytest.ini` | Crear | Limitar la colección de tests a `tests/` (en la raíz hay scripts manuales `test_*.py`) |
| `requirements.txt` | Modificar | Añadir pytest y pillow (falta pese a usarse) |
| `app/core/provider_manager.py` | Modificar | Caché de módulo para `proveedores.json` |
| `app/core/ocr_utils.py` | Crear | Extracción de texto de una página (nativo + OCR unificado) |
| `app/core/splitter.py` | Modificar | `agrupar_paginas()` pura + nuevo contrato de `dividir_pdf_por_proveedor` |
| `app/core/pdf_processor.py` | Modificar | Delegar el OCR en `ocr_utils` (mismo pre-procesado/psm) |
| `app/utils/settings.py` | Crear | Cargar/guardar `data/settings.json` |
| `app/gui/main_window.py` | Modificar | Usar nuevo contrato del splitter, settings, destino=origen, progreso |
| `app/config.py` | Modificar | Bump de versión |
| `tests/test_provider_manager.py` | Crear | Tests de caché |
| `tests/test_ocr_utils.py` | Crear | Tests del umbral y fallbacks |
| `tests/test_agrupar_paginas.py` | Crear | Tests de la lógica de corte |
| `tests/test_splitter.py` | Crear | Test de integración del contrato nuevo |
| `tests/test_settings.py` | Crear | Tests de persistencia |

Todos los comandos se ejecutan desde la raíz del repo. `PY=.venv/bin/python` y `PYTEST=.venv/bin/pytest`.

---

### Task 1: Infraestructura de tests

**Files:**
- Create: `pytest.ini`
- Create: `tests/__init__.py` (vacío)
- Modify: `requirements.txt`

- [ ] **Step 1: Instalar pytest en el venv**

Run: `.venv/bin/pip install pytest`
Expected: `Successfully installed ... pytest-8.x`

- [ ] **Step 2: Crear `pytest.ini`**

En la raíz hay scripts manuales (`test_debug.py`, `test_splitter.py`, `test_vision.py`) que pytest intentaría coleccionar y ejecutan código al importarse. Limitamos la colección:

```ini
[pytest]
testpaths = tests
```

- [ ] **Step 3: Crear `tests/__init__.py` vacío**

```python
```

- [ ] **Step 4: Actualizar `requirements.txt`**

Contenido completo nuevo:

```
customtkinter
pypdf
packaging
pytesseract
pdf2image
pillow
pytest
```

(`pdf2image` y `pillow` se usan pero faltaban en el archivo.)

- [ ] **Step 5: Verificar que pytest corre sin coleccionar los scripts de la raíz**

Run: `.venv/bin/pytest -v`
Expected: `no tests ran` (0 errores de colección)

- [ ] **Step 6: Commit**

```bash
git add pytest.ini tests/__init__.py requirements.txt
git commit -m "chore: infraestructura de tests con pytest"
```

---

### Task 2: Caché de proveedores

**Files:**
- Modify: `app/core/provider_manager.py`
- Test: `tests/test_provider_manager.py`

Hoy `cargar_proveedores()` relee el JSON del disco en cada página analizada.

- [ ] **Step 1: Escribir tests que fallan**

`tests/test_provider_manager.py`:

```python
from app.core import provider_manager


def test_cargar_devuelve_dict(tmp_path, monkeypatch):
    ruta = tmp_path / "prov.json"
    ruta.write_text('{"A": {"firma": ["X"]}}', encoding="utf-8")
    monkeypatch.setattr(provider_manager, "PROVIDERS_JSON_PATH", str(ruta))
    provider_manager.invalidar_cache()

    assert "A" in provider_manager.cargar_proveedores()


def test_segunda_lectura_usa_cache(tmp_path, monkeypatch):
    ruta = tmp_path / "prov.json"
    ruta.write_text('{"A": {"firma": ["X"]}}', encoding="utf-8")
    monkeypatch.setattr(provider_manager, "PROVIDERS_JSON_PATH", str(ruta))
    provider_manager.invalidar_cache()
    provider_manager.cargar_proveedores()

    # Cambiamos el archivo en disco: la caché debe seguir sirviendo lo anterior
    ruta.write_text('{"B": {"firma": ["Y"]}}', encoding="utf-8")
    assert "A" in provider_manager.cargar_proveedores()

    # Tras invalidar, se relee
    provider_manager.invalidar_cache()
    assert "B" in provider_manager.cargar_proveedores()


def test_archivo_inexistente_no_cachea(tmp_path, monkeypatch):
    monkeypatch.setattr(provider_manager, "PROVIDERS_JSON_PATH", str(tmp_path / "no.json"))
    provider_manager.invalidar_cache()
    assert provider_manager.cargar_proveedores() == {}
```

- [ ] **Step 2: Verificar que fallan**

Run: `.venv/bin/pytest tests/test_provider_manager.py -v`
Expected: FAIL con `AttributeError: ... has no attribute 'invalidar_cache'`

- [ ] **Step 3: Implementar la caché**

Contenido completo nuevo de `app/core/provider_manager.py`:

```python
import json
import os
from app.config import PROVIDERS_JSON_PATH

# Caché de módulo: el JSON solo se relee tras invalidar_cache()
_cache_proveedores = None


def cargar_proveedores():
    """
    Lee el archivo JSON y devuelve el diccionario de proveedores.
    Usa caché en memoria. Si falla, devuelve un diccionario vacío
    (sin cachear el fallo) para no romper la app.
    """
    global _cache_proveedores
    if _cache_proveedores is not None:
        return _cache_proveedores

    if not os.path.exists(PROVIDERS_JSON_PATH):
        return {}

    try:
        with open(PROVIDERS_JSON_PATH, 'r', encoding='utf-8') as f:
            _cache_proveedores = json.load(f)
            return _cache_proveedores
    except Exception as e:
        print(f"❌ Error crítico cargando proveedores: {e}")
        return {}


def invalidar_cache():
    """Fuerza relectura del JSON en la próxima llamada a cargar_proveedores()."""
    global _cache_proveedores
    _cache_proveedores = None


def guardar_proveedor(nombre_clave, datos_proveedor):
    """
    Añade o actualiza un proveedor y guarda los cambios en el JSON.
    """
    proveedores = dict(cargar_proveedores())
    proveedores[nombre_clave] = datos_proveedor
    resultado = _escribir_json(proveedores)
    invalidar_cache()
    return resultado


def _escribir_json(datos):
    """Función auxiliar privada para escribir en el archivo."""
    try:
        with open(PROVIDERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")
        return False
```

OJO: `cargar_proveedores` lee `PROVIDERS_JSON_PATH` como atributo de módulo (los tests lo monkeypatchean). No cambiar el import a una lectura local de `app.config`.

Nota: dentro de la función se usa el global `PROVIDERS_JSON_PATH` del módulo, por eso el monkeypatch de los tests funciona.

- [ ] **Step 4: Verificar que pasan**

Run: `.venv/bin/pytest tests/test_provider_manager.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/provider_manager.py tests/test_provider_manager.py
git commit -m "perf: cachear proveedores.json en memoria"
```

---

### Task 3: `ocr_utils.py` — extracción de texto unificada

**Files:**
- Create: `app/core/ocr_utils.py`
- Test: `tests/test_ocr_utils.py`

- [ ] **Step 1: Escribir tests que fallan**

`tests/test_ocr_utils.py`:

```python
from app.core import ocr_utils
from app.core.ocr_utils import extraer_texto_pagina, UMBRAL_TEXTO_NATIVO


class PaginaFalsa:
    """Simula una página de pypdf."""

    def __init__(self, texto):
        self._texto = texto

    def extract_text(self):
        return self._texto


class PaginaRota:
    def extract_text(self):
        raise RuntimeError("pdf corrupto")


def test_texto_nativo_suficiente_no_intenta_ocr():
    # Si intentara OCR petaría: la ruta no existe
    texto = "x" * (UMBRAL_TEXTO_NATIVO + 10)
    resultado = extraer_texto_pagina(PaginaFalsa(texto), "/no/existe.pdf", 0, usar_ocr=True)
    assert resultado == texto


def test_usar_ocr_false_devuelve_nativo_aunque_sea_corto():
    resultado = extraer_texto_pagina(PaginaFalsa("corto"), "/no/existe.pdf", 0, usar_ocr=False)
    assert resultado == "corto"


def test_ocr_no_disponible_devuelve_nativo(monkeypatch):
    monkeypatch.setattr(ocr_utils, "ocr_disponible", lambda: False)
    resultado = extraer_texto_pagina(PaginaFalsa("corto"), "/no/existe.pdf", 0, usar_ocr=True)
    assert resultado == "corto"


def test_pagina_rota_devuelve_vacio(monkeypatch):
    monkeypatch.setattr(ocr_utils, "ocr_disponible", lambda: False)
    resultado = extraer_texto_pagina(PaginaRota(), "/no/existe.pdf", 0, usar_ocr=True)
    assert resultado == ""
```

- [ ] **Step 2: Verificar que fallan**

Run: `.venv/bin/pytest tests/test_ocr_utils.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.core.ocr_utils'`

- [ ] **Step 3: Implementar `app/core/ocr_utils.py`**

```python
"""
Única fuente de verdad para extraer texto de una página de PDF.
La usan el splitter y el clasificador para que ambos "vean" el mismo texto.
"""
import os

from app.config import TESSERACT_CMD, POPPLER_PATH

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import ImageEnhance, ImageFilter

    OCR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AVISO: Falló la importación de OCR. Causa: {e}")
    OCR_AVAILABLE = False

# Si el texto nativo de una página no llega a este nº de caracteres,
# se considera escaneada y se intenta OCR. (Antes solo se OCR-eaba si
# estaba 100% vacía, y páginas con restos de texto digital se colaban.)
UMBRAL_TEXTO_NATIVO = 50

# Configuración única de Tesseract para TODAS las fases.
OCR_CONFIG = '--psm 6'
OCR_LANG = 'spa'

# [CRÍTICO] Umbral 10 descubierto en pruebas.
# Elimina fondos grises (Europart) dejando solo tinta negra fuerte.
UMBRAL_BINARIO = 10

_aviso_tesseract_emitido = False


def ocr_disponible():
    """True si las librerías Python y el binario de Tesseract están listos."""
    return OCR_AVAILABLE and TESSERACT_CMD is not None and os.path.exists(TESSERACT_CMD)


def preprocesar_imagen(img):
    """Pre-procesado único: grises, contraste x2, sharpen, umbral binario."""
    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(2)
    img = img.filter(ImageFilter.SHARPEN)
    return img.point(lambda x: 0 if x < UMBRAL_BINARIO else 255, '1')


def ocr_imagen(img):
    """Aplica pre-procesado + Tesseract a una imagen PIL. Devuelve el texto."""
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    return pytesseract.image_to_string(
        preprocesar_imagen(img), lang=OCR_LANG, config=OCR_CONFIG
    )


def extraer_texto_pagina(page, ruta_pdf, indice, usar_ocr):
    """
    Extrae el texto de una página.

    page: objeto página de pypdf (reader.pages[indice])
    ruta_pdf: ruta del PDF original (pdf2image necesita el archivo)
    indice: índice 0-based de la página
    usar_ocr: si True y el texto nativo es escaso, intenta OCR
    """
    global _aviso_tesseract_emitido

    try:
        texto = page.extract_text() or ""
    except Exception:
        texto = ""

    if len(texto.strip()) >= UMBRAL_TEXTO_NATIVO or not usar_ocr:
        return texto

    if not ocr_disponible():
        if not _aviso_tesseract_emitido:
            print("⚠️ OCR no disponible (falta Tesseract). Continuando en modo nativo.")
            _aviso_tesseract_emitido = True
        return texto

    try:
        imagenes = convert_from_path(
            ruta_pdf,
            first_page=indice + 1,
            last_page=indice + 1,
            poppler_path=POPPLER_PATH,
        )
        for img in imagenes:
            texto += "\n" + ocr_imagen(img)
    except Exception as e:
        print(f"   ⚠️ Fallo OCR en página {indice + 1}: {e}")

    return texto
```

- [ ] **Step 4: Verificar que pasan**

Run: `.venv/bin/pytest tests/test_ocr_utils.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/ocr_utils.py tests/test_ocr_utils.py
git commit -m "feat: extracción de texto por página unificada (ocr_utils)"
```

---

### Task 4: `agrupar_paginas()` — lógica de corte pura

**Files:**
- Modify: `app/core/splitter.py` (añadir función, sin tocar aún `dividir_pdf_por_proveedor`)
- Test: `tests/test_agrupar_paginas.py`

Reglas (del spec): proveedor distinto → corte; mismo proveedor con nº distinto → corte; mismo nº → continuación; sin nº legible → corte; sin proveedor → continuación.

- [ ] **Step 1: Escribir tests que fallan**

`tests/test_agrupar_paginas.py`:

```python
from app.core.splitter import agrupar_paginas


def pagina(prov, doc):
    return {"proveedor": prov, "id_documento": doc}


def test_lote_vacio():
    assert agrupar_paginas([]) == []


def test_mismo_proveedor_numeros_distintos_corta():
    grupos = agrupar_paginas([pagina("WURTH", "111"), pagina("WURTH", "222")])
    assert [g["paginas"] for g in grupos] == [[0], [1]]


def test_cabecera_repetida_mismo_numero_no_corta():
    grupos = agrupar_paginas([pagina("WURTH", "111"), pagina("WURTH", "111")])
    assert [g["paginas"] for g in grupos] == [[0, 1]]
    assert grupos[0]["proveedor"] == "WURTH"


def test_pagina_sin_proveedor_es_continuacion():
    grupos = agrupar_paginas([
        pagina("WURTH", "111"),
        pagina(None, None),
        pagina("VOLVO_TRUCKS", "333"),
    ])
    assert [g["paginas"] for g in grupos] == [[0, 1], [2]]


def test_huerfano_al_inicio():
    grupos = agrupar_paginas([pagina(None, None), pagina("WURTH", "111")])
    assert [g["paginas"] for g in grupos] == [[0], [1]]
    assert grupos[0]["proveedor"] == "Desconocido"


def test_mismo_proveedor_sin_numero_corta():
    grupos = agrupar_paginas([pagina("WURTH", "111"), pagina("WURTH", None)])
    assert [g["paginas"] for g in grupos] == [[0], [1]]


def test_lote_mixto():
    grupos = agrupar_paginas([
        pagina("WURTH", "111"),
        pagina("WURTH", "111"),
        pagina("EUROPART", "22AL333"),
        pagina(None, None),
        pagina("WURTH", "444"),
    ])
    assert [g["paginas"] for g in grupos] == [[0, 1], [2, 3], [4]]
    assert [g["proveedor"] for g in grupos] == ["WURTH", "EUROPART", "WURTH"]
```

- [ ] **Step 2: Verificar que fallan**

Run: `.venv/bin/pytest tests/test_agrupar_paginas.py -v`
Expected: FAIL con `ImportError: cannot import name 'agrupar_paginas'`

- [ ] **Step 3: Añadir la función a `app/core/splitter.py`**

Añadir después de los imports (antes de `dividir_pdf_por_proveedor`):

```python
def agrupar_paginas(analisis_por_pagina):
    """
    Decide los cortes de un lote a partir del análisis de cada página.

    Entrada: [{"proveedor": str|None, "id_documento": str|None}, ...]
    Salida:  [{"paginas": [índices], "proveedor": str, "id_documento": str|None}, ...]

    Reglas:
    - Sin proveedor detectado -> continuación del documento abierto
      (o huérfano "Desconocido" si no hay ninguno abierto).
    - Proveedor distinto al abierto -> corte.
    - Mismo proveedor con nº de documento distinto o ilegible -> corte.
      (Los documentos reales son de 1-2 páginas; cuando la cabecera se
      repite, el nº casi siempre se repite con ella.)
    - Mismo proveedor y mismo nº -> continuación.
    """
    grupos = []
    actual = None

    for i, info in enumerate(analisis_por_pagina):
        proveedor = info.get("proveedor")
        id_doc = info.get("id_documento")

        if proveedor is None:
            if actual is None:
                actual = {"paginas": [i], "proveedor": "Desconocido", "id_documento": None}
            else:
                actual["paginas"].append(i)
            continue

        es_continuacion = (
            actual is not None
            and actual["proveedor"] == proveedor
            and id_doc is not None
            and actual["id_documento"] == id_doc
        )

        if es_continuacion:
            actual["paginas"].append(i)
        else:
            if actual:
                grupos.append(actual)
            actual = {"paginas": [i], "proveedor": proveedor, "id_documento": id_doc}

    if actual:
        grupos.append(actual)

    return grupos
```

- [ ] **Step 4: Verificar que pasan**

Run: `.venv/bin/pytest tests/test_agrupar_paginas.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/splitter.py tests/test_agrupar_paginas.py
git commit -m "feat: lógica de corte por proveedor y nº de documento (agrupar_paginas)"
```

---

### Task 5: Nuevo contrato del splitter (fin del doble OCR)

**Files:**
- Modify: `app/core/splitter.py` (reescribir `dividir_pdf_por_proveedor`)
- Modify: `app/gui/main_window.py:289-337` (consumir el nuevo contrato)
- Test: `tests/test_splitter.py`

- [ ] **Step 1: Escribir test de integración que falla**

`tests/test_splitter.py`:

```python
import os

from pypdf import PdfWriter

from app.core.splitter import dividir_pdf_por_proveedor


def crear_pdf_en_blanco(ruta, paginas=2):
    w = PdfWriter()
    for _ in range(paginas):
        w.add_blank_page(width=200, height=200)
    with open(ruta, "wb") as f:
        w.write(f)


def test_contrato_de_salida(tmp_path):
    pdf = tmp_path / "lote.pdf"
    crear_pdf_en_blanco(str(pdf), paginas=2)

    resultados = dividir_pdf_por_proveedor(str(pdf), str(tmp_path / "tmp"), usar_ocr=False)

    # 2 páginas en blanco sin proveedor -> un único grupo huérfano
    assert len(resultados) == 1
    fragmento = resultados[0]
    assert set(fragmento.keys()) == {"ruta", "texto", "analisis"}
    assert os.path.exists(fragmento["ruta"])
    assert "Desconocido" in os.path.basename(fragmento["ruta"])
    assert fragmento["analisis"]["proveedor_detectado"] is None


def test_pdf_inexistente_devuelve_lista_vacia(tmp_path):
    assert dividir_pdf_por_proveedor(str(tmp_path / "no.pdf"), str(tmp_path)) == []
```

- [ ] **Step 2: Verificar que falla**

Run: `.venv/bin/pytest tests/test_splitter.py -v`
Expected: FAIL (`dividir_pdf_por_proveedor` aún devuelve lista de rutas, no de dicts)

- [ ] **Step 3: Reescribir `dividir_pdf_por_proveedor`**

Contenido completo nuevo de `app/core/splitter.py` (conserva `agrupar_paginas` de la Task 4 y `_guardar_fragmento`):

```python
from pypdf import PdfReader, PdfWriter
from app.core.parser import analizar_documento
from app.core.ocr_utils import extraer_texto_pagina
import os


def agrupar_paginas(analisis_por_pagina):
    """
    Decide los cortes de un lote a partir del análisis de cada página.
    (Misma función de la Task 4; ver allí la documentación de reglas.)
    """
    grupos = []
    actual = None

    for i, info in enumerate(analisis_por_pagina):
        proveedor = info.get("proveedor")
        id_doc = info.get("id_documento")

        if proveedor is None:
            if actual is None:
                actual = {"paginas": [i], "proveedor": "Desconocido", "id_documento": None}
            else:
                actual["paginas"].append(i)
            continue

        es_continuacion = (
            actual is not None
            and actual["proveedor"] == proveedor
            and id_doc is not None
            and actual["id_documento"] == id_doc
        )

        if es_continuacion:
            actual["paginas"].append(i)
        else:
            if actual:
                grupos.append(actual)
            actual = {"paginas": [i], "proveedor": proveedor, "id_documento": id_doc}

    if actual:
        grupos.append(actual)

    return grupos


def dividir_pdf_por_proveedor(ruta_pdf_masivo, carpeta_temporal, usar_ocr=False):
    """
    Trocea un PDF multipágina (Lote) en documentos individuales.

    Devuelve: [{"ruta": str, "texto": str, "analisis": dict}, ...]
    El texto extraído aquí se reaprovecha en la clasificación:
    no hay que volver a abrir ni OCR-ear los fragmentos.
    """
    if not os.path.exists(ruta_pdf_masivo):
        return []

    try:
        reader = PdfReader(ruta_pdf_masivo)
    except Exception as e:
        print(f"❌ Error abriendo lote PDF: {e}")
        return []

    os.makedirs(carpeta_temporal, exist_ok=True)

    total_paginas = len(reader.pages)
    print(f"🔄 Analizando lote de {total_paginas} páginas (OCR={usar_ocr})...")

    # 1. Extraer texto y analizar página a página (una sola vez)
    textos = []
    analisis_paginas = []
    for i, page in enumerate(reader.pages):
        texto = extraer_texto_pagina(page, ruta_pdf_masivo, i, usar_ocr)
        textos.append(texto)
        analisis = analizar_documento(texto)
        analisis_paginas.append({
            "proveedor": analisis["proveedor_detectado"],
            "id_documento": analisis["id_documento"],
        })

    # 2. Decidir los cortes
    grupos = agrupar_paginas(analisis_paginas)

    # 3. Escribir cada grupo y devolver texto + análisis del documento completo
    resultados = []
    for grupo in grupos:
        writer = PdfWriter()
        for indice in grupo["paginas"]:
            writer.add_page(reader.pages[indice])

        ruta = _guardar_fragmento(
            writer, grupo["proveedor"], grupo["paginas"][0], carpeta_temporal
        )
        texto_grupo = "\n".join(textos[indice] for indice in grupo["paginas"])
        resultados.append({
            "ruta": ruta,
            "texto": texto_grupo,
            # El análisis del grupo completo extrae también fecha y carpeta destino
            "analisis": analizar_documento(texto_grupo),
        })
        print(f"   ✂️ Documento: {grupo['proveedor']} (págs {grupo['paginas']})")

    return resultados


def _guardar_fragmento(writer, proveedor, indice_pag, carpeta):
    """Escribe el PDF temporal en disco"""
    nombre = f"SPLIT_Pag{indice_pag}_{proveedor}.pdf"
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "wb") as f:
        writer.write(f)
    return ruta
```

(Desaparecen los imports condicionales de pytesseract/pdf2image y el uso de `TESSERACT_CMD`/`POPPLER_PATH`: todo eso vive ahora en `ocr_utils`.)

- [ ] **Step 4: Adaptar el consumidor en `app/gui/main_window.py`**

En `run_processing`, sustituir el bloque "2. PROCESAR CADA TROZO" (el bucle `for sub_ruta in sub_archivos:` completo, líneas ~305-337) por:

```python
                # 2. PROCESAR CADA TROZO (texto y análisis ya vienen del splitter)
                for fragmento in sub_archivos:
                    sub_ruta = fragmento["ruta"]
                    nombre_sub = os.path.basename(sub_ruta)
                    datos = fragmento["analisis"]

                    if not fragmento["texto"].strip():
                        self.log_message(f"   ⚠️ {nombre_sub}: sin texto legible -> Revision_Manual")
                        errores += 1
                    elif datos.get("proveedor_detectado"):
                        self.log_message(
                            f"   ✅ {datos['proveedor_detectado']} | Doc: {datos.get('id_documento', 'N/A')}")
                    else:
                        self.log_message(f"   ❓ {nombre_sub} -> Desconocido")

                    # C) Mover
                    exito, ruta_final = mover_y_renombrar(sub_ruta, datos, base_output_dir)

                    # D) Registrar
                    registrar_evento(f"{archivo} -> {nombre_sub}", datos, ruta_final, exito)
                    procesados_finales += 1
```

Y en el bloque "1. DIVIDIR", simplificar (la variable `sub_archivos` ahora contiene dicts y el `if dividir_pdf_por_proveedor:` era código muerto):

```python
                # 1. DIVIDIR (SPLITTER) - también extrae el texto de cada fragmento
                try:
                    sub_archivos = dividir_pdf_por_proveedor(
                        ruta_completa_origen,
                        temp_split_dir,
                        usar_ocr=usar_ocr_activo
                    )
                except Exception as e:
                    self.log_message(f"💥 Error crítico dividiendo {archivo}: {e}")
                    errores += 1
                    continue
```

Quitar también el import que queda sin uso: `from app.core.pdf_processor import extraer_texto_pdf`.

Mejora colateral: antes, un fragmento con error de lectura se quedaba en `_TEMP_SPLIT` y se borraba con la limpieza final (se perdía). Ahora siempre pasa por `mover_y_renombrar`, que sin proveedor lo manda a `Revision_Manual`.

- [ ] **Step 5: Verificar tests y que la app importa**

Run: `.venv/bin/pytest -v && .venv/bin/python -c "import app.gui.main_window; print('OK')"`
Expected: todos los tests passed + `OK`

- [ ] **Step 6: Commit**

```bash
git add app/core/splitter.py app/gui/main_window.py tests/test_splitter.py
git commit -m "feat: splitter sin doble OCR, devuelve texto y análisis por fragmento"
```

---

### Task 6: `pdf_processor` delega el OCR en `ocr_utils`

**Files:**
- Modify: `app/core/pdf_processor.py:33-79`

`extraer_texto_pdf` se sigue usando como utilidad para PDFs sueltos (scripts de la raíz). Debe usar el mismo pre-procesado y `--psm` que el splitter.

- [ ] **Step 1: Sustituir el bloque "MODO 1: OCR VISUAL"**

Reemplazar desde `if forzar_ocr:` hasta el final de su `except` (líneas ~33-79) por:

```python
    if forzar_ocr:
        if not OCR_AVAILABLE:
            return None, "Librerías OCR no instaladas."

        if not ocr_utils.ocr_disponible():
            return None, "❌ Falta Tesseract (en Linux: sudo dnf install tesseract tesseract-langpack-spa)"
        if POPPLER_PATH is not None and not os.path.exists(POPPLER_PATH):
            return None, f"❌ Falta Poppler: {POPPLER_PATH}"

        try:
            print(f"   👁️ Motor OCR arrancando... (Procesando imagen)")
            images = convert_from_path(ruta_archivo, poppler_path=POPPLER_PATH)

            texto_completo = ""
            for img in images:
                # Pre-procesado + Tesseract unificados (mismos que el splitter)
                texto_completo += ocr_utils.ocr_imagen(img) + "\n"

            if not texto_completo.strip():
                return None, "OCR: Imagen vacía o ilegible."

            return texto_completo, None

        except Exception as e:
            return None, f"Fallo Crítico Motor OCR: {str(e)}"
```

Y actualizar los imports del archivo:

```python
from pypdf import PdfReader
import os
from app.config import POPPLER_PATH
from app.core import ocr_utils

# Importación condicional
try:
    from pdf2image import convert_from_path

    OCR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AVISO DEBUG: Falló la importación de OCR. Causa: {e}")
    OCR_AVAILABLE = False
```

(Se eliminan `import sys`, `TESSERACT_CMD`, `pytesseract` y los imports de PIL: ya no se usan aquí. Desaparecen también el `ImageEnhance`/`ImageFilter`/umbral duplicados.)

- [ ] **Step 2: Verificar**

Run: `.venv/bin/pytest -v && .venv/bin/python -c "from app.core.pdf_processor import extraer_texto_pdf; print(extraer_texto_pdf('/no/existe.pdf'))"`
Expected: tests passed + `(None, 'Archivo no encontrado')`

- [ ] **Step 3: Commit**

```bash
git add app/core/pdf_processor.py
git commit -m "refactor: pdf_processor usa el OCR unificado de ocr_utils"
```

---

### Task 7: Settings persistentes

**Files:**
- Create: `app/utils/settings.py`
- Test: `tests/test_settings.py`

- [ ] **Step 1: Escribir tests que fallan**

`tests/test_settings.py`:

```python
from app.utils.settings import cargar_settings, guardar_settings, DEFAULTS


def test_defaults_si_no_existe(tmp_path):
    s = cargar_settings(ruta=str(tmp_path / "no_existe.json"))
    assert s["usar_ocr"] is True
    assert s["output_manual"] is False
    assert s["tema"] == "Dark"


def test_persistencia(tmp_path):
    ruta = str(tmp_path / "settings.json")
    s = cargar_settings(ruta=ruta)
    s["usar_ocr"] = False
    s["tema"] = "Light"
    s["last_input_dir"] = str(tmp_path)  # carpeta que existe
    assert guardar_settings(s, ruta=ruta) is True

    s2 = cargar_settings(ruta=ruta)
    assert s2["usar_ocr"] is False
    assert s2["tema"] == "Light"
    assert s2["last_input_dir"] == str(tmp_path)


def test_archivo_corrupto_devuelve_defaults(tmp_path):
    ruta = tmp_path / "settings.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    s = cargar_settings(ruta=str(ruta))
    assert s["usar_ocr"] is True


def test_carpeta_guardada_inexistente_cae_a_default(tmp_path):
    ruta = str(tmp_path / "settings.json")
    datos = dict(DEFAULTS)
    datos["last_input_dir"] = "/ruta/que/no/existe"
    guardar_settings(datos, ruta=ruta)

    s = cargar_settings(ruta=ruta)
    assert s["last_input_dir"] == DEFAULTS["last_input_dir"]


def test_claves_desconocidas_se_ignoran(tmp_path):
    ruta = tmp_path / "settings.json"
    ruta.write_text('{"usar_ocr": false, "clave_rara": 1}', encoding="utf-8")
    s = cargar_settings(ruta=str(ruta))
    assert s["usar_ocr"] is False
    assert "clave_rara" not in s
```

- [ ] **Step 2: Verificar que fallan**

Run: `.venv/bin/pytest tests/test_settings.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.utils.settings'`

- [ ] **Step 3: Implementar `app/utils/settings.py`**

```python
"""
Persistencia de preferencias del usuario en data/settings.json.
Si el archivo no existe o está corrupto, se usan los defaults.
"""
import json
import os

from app.config import BASE_DIR, DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR

SETTINGS_PATH = os.path.join(BASE_DIR, "data", "settings.json")

DEFAULTS = {
    "last_input_dir": DEFAULT_INPUT_DIR,
    "last_output_dir": DEFAULT_OUTPUT_DIR,
    "usar_ocr": True,
    "tema": "Dark",
    # True cuando el usuario eligió carpeta destino a mano:
    # entonces NO se sincroniza automáticamente con la de origen.
    "output_manual": False,
}


def cargar_settings(ruta=None):
    """Devuelve los settings combinados con los defaults (claves extrañas fuera)."""
    ruta = ruta or SETTINGS_PATH
    settings = dict(DEFAULTS)

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            settings.update({k: datos[k] for k in DEFAULTS if k in datos})
    except (OSError, ValueError):
        pass  # sin archivo o corrupto: defaults

    # Carpetas guardadas que ya no existen -> volver al default
    for clave in ("last_input_dir", "last_output_dir"):
        if not os.path.isdir(settings[clave]):
            settings[clave] = DEFAULTS[clave]

    return settings


def guardar_settings(settings, ruta=None):
    """Escribe los settings. Devuelve True/False según éxito."""
    ruta = ruta or SETTINGS_PATH
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except OSError as e:
        print(f"⚠️ No se pudieron guardar los settings: {e}")
        return False
```

- [ ] **Step 4: Verificar que pasan**

Run: `.venv/bin/pytest tests/test_settings.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/utils/settings.py tests/test_settings.py
git commit -m "feat: settings persistentes en data/settings.json"
```

---

### Task 8: GUI — settings, destino=origen y barra de progreso

**Files:**
- Modify: `app/gui/main_window.py`
- Modify: `.gitignore` (excluir `data/settings.json`)

No hay test automatizado de GUI; la verificación es import-check + prueba manual al final.

- [ ] **Step 1: Cargar settings en `__init__`**

Añadir el import:

```python
from app.utils.settings import cargar_settings, guardar_settings
```

Sustituir el bloque "Variables de estado" por:

```python
        # Variables de estado (restauradas de la última sesión)
        self.settings = cargar_settings()
        self.input_folder = ctk.StringVar(value=os.path.abspath(self.settings["last_input_dir"]))
        self.output_folder = ctk.StringVar(value=os.path.abspath(self.settings["last_output_dir"]))
        self.is_running = False
        self.usar_ocr = ctk.BooleanVar(value=self.settings["usar_ocr"])
        self.output_manual = self.settings["output_manual"]
```

- [ ] **Step 2: Restaurar el tema guardado**

Sustituir la línea `self.switch_tema.select()` (justo tras crear el switch) por:

```python
        if self.settings["tema"] == "Light":
            self.switch_tema.deselect()
        else:
            self.switch_tema.select()
        self.cambiar_tema()
```

- [ ] **Step 3: Añadir la barra de progreso**

En el botón `btn_run`, cambiar `pady=(0, 20)` por `pady=(0, 10)`. Justo debajo del bloque del botón, añadir:

```python
        # Barra de progreso (avanza por archivo de origen procesado)
        self.progress_bar = ctk.CTkProgressBar(self.frame_config, height=12)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=6, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="ew")
```

- [ ] **Step 4: Sincronizar destino con origen y persistir**

Sustituir `select_input`, `select_output` y `cerrar_app` por:

```python
    def select_input(self):
        """ Permite ver archivos en las carpetas de entrada """

        archivo = filedialog.askopenfilename(
            title="Selecciona cualquiera de los archivos PDF dentro de la carpeta",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            # Obtenemos el directorio padre de ese archivo
            folder = os.path.dirname(archivo)
            self.input_folder.set(folder)
            self.log_message(f"📂 Carpeta origen seleccionada: {folder}")

            # Si el usuario no fijó destino a mano, destino = origen
            if not self.output_manual:
                self.output_folder.set(folder)
                self.log_message(f"📂 Carpeta destino sincronizada con origen")

            self._persistir_settings()

    def select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)
            self.output_manual = True  # elección manual: deja de sincronizarse
            self._persistir_settings()

    def _persistir_settings(self):
        self.settings.update({
            "last_input_dir": self.input_folder.get(),
            "last_output_dir": self.output_folder.get(),
            "usar_ocr": self.usar_ocr.get(),
            "tema": self.switch_tema.get(),
            "output_manual": self.output_manual,
        })
        guardar_settings(self.settings)

    def cerrar_app(self):
        self._persistir_settings()
        self.destroy()
        sys.exit()
```

- [ ] **Step 5: Progreso X/Y en `run_processing`**

Sustituir el arranque del bucle principal:

```python
            for archivo in archivos_origen:
                ruta_completa_origen = os.path.join(input_dir, archivo)
                self.lbl_status.configure(text=f"Procesando: {archivo}...")
```

por:

```python
            total_archivos = len(archivos_origen)
            for num_archivo, archivo in enumerate(archivos_origen, start=1):
                ruta_completa_origen = os.path.join(input_dir, archivo)
                self.lbl_status.configure(text=f"Procesando {num_archivo}/{total_archivos}: {archivo}")
```

Y al final del cuerpo del bucle (tras procesar los fragmentos del archivo, dentro del `for`):

```python
                self.progress_bar.set(num_archivo / total_archivos)
```

En `reset_ui`, añadir tras `self.btn_exit.configure(state="normal")`:

```python
        self.progress_bar.set(0)
```

En `start_processing_thread`, persistir el estado del checkbox al lanzar (tras `self.is_running = True`):

```python
        self._persistir_settings()
```

- [ ] **Step 6: Excluir settings.json del repo**

En `.gitignore`, bajo `# Datos de trabajo y logs`, añadir:

```
data/settings.json
```

- [ ] **Step 7: Verificar**

Run: `.venv/bin/pytest -v && .venv/bin/python -c "import app.gui.main_window; print('OK')"`
Expected: todos los tests passed + `OK`

- [ ] **Step 8: Commit**

```bash
git add app/gui/main_window.py .gitignore
git commit -m "feat: settings persistentes, destino=origen y barra de progreso en la GUI"
```

---

### Task 9: Bump de versión y verificación final

**Files:**
- Modify: `app/config.py:46`

- [ ] **Step 1: Subir versión**

```python
VERSION_ACTUAL = "v2.7 (Splitter+)"
```

- [ ] **Step 2: Suite completa**

Run: `.venv/bin/pytest -v`
Expected: ~21 passed, 0 failed

- [ ] **Step 3: Prueba manual (requiere usuario o entorno con display)**

Checklist para el usuario:
1. `.venv/bin/python main.py` — la app abre con las carpetas de la última sesión.
2. Seleccionar carpeta origen → el destino se sincroniza solo.
3. Elegir destino a mano → seleccionar otro origen → el destino NO cambia.
4. Procesar un lote con dos albaranes seguidos del mismo proveedor → 2 archivos.
5. Procesar un albarán de 2 páginas con cabecera repetida → 1 archivo.
6. La barra de progreso avanza y el estado muestra `X/Y`.
7. Cerrar y reabrir → carpetas, checkbox OCR y tema restaurados.

- [ ] **Step 4: Commit**

```bash
git add app/config.py
git commit -m "chore: versión v2.7 (Splitter+)"
```

---

## Notas para el ejecutor

- Tesseract puede no estar instalado en la máquina (Linux): los tests NO lo
  requieren (todo lo que toca OCR real está detrás de `ocr_disponible()` y los
  tests lo monkeypatchean). La prueba manual con OCR sí lo necesita:
  `sudo dnf install tesseract tesseract-langpack-spa`.
- No tocar los scripts manuales de la raíz (`test_debug.py`, `test_splitter.py`,
  `test_vision.py`): quedan fuera de pytest vía `pytest.ini`. El nuevo
  `tests/test_splitter.py` no choca con el `test_splitter.py` de la raíz porque
  pytest solo colecciona `tests/`.
- Los mensajes de commit terminan con la línea de coautoría de Claude
  (ver convención del repo en commits recientes).
