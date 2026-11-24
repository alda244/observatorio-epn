"""Shared paths, fiscal years, and sampling rules for the ETL."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

ETL = Path(__file__).resolve().parents[2]
DATOS = ETL / "datos"
CRUDO = DATOS / "crudo"
WEB = CRUDO / "web"
PLATA = DATOS / "plata"
ORO = DATOS / "oro"

ANIO_UNIVERSO = 2025
ANIO_POR_DEFECTO = ANIO_UNIVERSO
ANIO_MINIMO_COMPARABLE = 2012
COBERTURA_MINIMA_VENTAS = 50.0

PREFIJOS_TEC = ("J61", "J62", "J63", "J582")
SECCIONES = ("G", "C", "M", "K")
GRUPOS = {
    "TEC": "Tecnológicas (J61, J62, J63, J582)",
    "G": "Comercio",
    "C": "Manufactura",
    "M": "Actividades profesionales, científicas y técnicas",
    "K": "Actividades financieras y de seguros",
}
TOP_N = 50


def database_url() -> str:
    """Resolve the database connection only when a command needs it."""
    url = os.getenv("ETL_BASE_DE_DATOS") or dotenv_values(ETL / ".env").get("ETL_BASE_DE_DATOS")
    if not url:
        raise RuntimeError("Configura ETL_BASE_DE_DATOS en etl/.env o en el entorno.")
    return url


def ruta_crudo(anio: int) -> Path:
    return CRUDO / str(anio)


def ruta_plata(anio: int) -> Path:
    return PLATA / str(anio)


def ruta_oro(anio: int) -> Path:
    return ORO / str(anio)


def ruta_web(anio: int) -> Path:
    return WEB / str(anio)


def preparar(anio: int) -> None:
    """Crea las carpetas de salida del año si no existen."""
    for carpeta in (ruta_plata(anio), ruta_oro(anio), ruta_web(anio)):
        carpeta.mkdir(parents=True, exist_ok=True)
