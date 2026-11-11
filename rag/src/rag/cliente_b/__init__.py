"""Cliente de la API del Componente B.

Regla de arquitectura: A nunca lee la base de B; solo consume su API. Mientras
la API no exista, ``ClienteBArchivo`` lee la exportación publicada por B
(``piloto_500.csv``) y devuelve registros con la forma prevista para
``GET /empresas`` y ``GET /empresas/{expediente}``. En el Sprint 6 se agrega
``ClienteBHttp`` con la misma interfaz.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Protocol

URL_RANKING = "https://appscvsmovil.supercias.gob.ec/ranking/reporte.html"
FECHA_CORTE_RANKING = "2026-10-22"

CAMPOS_NUMERICOS = ("empleados", "activo", "patrimonio", "ventas", "utilidad_neta", "ingreso_total")
CAMPOS_BOOLEANOS = ("es_holding", "alerta_empleados", "en_top50_tec")


class ClienteB(Protocol):
    def empresas(self) -> list[dict]: ...

    def empresa(self, expediente: str) -> dict | None: ...


def _convertir(fila: dict) -> dict:
    out = dict(fila)
    out["expediente"] = str(fila["expediente"]).strip()
    for c in CAMPOS_NUMERICOS:
        if c in out and out[c] not in ("", None):
            out[c] = float(out[c])
    for c in CAMPOS_BOOLEANOS:
        if c in out:
            out[c] = str(out[c]).strip().lower() == "true"
    out["fuente_url"] = URL_RANKING
    out["fuente_tipo"] = "scvs_ranking"
    out["fecha_corte"] = FECHA_CORTE_RANKING
    return out


class ClienteBArchivo:
    """Simula la API de B a partir de su exportación CSV."""

    def __init__(self, ruta: Path) -> None:
        with Path(ruta).open(encoding="utf-8", newline="") as f:
            self._filas = [_convertir(r) for r in csv.DictReader(f)]
        self._por_exp = {r["expediente"]: r for r in self._filas}

    def empresas(self) -> list[dict]:
        return list(self._filas)

    def empresa(self, expediente: str) -> dict | None:
        return self._por_exp.get(str(expediente))
