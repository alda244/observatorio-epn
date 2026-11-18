"""Evaluación de la recuperación del prototipo.

Cada pregunta de referencia indica los expedientes que deben recuperarse
(``esperados`` o ``esperados_ciiu``; basta uno en el top k) o ``"rechazo": true`` cuando el asistente debe
responder que no hay dato publicado: preguntas fuera de alcance o sobre datos
que el Observatorio no tiene (``sin_dato``). Métricas:

- ``acierto@k``: fracción de preguntas con al menos un esperado en el top k.
- ``mrr``: media del inverso del rango del primer esperado.
- ``rechazo_correcto``: fracción de preguntas fuera de alcance rechazadas.
- ``sin_dato_correcto``: fracción de preguntas sobre datos no publicados rechazadas.
- ``falso_rechazo``: preguntas con respuesta que el umbral rechazó.
- ``por_tipo``: aciertos sobre total en cada tipo de pregunta.

Es la línea base del Sprint 2; RAGAS (fidelidad y pertinencia) se agrega en
el Sprint 3, cuando haya generación con LLM.
"""

from __future__ import annotations

import json
from pathlib import Path

from rag.config import RAIZ_REPO, Config
from rag.motor import Motor

PREGUNTAS = RAIZ_REPO / "rag/evaluacion/preguntas_referencia.json"


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


def _tasa(ok: int, total: int) -> float | None:
    return round(ok / total, 3) if total else None


def _por_tipo(filas: list[dict]) -> dict[str, str]:
    out: dict[str, list[int]] = {}
    for f in filas:
        c = out.setdefault(f["tipo"], [0, 0])
        c[0] += f["ok"]
        c[1] += 1
    return {t: f"{ok}/{n}" for t, (ok, n) in out.items()}


def evaluar(cfg: Config, ruta_preguntas: str | None = None, salida: str | None = None) -> dict:
    preguntas = json.loads(Path(ruta_preguntas or PREGUNTAS).read_text(encoding="utf-8"))
    motor = Motor(cfg)
    empresas = motor.cliente_b.empresas()
    k = cfg.top_k
    filas, rr, aciertos, con_resp, falsos = [], [], 0, 0, 0
    rechazos = {"fuera_de_alcance": [0, 0], "sin_dato": [0, 0]}  # [correctos, total]
    for q in preguntas:
        r = motor.responder(q["pregunta"], filtros=q.get("filtros"))
        recuperados = [c["frag_id"].split("#")[0].removeprefix("empresa:") for c in r.citas]
        if q.get("rechazo"):
            tipo = q.get("tipo", "fuera_de_alcance")
            ok = r.modo == "rechazo"
            rechazos.setdefault(tipo, [0, 0])
            rechazos[tipo][0] += ok
            rechazos[tipo][1] += 1
            filas.append({"id": q["id"], "tipo": tipo, "ok": ok, "modo": r.modo})
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
        "rechazo_correcto": _tasa(*rechazos["fuera_de_alcance"]),
        "sin_dato_correcto": _tasa(*rechazos["sin_dato"]),
        "falso_rechazo": falsos,
        "por_tipo": _por_tipo(filas),
    }
    res = {"resumen": resumen, "detalle": filas}
    if salida:
        Path(salida).parent.mkdir(parents=True, exist_ok=True)
        Path(salida).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res
