"""Pruebas del almacén pgvector contra una base real.

Se ejecutan solo si ``RAG_PG_DSN_PRUEBAS`` apunta a un PostgreSQL con la
extensión ``vector``; la prueba borra el esquema ``asistente`` de esa base.
"""

from __future__ import annotations

import os
from dataclasses import replace

import numpy as np
import pytest
from test_pipeline import cfg  # noqa: F401 - fixture compartida

from rag.config import Config
from rag.indice import AlmacenPgvector, EmbedderHash
from rag.motor import Motor
from rag.pipeline import ingerir

DSN = os.environ.get("RAG_PG_DSN_PRUEBAS", "")
pytestmark = pytest.mark.skipif(not DSN, reason="sin RAG_PG_DSN_PRUEBAS")


@pytest.fixture
def cfg_pg(cfg: Config) -> Config:  # noqa: F811
    import psycopg

    with psycopg.connect(DSN, autocommit=True) as con:
        con.execute("CREATE EXTENSION IF NOT EXISTS vector")
        con.execute("DROP SCHEMA IF EXISTS asistente CASCADE")
    return replace(cfg, almacen="pgvector", pg_dsn=DSN)


def test_ingesta_idempotente_en_pgvector(cfg_pg: Config):
    r1 = ingerir(cfg_pg)
    assert (r1.nuevos, r1.fragmentos_totales) == (10, 10)
    r2 = ingerir(cfg_pg)
    assert (r2.sin_cambios, r2.fragmentos_indexados) == (10, 0)


def test_hnsw_coincide_con_busqueda_exacta(cfg_pg: Config):
    ingerir(cfg_pg)
    almacen = AlmacenPgvector(DSN, cfg_pg.modelo_embeddings)
    frag, vec = almacen.todo()
    q = EmbedderHash(512).codificar(["telecomunicaciones Guayaquil"])[0]
    exacto = [frag[i].frag_id for i in np.argsort(-(vec @ q))[:3]]
    assert [f for f, _ in almacen.buscar(q, k=3)] == exacto


def test_traza_en_tabla(cfg_pg: Config):
    import psycopg

    ingerir(cfg_pg)
    r = Motor(cfg_pg, embedder=EmbedderHash(512)).responder("¿A qué se dedica Telconet?")
    with psycopg.connect(DSN) as con:
        modo, rec = con.execute(
            "SELECT modo, recuperados FROM asistente.traza WHERE traza_id = %s", (r.traza_id,)
        ).fetchone()
    assert modo == "extractivo" and rec[0]["frag_id"] == "empresa:72951#0"


def test_cambio_de_modelo_exige_reconstruir(cfg_pg: Config):
    ingerir(cfg_pg)
    otro = replace(cfg_pg, modelo_embeddings="hash-256")
    with pytest.raises(ValueError, match="reconstruir"):
        ingerir(otro)
    assert ingerir(otro, reconstruir=True).fragmentos_totales == 10
