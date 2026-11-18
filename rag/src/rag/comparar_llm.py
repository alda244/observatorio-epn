"""Comparación de LLM con las preguntas de referencia.

Cada modelo de ``rag/evaluacion/modelos_llm.json`` responde las mismas
preguntas con la misma recuperación. Por modelo se mide:

- ``citas_validas``: respuestas del LLM con citas válidas, sobre las que
  pasaron la recuperación (las demás se descartan y quedan extractivas).
- ``rechazo_correcto``: preguntas sin respuesta que terminan en rechazo.
- ``latencia_p50_ms`` y ``latencia_p95_ms``.
- Tokens promedio por consulta y costo estimado de 10.000 consultas al mes.

Además se exporta un CSV con todas las respuestas para la revisión manual
(español y citas) y para calcular RAGAS en el Sprint 3.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import replace
from pathlib import Path

import numpy as np

from rag.config import RAIZ_REPO, Config
from rag.evaluacion import PREGUNTAS
from rag.motor import Motor

MODELOS = RAIZ_REPO / "rag/evaluacion/modelos_llm.json"
CONSULTAS_MES = 10_000


def _modelos_listos(modelos: list[dict]) -> tuple[list[dict], list[str]]:
    listos, omitidos = [], []
    for m in modelos:
        if not m.get("modelo") or m["modelo"] == "COMPLETAR":
            omitidos.append(f"{m['nombre']}: falta el id del modelo")
        elif m.get("clave_env") and not os.environ.get(m["clave_env"]):
            omitidos.append(f"{m['nombre']}: falta la variable {m['clave_env']}")
        else:
            listos.append(m)
    return listos, omitidos


def comparar(cfg: Config, ruta_modelos: str | None = None, ruta_preguntas: str | None = None,
             salida: str | None = None) -> dict:
    modelos, omitidos = _modelos_listos(json.loads(Path(ruta_modelos or MODELOS).read_text(encoding="utf-8")))
    preguntas = json.loads(Path(ruta_preguntas or PREGUNTAS).read_text(encoding="utf-8"))
    resumen, filas = [], []
    for m in modelos:
        motor = Motor(replace(cfg, llm_base_url=m["base_url"], llm_modelo=m["modelo"],
                              llm_api_key=os.environ.get(m.get("clave_env") or "", "")))
        lat, t_in, t_out = [], [], []
        generadas = validas = rechazos_ok = rechazos = 0
        for q in preguntas:
            r = motor.responder(q["pregunta"], filtros=q.get("filtros"))
            lat.append(r.latencia_ms)
            if q.get("rechazo"):
                rechazos += 1
                rechazos_ok += r.modo == "rechazo" or r.respuesta.startswith("No hay dato publicado")
            if r.modo != "rechazo":
                generadas += 1
                validas += r.modo == "llm"
            if r.tokens_entrada is not None:
                t_in.append(r.tokens_entrada)
                t_out.append(r.tokens_salida or 0)
            filas.append({"modelo": m["nombre"], "id": q["id"], "tipo": q.get("tipo", ""),
                          "pregunta": q["pregunta"], "modo": r.modo, "respuesta": r.respuesta,
                          "latencia_ms": r.latencia_ms, "puntaje_espanol": "", "puntaje_citas": ""})
        prom_in = float(np.mean(t_in)) if t_in else 0.0
        prom_out = float(np.mean(t_out)) if t_out else 0.0
        costo = CONSULTAS_MES * (prom_in * m["precio_entrada"] + prom_out * m["precio_salida"]) / 1e6
        resumen.append({
            "modelo": m["nombre"],
            "id": m["modelo"],
            "citas_validas": round(validas / generadas, 3) if generadas else None,
            "rechazo_correcto": round(rechazos_ok / rechazos, 3) if rechazos else None,
            "latencia_p50_ms": int(np.percentile(lat, 50)),
            "latencia_p95_ms": int(np.percentile(lat, 95)),
            "tokens_entrada_prom": round(prom_in),
            "tokens_salida_prom": round(prom_out),
            "costo_10k_consultas_usd": round(costo, 2),
        })
    res = {"preguntas": len(preguntas), "modelos": resumen, "omitidos": omitidos}
    if salida:
        base = Path(salida)
        base.parent.mkdir(parents=True, exist_ok=True)
        base.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        with base.with_suffix(".csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]) if filas else ["modelo"])
            w.writeheader()
            w.writerows(filas)
    return res
