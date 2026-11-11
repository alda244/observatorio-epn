"""Pruebas del prototipo con embeddings deterministas (sin descargar modelos).

Los datos de prueba son 9 filas reales del piloto (``tests/datos/empresas.csv``)
y el catálogo CIIU oficial.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag.cliente_b import ClienteBArchivo
from rag.config import RAIZ_REPO, Config
from rag.indice import EmbedderHash, fragmentar
from rag.ingesta import Documento, cargar_catalogo_ciiu, ficha_identificacion, leer_documento_markdown, normalizar
from rag.motor import SIN_DATO, Motor
from rag.pipeline import ingerir

DATOS = Path(__file__).parent / "datos"
CIIU = RAIZ_REPO / "etl/datos/crudo/2025/bi_ciiu.csv"


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    docs = tmp_path / "documentos"
    docs.mkdir()
    (docs / "reporte-demo.md").write_text(
        "---\ntitulo: Reporte de prueba del Observatorio\nfuente_url: https://observatorio.epn.edu.ec/demo\n"
        "fuente_tipo: reporte_observatorio\nfecha: 2026-11-09\n---\n"
        "Documento sintético de prueba: la adopción de computación en la nube en empresas medianas.",
        encoding="utf-8",
    )
    return Config(
        fuente_empresas=DATOS / "empresas.csv",
        catalogo_ciiu=CIIU,
        documentos=docs,
        indice=tmp_path / "indice",
        trazas=tmp_path / "trazas.jsonl",
        modelo_embeddings="hash-512",
        umbral_similitud=0.05,
        umbral_fuerte=0.95,
    )


def test_normalizar_quita_control_y_espacios():
    assert normalizar("a\u0000  b\n\n\n\nc") == "a b\n\nc"


def test_ficha_no_contiene_cifras():
    """Salvaguarda: las cifras nunca entran al texto indexado."""
    ciiu = cargar_catalogo_ciiu(CIIU)
    tuti = ClienteBArchivo(DATOS / "empresas.csv").empresa("721037")
    doc = ficha_identificacion(tuti, ciiu)
    assert "TIENDAS TUTI" in doc.texto
    assert "1008" not in doc.texto.replace(".", "") and "empleados" not in doc.texto.lower()
    assert doc.origen == "derivado" and doc.fuente_tipo == "scvs_ranking"


def test_fragmentar_con_solape():
    doc = Documento("d", "t", " ".join(f"p{i}" for i in range(100)), "u", "x", "2026-01-01")
    frs = fragmentar(doc, palabras=40, solape=10)
    assert [len(f.texto.split()) for f in frs] == [40, 40, 40]
    assert frs[1].texto.split()[0] == "p30"
    assert all(f.sha256_doc == doc.sha256 for f in frs)


def test_documento_markdown_exige_metadatos(tmp_path: Path):
    p = tmp_path / "x.md"
    p.write_text("---\ntitulo: X\n---\ntexto", encoding="utf-8")
    with pytest.raises(ValueError, match="faltan metadatos"):
        leer_documento_markdown(p)


def test_ingesta_idempotente(cfg: Config):
    r1 = ingerir(cfg)
    assert (r1.documentos_fuente, r1.nuevos, r1.fragmentos_totales) == (10, 10, 10)
    r2 = ingerir(cfg)
    assert (r2.nuevos, r2.actualizados, r2.sin_cambios, r2.fragmentos_indexados) == (0, 0, 10, 0)
    # Un documento que cambia se reindexa; uno que desaparece se elimina.
    md = cfg.documentos / "reporte-demo.md"
    md.write_text(md.read_text(encoding="utf-8") + " Texto agregado.", encoding="utf-8")
    assert ingerir(cfg).actualizados == 1
    md.unlink()
    r4 = ingerir(cfg)
    assert (r4.eliminados, r4.fragmentos_totales) == (1, 9)
    assert len((cfg.indice / "corridas.jsonl").read_text(encoding="utf-8").splitlines()) == 4


def test_consulta_por_nombre_cita_y_traza(cfg: Config):
    ingerir(cfg)
    r = Motor(cfg, embedder=EmbedderHash(512)).responder("¿A qué se dedica Telconet?")
    assert r.modo == "extractivo"
    assert r.citas[0]["titulo"] == "TELCONET S.A."
    assert "[1]" in r.respuesta
    traza = json.loads(cfg.trazas.read_text(encoding="utf-8").splitlines()[-1])
    assert traza["traza_id"] == r.traza_id and traza["recuperados"][0]["frag_id"] == "empresa:72951#0"


def test_cifras_desde_b_con_alerta_de_empleados(cfg: Config):
    ingerir(cfg)
    r = Motor(cfg, embedder=EmbedderHash(512)).responder("¿Cuánto vendió Tiendas Tuti y cuántos empleados tiene?")
    tuti = next(c for c in r.cifras if c["expediente"] == "721037")
    assert tuti["empleados_declarados"] == 8 and tuti["fuente"].startswith("API de B")
    assert any("inconsistente" in a for a in r.advertencias)


def test_filtro_implicito_por_ciudad(cfg: Config):
    ingerir(cfg)
    r = Motor(cfg, embedder=EmbedderHash(512)).responder("empresas de tecnología en Ambato")
    assert r.citas and all(c["frag_id"] in {"empresa:37947#0", "empresa:309569#0"} for c in r.citas)


def test_rechazo_sin_respaldo(cfg: Config):
    ingerir(cfg)
    r = Motor(cfg, embedder=EmbedderHash(512)).responder("zzzz qqqq")
    assert r.modo == "rechazo" and r.respuesta == SIN_DATO and not r.citas


def test_llm_sin_citas_se_descarta(cfg: Config, monkeypatch: pytest.MonkeyPatch):
    ingerir(cfg)
    cfg_llm = Config(**{**cfg.__dict__, "llm_base_url": "http://llm.invalido", "llm_modelo": "m"})
    motor = Motor(cfg_llm, embedder=EmbedderHash(512))
    monkeypatch.setattr(motor, "_llm", lambda *a: "Telconet es una empresa enorme.")
    r = motor.responder("¿Qué hace Telconet?")
    assert r.modo == "extractivo" and any("sin citas" in a for a in r.advertencias)
    monkeypatch.setattr(motor, "_llm", lambda *a: "Telconet ofrece telecomunicaciones [1].")
    assert motor.responder("¿Qué hace Telconet?").modo == "llm"
