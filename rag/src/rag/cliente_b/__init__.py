"""Cliente de la API del Componente B.

Regla de arquitectura: A nunca lee la base de B; solo consume su API. Hay dos
clientes con la misma interfaz:

- ``ClienteBArchivo`` simula la API con lo que B publica en el repositorio:
  ``piloto_500.csv`` para las empresas y ``etl/seed/profiles.csv`` para las
  fichas del Company Profile. Sirve para desarrollar y para la CI sin levantar
  la API.
- ``ClienteBHttp`` consume ``GET /v1/empresas`` y ``GET /v1/empresas/{expediente}``
  de la API de B (``scripts/start-local.cmd`` la levanta en local).

Ambos devuelven las empresas con la forma de ``piloto_500.csv`` y las fichas
con la forma de ``ficha`` en el detalle de la API.
"""

from __future__ import annotations

import csv
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Protocol

URL_RANKING = "https://appscvsmovil.supercias.gob.ec/ranking/reporte.html"
FECHA_CORTE_RANKING = "2026-10-22"

CAMPOS_NUMERICOS = ("empleados", "activo", "patrimonio", "ventas", "utilidad_neta", "ingreso_total")
CAMPOS_BOOLEANOS = ("es_holding", "alerta_empleados", "en_top50_tec")
# Columna de profiles.csv con la URL de origen de cada campo de la ficha.
FUENTES_FICHA = {"tagline": "tagline_fuente", "descripcion": "descripcion_fuente",
                 "productos_servicios": "productos_fuente"}
CAMPOS_FICHA = ("url_oficial", "tagline", "descripcion", "productos_servicios", "correo_corporativo",
                "telefono", "direccion")


class ClienteB(Protocol):
    def empresas(self) -> list[dict]: ...

    def empresa(self, expediente: str) -> dict | None: ...

    def fichas(self) -> dict[str, dict]: ...


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


def _ficha_csv(fila: dict) -> dict:
    """Fila de profiles.csv -> ficha con la forma de la API."""
    ficha = {c: (fila.get(c) or "").strip() or None for c in CAMPOS_FICHA}
    ficha["redes"] = [r.strip() for r in (fila.get("redes") or "").split(";") if r.strip()]
    ficha["fuente_tipo"] = fila.get("fuente_tipo") or "web_oficial"
    ficha["fecha_captura"] = fila.get("fecha_captura") or ""
    ficha["estado"] = fila.get("estado") or "pendiente"
    ficha["fuentes"] = {c: fila[col].strip() for c, col in FUENTES_FICHA.items() if (fila.get(col) or "").strip()}
    return ficha


class ClienteBArchivo:
    """Simula la API de B a partir de su exportación CSV y de sus fichas."""

    def __init__(self, ruta: Path, ruta_fichas: Path | None = None) -> None:
        with Path(ruta).open(encoding="utf-8", newline="") as f:
            self._filas = [_convertir(r) for r in csv.DictReader(f)]
        self._por_exp = {r["expediente"]: r for r in self._filas}
        self._fichas: dict[str, dict] = {}
        if ruta_fichas and Path(ruta_fichas).exists():
            with Path(ruta_fichas).open(encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    exp = str(r["expediente"]).strip()
                    if exp in self._por_exp:
                        self._fichas[exp] = _ficha_csv(r)

    def empresas(self) -> list[dict]:
        return list(self._filas)

    def empresa(self, expediente: str) -> dict | None:
        return self._por_exp.get(str(expediente))

    def fichas(self) -> dict[str, dict]:
        return dict(self._fichas)


def _detalle_a_empresa(d: dict) -> dict:
    """Detalle de ``GET /v1/empresas/{expediente}`` -> forma de piloto_500.csv."""
    cifras = sorted(d.get("cifras") or [], key=lambda c: c["anio"])
    ultima = cifras[-1] if cifras else {}
    proc = ultima.get("procedencia") or {}
    out = {
        "expediente": str(d["expediente"]),
        "nombre": d["nombre"],
        "grupo": d["grupo"],
        "ciiu": d["ciiu"],
        "ciiu_descripcion": d.get("ciiu_descripcion") or "",
        "seccion_ciiu": d.get("seccion_ciiu") or "",
        "division_ciiu": d.get("division_ciiu") or "",
        "tamano_derivado": d.get("tamano") or ultima.get("tamano") or "",
        "tipo_compania": d.get("tipo_compania") or "",
        "region": d.get("region") or "",
        "provincia": d.get("provincia") or "",
        "ciudad": d.get("ciudad") or "",
        "es_holding": bool(d.get("es_holding")),
        "alerta_empleados": bool(ultima.get("tiene_alerta", d.get("tiene_alerta"))),
        "anio": ultima.get("anio"),
        "cifras": cifras,
        "fuente_url": proc.get("fuente_url") or URL_RANKING,
        "fuente_tipo": proc.get("fuente_tipo") or "scvs_ranking",
        "fecha_corte": proc.get("fecha_corte") or FECHA_CORTE_RANKING,
    }
    for c in CAMPOS_NUMERICOS:
        out[c] = ultima.get(c)
    return out


class ClienteBHttp:
    """Consume la API de B. Lee el piloto completo una vez y lo guarda en memoria."""

    def __init__(self, base_url: str, timeout: float = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._detalles: dict[str, dict] | None = None

    def _get(self, ruta: str, **params) -> dict | None:
        url = f"{self.base_url}{ruta}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def _cargar(self) -> dict[str, dict]:
        if self._detalles is None:
            exps, offset = [], 0
            while True:
                pagina = self._get("/v1/empresas", en_piloto="true", limit=100, offset=offset, orden="nombre")
                exps += [str(e["expediente"]) for e in pagina["datos"]]
                offset += pagina["limit"]
                if offset >= pagina["total"]:
                    break
            self._detalles = {e: d for e in exps if (d := self._get(f"/v1/empresas/{e}"))}
        return self._detalles

    def empresas(self) -> list[dict]:
        return [_detalle_a_empresa(d) for d in self._cargar().values()]

    def empresa(self, expediente: str) -> dict | None:
        exp = str(expediente)
        d = self._detalles.get(exp) if self._detalles is not None else self._get(f"/v1/empresas/{exp}")
        return _detalle_a_empresa(d) if d else None

    def fichas(self) -> dict[str, dict]:
        return {e: d["ficha"] for e, d in self._cargar().items() if d.get("ficha")}


def crear_cliente_b(cfg) -> ClienteB:
    if cfg.fuente_b == "http":
        return ClienteBHttp(cfg.api_b_url)
    return ClienteBArchivo(cfg.fuente_empresas, cfg.fichas)
