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
