"""Rutas, parámetros y reglas del ETL.

Las capas siguen la metodología Medallion:

- **crudo** (bronce): archivos tal como llegan de la fuente, nunca se editan.
- **plata**: datos limpios, normalizados y validados.
- **oro**: datos listos para publicar por la API y el portal.
"""

from __future__ import annotations

import os
from pathlib import Path

ETL = Path(__file__).resolve().parents[2]
DATOS = ETL / "datos"
CRUDO = DATOS / "crudo"
WEB = CRUDO / "web"
PLATA = DATOS / "plata"
ORO = DATOS / "oro"

ANIO_POR_DEFECTO = 2025

# --- Universo aprobado en la reunión del 04-nov-2026 (docs/universo.md) ---
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

# Tamaño por ventas anuales (COPCI): la columna oficial del ranking viene vacía.
UMBRAL_MEDIANA = 1_000_000
UMBRAL_GRANDE = 5_000_000

# Una empresa grande que declara muy pocos empleados, o que vende muchas más
# veces por empleado que la mediana de su división CIIU, queda marcada.
EMPLEADOS_IMPOSIBLE = 100_000
EMPLEADOS_MINIMO_GRANDE = 10
VECES_MEDIANA_DIVISION = 20

# --- Recolección web (docs/investigacion-b/06-scraping-etico.md) ---
# Sin tildes: una cabecera HTTP no admite caracteres fuera de ASCII.
USER_AGENT = (
    "ObservatorioEPN-Bot/0.1 (+https://github.com/alda244/observatorio-epn; proyecto academico EPN)"
)
SEGUNDOS_ENTRE_PETICIONES = 3.0
PETICIONES_SIMULTANEAS_POR_DOMINIO = 1
PAGINAS_EXTRA_POR_EMPRESA = 3
TIEMPO_LIMITE = 20

# Puntaje mínimo para dar una URL por verificada.
UMBRAL_VERIFICACION = 85
UMBRAL_REVISION = 60

BASE_DE_DATOS = os.getenv(
    "ETL_BASE_DE_DATOS", "postgresql+psycopg://rol_datos:rol_datos@localhost:5432/observatorio"
)


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
