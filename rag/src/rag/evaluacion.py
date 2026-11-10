"""Evaluación de la recuperación del prototipo.

Cada pregunta de referencia indica los expedientes que deben recuperarse
(``esperados`` o ``esperados_ciiu``; basta uno en el top k) o ``"rechazo": true`` cuando el asistente debe
responder que no hay dato publicado. Métricas:

- ``acierto@k``: fracción de preguntas con al menos un esperado en el top k.
- ``mrr``: media del inverso del rango del primer esperado.
- ``rechazo_correcto``: fracción de preguntas fuera de alcance rechazadas.
- ``falso_rechazo``: preguntas con respuesta que el umbral rechazó.

Es la línea base del Sprint 2; RAGAS (fidelidad y pertinencia) se agrega en
el Sprint 3, cuando haya generación con LLM.
"""

from __future__ import annotations

import json
from pathlib import Path

from rag.config import RAIZ_REPO, Config
from rag.motor import Motor

PREGUNTAS = RAIZ_REPO / "rag/evaluacion/preguntas_prototipo.json"


def esperados_de(q: dict, empresas: list[dict]) -> set[str]:
    """Expedientes esperados: lista explícita y/o todos los del piloto que cumplen
    ``esperados_ciiu`` (prefijos) y, si se indica, ``esperados_ciudad``."""
    out = {str(e) for e in q.get("esperados", [])}
    prefijos = tuple(q.get("esperados_ciiu", []))
    if prefijos:
        ciudad = q.get("esperados_ciudad", "").upper()
        out |= {
            e["expediente"] for e in empresas
            if e["ciiu"].startswith(prefijos) and (not ciudad or e["ciudad"].strip().upper() == ciudad)
        }
    return out


def evaluar(cfg: Config, ruta_preguntas: str | None = None, salida: str | None = None) -> dict:
    preguntas = json.loads(Path(ruta_preguntas or PREGUNTAS).read_text(encoding="utf-8"))
    motor = Motor(cfg)
    empresas = motor.cliente_b.empresas()
    k = cfg.top_k
    filas, rr, aciertos, con_resp, rechazos_ok, fuera, falsos = [], [], 0, 0, 0, 0, 0
    for q in preguntas:
        r = motor.responder(q["pregunta"], filtros=q.get("filtros"))
        recuperados = [c["frag_id"].split("#")[0].removeprefix("empresa:") for c in r.citas]
        if q.get("rechazo"):
            fuera += 1
            ok = r.modo == "rechazo"
            rechazos_ok += ok
            filas.append({"id": q["id"], "tipo": "fuera_de_alcance", "ok": ok, "modo": r.modo})
            continue
        con_resp += 1
        esperados = esperados_de(q, empresas)
        rango = next((i for i, e in enumerate(recuperados, 1) if e in esperados), None)
        if r.modo == "rechazo":
            falsos += 1
        aciertos += rango is not None
        rr.append(1 / rango if rango else 0.0)
        filas.append({"id": q["id"], "tipo": q.get("tipo", ""), "ok": rango is not None, "rango": rango,
                      "modo": r.modo, "recuperados": recuperados})
    resumen = {
        "modelo_embeddings": cfg.modelo_embeddings,
        "umbral_similitud": cfg.umbral_similitud,
        "umbral_fuerte": cfg.umbral_fuerte,
        "k": k,
        "preguntas": len(preguntas),
        f"acierto@{k}": round(aciertos / con_resp, 3) if con_resp else None,
        "mrr": round(sum(rr) / len(rr), 3) if rr else None,
        "rechazo_correcto": round(rechazos_ok / fuera, 3) if fuera else None,
        "falso_rechazo": falsos,
    }
    res = {"resumen": resumen, "detalle": filas}
    if salida:
        Path(salida).parent.mkdir(parents=True, exist_ok=True)
        Path(salida).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res
