# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DocEngie is a Windows-first desktop application (Python 3.14 + CustomTkinter) that classifies, renames and moves supplier PDFs (albaranes/facturas) into structured folders. It uses a hybrid native-PDF + OCR pipeline and rules defined in an external JSON file.

The application is designed to be packaged as a standalone Windows `.exe` via PyInstaller, with Tesseract and Poppler shipped alongside in a `bin/` folder.

## Running and Building

```bash
# Run the GUI (entry point lives at repo root, NOT in app/)
python main.py

# Install dependencies
pip install -r requirements.txt
```

There is no test runner, linter or CI configured. The three `test_*.py` files at the repo root are **interactive debugging scripts**, not pytest tests — they hardcode Windows paths in `RUTA_PDF_PRUEBA` / `PDF_MASIVO` and must be edited before running:

- `test_debug.py` — exercises `extraer_texto_pdf` + `analizar_documento` against one PDF, dumping the OCR text and parsed fields. Use this when iterating on regex in `data/proveedores.json`.
- `test_splitter.py` — exercises the multi-document splitter against a "Frankenstein" lote PDF.
- `test_vision.py` — dumps `1_original.png`, `2_grises.png`, `3_contraste.png` and several `4_binarizado_umbral_*.png` so you can pick the correct binarization threshold for a new supplier (the current production value `UMBRAL_CORTE = 10` in `pdf_processor.py:60` was tuned this way for Europart's gray backgrounds).

## External Binaries (Tesseract + Poppler)

OCR is **not** pip-installable for this project; `pytesseract` and `pdf2image` are wrappers that shell out to native executables. `app/config.py` resolves them relative to `BASE_DIR`:

- `TESSERACT_CMD = BIN_DIR/Tesseract-OCR/tesseract.exe`
- `POPPLER_PATH  = BIN_DIR/poppler/Library/bin`  (folder, not exe — that's what `pdf2image` expects)

`BASE_DIR` is computed in two modes (`app/config.py:9-15`):
- **Script mode** (`python main.py`): two levels up from `app/config.py`.
- **Frozen mode** (PyInstaller `.exe`): `os.path.dirname(sys.executable)`, so the `bin/`, `data/` folders sit next to the `.exe` for the end user.

When working in this sandbox / on Linux those Windows paths will not resolve, and `pdf_processor.extraer_texto_pdf(..., forzar_ocr=True)` will return `"❌ Falta Tesseract"` / `"❌ Falta Poppler"`. The native-PDF path still works.

## Architecture

The pipeline runs in this order, all orchestrated from `app/gui/main_window.py::run_processing` on a background thread:

```
folder ─► splitter ─► pdf_processor ─► parser ─► file_manager ─► logger
         (Guillotina)  (native|OCR)    (regex)   (rename+move)   (CSV)
```

### Splitter — "Guillotina" strategy (`app/core/splitter.py`)

Treats every page whose text matches a known supplier `firma` as the **start** of a new document; non-matching pages are appended to the current writer. This is how a single scanned batch PDF gets atomized into per-supplier sub-PDFs in `<output>/_TEMP_SPLIT/` before the rest of the pipeline runs. If a page has no native text and `usar_ocr=True`, only that page is rasterized (via `first_page=i+1, last_page=i+1`) — full-PDF OCR is avoided here for speed.

### PDF processor — hybrid native/OCR (`app/core/pdf_processor.py`)

Two modes, selected by `forzar_ocr`:
- **Native**: `pypdf.PdfReader`. Returns `"PDF vacío o imagen (Activa OCR)"` if extracted text is shorter than 10 chars — this string is the trigger the caller can use to retry with OCR.
- **OCR**: Rasterize via `pdf2image`, then `convert('L')` → `ImageEnhance.Contrast(2)` → `ImageFilter.SHARPEN` → binarize at `UMBRAL_CORTE = 10` → `pytesseract.image_to_string(..., lang='spa', config='--psm 3')`. The `psm 3` choice and threshold `10` are empirical (see commit history) — don't change them casually; re-run `test_vision.py` first.

OCR libraries are imported under a `try/except` block that sets `OCR_AVAILABLE = False` on failure, so the app must keep working when Tesseract/Poppler aren't installed.

### Parser — supplier identification (`app/core/parser.py` + `data/proveedores.json`)

`analizar_documento(texto)` does three things in order:
1. **Identify supplier** — substring search of every `firma` entry against the lowercased PDF text. First match wins; order in the JSON matters.
2. **Extract doc id** — `re.search(reglas["patron_documento"], texto, IGNORECASE|MULTILINE)`, then strips spaces and dots from group 1 (OCR often inserts `"49 51 667"` for `"4951667"`).
3. **Extract date** — same pattern, also stripping spaces inside `"19/ 01 / 2026"`.

If supplier is not found, returns early with everything `None` except `log_info`. The downstream `file_manager` treats missing-supplier-or-missing-id as "send to `Revision_Manual/`".

### Provider rules (`data/proveedores.json`) — hot-swappable

This is **the** configuration surface for adding/tuning suppliers. Each key is an internal supplier slug; the schema is:

```json
"SUPPLIER_KEY": {
  "firma":                ["CIF_OR_KEYWORD", "..."],   // substring match, lowercased
  "patron_documento":     "regex with group 1",         // doc/albarán number
  "patron_fecha":         "regex with group 1",         // date string
  "formato_fecha_origen": "%d/%m/%Y",                   // strptime format
  "carpeta_destino":      "Subfolder_Name"              // under output dir
}
```

When iterating on a new supplier, the loop is: edit `proveedores.json` → run `test_debug.py` against a sample PDF → inspect printed OCR text + parsed fields → adjust regex. The OCR text dump is essential because OCR introduces stray spaces that the regex must tolerate (most existing patterns use `\s*` liberally between digits — keep that style).

### File manager — rename + fallback (`app/core/file_manager.py`)

Success condition is **`proveedor_detectado` AND `id_documento`** — date is allowed to be missing. Date resolution cascade:
1. Try the regex result against `["%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d"]` (after normalizing `.` and `-` to `/`).
2. **Fallback to `os.path.getmtime`** of the source file → `"YYYY-MM-DD"`.
3. Last resort: `"0000-00-00"`.

Final name is `{YYYY-MM-DD}_{doc_id}.pdf` inside `<output>/<carpeta_destino>/`. On collision a 2-byte hex suffix `_DUPLICADO_xxxx` is appended (so re-running the same batch never overwrites).

Failures (no supplier or no id) go to `<output>/Revision_Manual/` with the **original filename preserved** for human triage.

### Logger (`app/utils/logger.py`)

Appends one row per processed sub-document to `data/logs/historial_procesos.csv`. Header is written on first run only. This is also the audit trail referenced by the "Revision_Manual" workflow.

## GUI Threading Model

`PDFClassifierApp.start_processing_thread` spawns `run_processing` as a `daemon=True` thread to keep the CustomTkinter main loop responsive. UI updates from the worker thread (e.g. `self.lbl_status.configure(...)`, `self.log_message(...)`) are made directly without `after()` — the codebase relies on CTk's tolerance for this. If you add new UI updates from worker code and see crashes, wrap them in `self.after(0, lambda: ...)`.

`extraer_texto_pdf` is called with `forzar_ocr=usar_ocr_activo`, wrapped in a `try/except TypeError` that retries without the kwarg — this is a backwards-compat shim for an older signature (`main_window.py:313-316`). The current signature accepts the kwarg, so the `except` branch is dead unless someone reverts `pdf_processor.py`.

## Windows-Specific Concerns

`main.py` monkey-patches `subprocess.Popen` on Windows to force `STARTF_USESHOWWINDOW | SW_HIDE` on every subprocess call. This suppresses the black console flash that `pytesseract` and `pdf2image` would otherwise produce on every page. Do not remove this patch — it applies globally and silently to every subprocess spawned afterwards (including the OCR calls deep inside `pytesseract`).

The OCR language pack must be `spa` (Spanish). If Tesseract is installed without `spa.traineddata`, OCR will fail with a runtime error from inside pytesseract — the codebase has no preflight check for this.

## Development Branch

Per the agent's working instructions, all changes go on the `claude/analyze-project-documentation-3kbaf` branch.
