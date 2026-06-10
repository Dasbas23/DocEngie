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
