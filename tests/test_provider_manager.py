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
