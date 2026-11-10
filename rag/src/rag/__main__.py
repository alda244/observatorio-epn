"""Línea de comandos del prototipo.

    python -m rag ingesta [--reconstruir]
    python -m rag consulta "¿Qué empresas desarrollan software en Cuenca?" [--grupo TEC] [--json]
    python -m rag evaluar [--salida rag/evidencias/eval.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from rag.config import Config


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="rag", description="Prototipo del asistente RAG del Observatorio EPN")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingesta", help="Construye o actualiza el índice")
    pi.add_argument("--reconstruir", action="store_true", help="Borra el índice y lo construye de cero")

    pc = sub.add_parser("consulta", help="Responde una pregunta con citas")
    pc.add_argument("pregunta")
    for f in ("grupo", "provincia", "ciudad", "tamano"):
        pc.add_argument(f"--{f}")
    pc.add_argument("--json", action="store_true")

    pe = sub.add_parser("evaluar", help="Evalúa la recuperación con las preguntas de referencia")
    pe.add_argument("--preguntas", default=None)
    pe.add_argument("--salida", default=None)

    a = p.parse_args(argv)
    cfg = Config()

    if a.cmd == "ingesta":
        from rag.pipeline import ingerir

        print(json.dumps(asdict(ingerir(cfg, reconstruir=a.reconstruir)), ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "consulta":
        from rag.motor import Motor

        filtros = {k: getattr(a, k) for k in ("grupo", "provincia", "ciudad", "tamano") if getattr(a, k)}
        r = Motor(cfg).responder(a.pregunta, filtros=filtros or None)
        if a.json:
            print(json.dumps(asdict(r), ensure_ascii=False, indent=2))
        else:
            print(r.respuesta)
            if r.citas:
                print("\nFuentes:")
                for c in r.citas:
                    print(f"  [{c['n']}] {c['titulo']} · {c['fuente_tipo']} · {c['fuente_url']} · corte {c['fecha']}")
            for w in r.advertencias:
                print(f"\nAdvertencia: {w}")
            print(f"\n(modo {r.modo} · {r.latencia_ms} ms · traza {r.traza_id})")
        return 0

    if a.cmd == "evaluar":
        from rag.evaluacion import evaluar

        res = evaluar(cfg, a.preguntas, a.salida)
        print(json.dumps(res["resumen"], ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
