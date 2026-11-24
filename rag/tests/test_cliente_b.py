"""Pruebas de los clientes de B y de la ingesta del Company Profile.

``tests/datos/fichas.csv`` tiene dos fichas reales de ``etl/seed/profiles.csv``
(Favorita y Telconet) y una ficha pendiente sintética de Otecel.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from rag.cliente_b import ClienteBArchivo, ClienteBHttp
from rag.config import RAIZ_REPO, Config
from rag.ingesta import ficha_company_profile
from rag.motor import Motor
from rag.pipeline import ingerir, recolectar

DATOS = Path(__file__).parent / "datos"
CIIU = RAIZ_REPO / "etl/datos/crudo/2025/bi_ciiu.csv"


@pytest.fixture
def cliente() -> ClienteBArchivo:
    return ClienteBArchivo(DATOS / "empresas.csv", DATOS / "fichas.csv")


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    return Config(
        fuente_empresas=DATOS / "empresas.csv",
        fichas=DATOS / "fichas.csv",
        fuente_b="archivo",
        catalogo_ciiu=CIIU,
        documentos=tmp_path / "documentos",
        indice=tmp_path / "indice",
        trazas=tmp_path / "trazas.jsonl",
        modelo_embeddings="hash-512",
        umbral_similitud=0.05,
        umbral_fuerte=0.95,
    )


def test_archivo_lee_fichas_con_forma_de_la_api(cliente):
    fichas = cliente.fichas()
    assert set(fichas) == {"384", "72951", "47972"}
    t = fichas["72951"]
    assert t["url_oficial"] == "https://telconet.ec/"
    assert t["estado"] == "completo"
    assert isinstance(t["redes"], list) and t["redes"]
    assert t["fuentes"]["descripcion"].startswith("https://")


def test_archivo_sin_fichas_no_falla(tmp_path):
    assert ClienteBArchivo(DATOS / "empresas.csv", tmp_path / "no-existe.csv").fichas() == {}


def test_perfil_cita_la_web_oficial_y_no_tiene_cifras(cliente):
    e = cliente.empresa("384")
    doc = ficha_company_profile(e, cliente.fichas()["384"])
    assert doc.doc_id == "perfil:384"
    assert doc.fuente_tipo == "company_profile"
    assert doc.fuente_url == "https://www.corporacionfavorita.com/"
    assert doc.fecha == "2026-11-11"
    assert "Supermercados" in doc.texto
    assert doc.metadatos["ciudad"] == e["ciudad"]
    # Salvaguarda: las cifras de la SCVS no entran al texto indexado.
    assert not re.search(r"\d{6,}", doc.texto.replace("+593", ""))


def test_ficha_pendiente_no_entra(cliente):
    assert ficha_company_profile(cliente.empresa("47972"), cliente.fichas()["47972"]) is None


def test_ingesta_agrega_los_perfiles(cfg):
    ids = {d.doc_id for d in recolectar(cfg)}
    assert {"perfil:384", "perfil:72951"} <= ids
    assert "perfil:47972" not in ids


def test_perfil_mejora_la_busqueda_de_supermercados(cfg):
    """H2: la CIIU de Favorita no dice "supermercado"; su ficha sí."""
    ingerir(cfg, reconstruir=True)
    r = Motor(cfg).responder("¿Qué empresas tienen supermercados?")
    assert r.modo != "rechazo"
    assert r.citas[0]["frag_id"].startswith("perfil:384")
    sin = replace(cfg, fichas=cfg.indice.parent / "sin.csv", indice=cfg.indice.parent / "indice_sin")
    ingerir(sin, reconstruir=True)
    r_sin = Motor(sin).responder("¿Qué empresas tienen supermercados?")
    assert r_sin.modo == "rechazo" or "384" not in r_sin.citas[0]["frag_id"]


DETALLE = {
    "expediente": 72951, "nombre": "TELCONET S.A.", "grupo": "TEC", "ciiu": "J6110.01",
    "ciiu_descripcion": "ACTIVIDADES DE TELECOMUNICACIONES", "seccion_ciiu": "J", "division_ciiu": "J61",
    "tamano": "grande", "tipo_compania": "ANÓNIMA", "region": "COSTA", "provincia": "GUAYAS",
    "ciudad": "GUAYAQUIL", "es_holding": False, "tiene_alerta": False,
    "cifras": [
        {"anio": 2025, "ventas": 317568865.89, "empleados": 5382, "tiene_alerta": False,
         "procedencia": {"fuente_tipo": "scvs_ranking", "fuente_url": "https://scvs/2025", "fecha_corte": "2026-10-22"}},
        {"anio": 2024, "ventas": 317134200.0, "empleados": 5300, "tiene_alerta": False,
         "procedencia": {"fuente_tipo": "scvs_ranking", "fuente_url": "https://scvs/2024", "fecha_corte": "2025-10-01"}},
    ],
    "ficha": {"url_oficial": "https://telconet.ec/", "tagline": "Infraestructura digital", "estado": "completo",
              "fuente_tipo": "web_oficial", "fecha_captura": "2026-11-18", "redes": [], "fuentes": {}},
}


def test_http_pagina_y_toma_el_ultimo_ejercicio(monkeypatch):
    c = ClienteBHttp("http://api-b")
    llamadas = []

    def falso_get(ruta, **params):
        llamadas.append((ruta, params))
        if ruta == "/v1/empresas":
            return {"total": 1, "limit": 100, "offset": 0, "datos": [{"expediente": 72951}]}
        return DETALLE if ruta == "/v1/empresas/72951" else None

    monkeypatch.setattr(c, "_get", falso_get)
    [e] = c.empresas()
    assert llamadas[0] == ("/v1/empresas", {"en_piloto": "true", "limit": 100, "offset": 0, "orden": "nombre"})
    assert e["expediente"] == "72951" and e["anio"] == 2025
    assert e["ventas"] == 317568865.89 and e["tamano_derivado"] == "grande"
    assert e["fuente_url"] == "https://scvs/2025"
    assert [x["anio"] for x in e["cifras"]] == [2024, 2025]
    assert c.fichas()["72951"]["url_oficial"] == "https://telconet.ec/"
    assert c.empresa("1") is None


def test_campo_pedido_se_busca_en_la_empresa_nombrada(cfg):
    """El teléfono de Telconet no respalda una pregunta por el teléfono de Speedycom."""
    ingerir(cfg, reconstruir=True)
    m = Motor(cfg)
    assert m.responder("¿Cuál es el teléfono de Speedycom?").modo == "rechazo"
    r = m.responder("¿Cuál es el teléfono de Telconet?")
    assert r.modo != "rechazo" and r.citas[0]["frag_id"].startswith("perfil:72951")
