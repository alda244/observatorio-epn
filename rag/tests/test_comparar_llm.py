"""Comparación de LLM contra un servidor local compatible con OpenAI."""

from __future__ import annotations

import csv
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from test_pipeline import cfg  # noqa: F401 - fixture compartida

from rag.comparar_llm import comparar, listar_modelos
from rag.config import Config
from rag.indice import EmbedderHash
from rag.pipeline import ingerir


class _LLMFalso(BaseHTTPRequestHandler):
    """Cita [1] salvo cuando el modelo es 'sin-citas'."""

    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        texto = "Respuesta sin fuente." if cuerpo["model"] == "sin-citas" else "Según la ficha [1]."
        datos = {"choices": [{"message": {"content": texto}}],
                 "usage": {"prompt_tokens": 1000, "completion_tokens": 100}}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"data": [{"id": "modelo-falso"}]}).encode())

    def log_message(self, *a):
        pass


@pytest.fixture
def servidor():
    srv = HTTPServer(("127.0.0.1", 0), _LLMFalso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/v1"
    srv.shutdown()


def test_comparar_dos_modelos(cfg: Config, servidor: str, tmp_path: Path, monkeypatch):  # noqa: F811
    monkeypatch.setattr("rag.motor.crear_embedder", lambda n: EmbedderHash(512))
    ingerir(cfg)
    modelos = tmp_path / "modelos.json"
    modelos.write_text(json.dumps([
        {"nombre": "bueno", "base_url": servidor, "modelo": "bueno", "clave_env": "",
         "precio_entrada": 0.10, "precio_salida": 0.50},
        {"nombre": "sin citas", "base_url": servidor, "modelo": "sin-citas", "clave_env": "",
         "precio_entrada": 0, "precio_salida": 0},
        {"nombre": "sin id", "base_url": servidor, "modelo": "COMPLETAR", "clave_env": "",
         "precio_entrada": 0, "precio_salida": 0},
    ]), encoding="utf-8")
    preguntas = tmp_path / "preguntas.json"
    preguntas.write_text(json.dumps([
        {"id": "P1", "pregunta": "¿A qué se dedica Telconet?", "esperados": ["72951"]},
        {"id": "F1", "tipo": "fuera_de_alcance", "pregunta": "zzzz qqqq", "rechazo": True},
    ]), encoding="utf-8")
    res = comparar(cfg, str(modelos), str(preguntas), str(tmp_path / "llm"))
    bueno, malo = res["modelos"]
    assert bueno["citas_validas"] == 1.0 and malo["citas_validas"] == 0.0
    assert bueno["rechazo_correcto"] == 1.0
    assert bueno["tokens_entrada_prom"] == 1000
    assert bueno["costo_10k_consultas_usd"] == 1.5  # 10.000 × (1000 × 0,10 + 100 × 0,50) / 1e6
    assert res["omitidos"] == ["sin id: falta el id del modelo"]
    with (tmp_path / "llm.csv").open(encoding="utf-8", newline="") as f:
        assert len(list(csv.DictReader(f))) == 4  # 2 modelos × 2 preguntas


def test_cuenta_errores_del_proveedor(cfg: Config, tmp_path: Path, monkeypatch):  # noqa: F811
    """Una clave o un id mal puestos no deben pasar como respuestas extractivas."""
    monkeypatch.setattr("rag.motor.crear_embedder", lambda n: EmbedderHash(512))
    ingerir(cfg)
    modelos = tmp_path / "modelos.json"
    modelos.write_text(json.dumps([
        {"nombre": "caido", "base_url": "http://127.0.0.1:9/v1", "modelo": "x", "clave_env": "",
         "precio_entrada": 0, "precio_salida": 0},
    ]), encoding="utf-8")
    preguntas = tmp_path / "preguntas.json"
    preguntas.write_text(json.dumps([
        {"id": "P1", "pregunta": "¿A qué se dedica Telconet?", "esperados": ["72951"]},
    ]), encoding="utf-8")
    [caido] = comparar(cfg, str(modelos), str(preguntas))["modelos"]
    assert caido["errores_llm"] == 1


def test_listar_modelos(servidor: str, tmp_path: Path, monkeypatch):
    modelos = tmp_path / "modelos.json"
    modelos.write_text(json.dumps([
        {"nombre": "local", "base_url": servidor, "modelo": "x", "clave_env": ""},
        {"nombre": "sin clave", "base_url": servidor, "modelo": "x", "clave_env": "CLAVE_QUE_NO_EXISTE"},
    ]), encoding="utf-8")
    monkeypatch.delenv("CLAVE_QUE_NO_EXISTE", raising=False)
    res = listar_modelos(str(modelos))
    assert res["local"] == ["modelo-falso"]
    assert res["sin clave"] == "falta la variable CLAVE_QUE_NO_EXISTE"


def test_cargar_env_no_pisa_la_sesion(tmp_path: Path, monkeypatch):
    from rag.config import cargar_env

    env = tmp_path / ".env"
    env.write_text('# comentario\nCLAVE_A="desde-archivo"\nCLAVE_B=desde-archivo\nCLAVE_C=\n', encoding="utf-8")
    monkeypatch.delenv("CLAVE_A", raising=False)
    monkeypatch.setenv("CLAVE_B", "desde-sesion")
    monkeypatch.delenv("CLAVE_C", raising=False)
    cargar_env(env)
    import os
    assert os.environ["CLAVE_A"] == "desde-archivo"
    assert os.environ["CLAVE_B"] == "desde-sesion"
    assert "CLAVE_C" not in os.environ
    monkeypatch.delenv("CLAVE_A")
