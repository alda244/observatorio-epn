"""Utilidades compartidas por los pasos del pipeline."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

log = logging.getLogger("etl")

# Formas jurídicas que se quitan de la razón social para quedarse con el nombre.
FORMAS_JURIDICAS = (
    r"\b(S\.?\s?A\.?\s?S\.?|S\.?\s?A\.?|C\.?\s?A\.?|C\.?\s?L\.?|C[IÍ]A\.?\s?LTDA\.?|LTDA\.?"
    r"|SOCIEDAD AN[OÓ]NIMA|COMPA[ÑN][IÍ]A LIMITADA|SOCIEDAD POR ACCIONES SIMPLIFICADA"
    r"|SOCIEDAD DE BENEFICIO E INTER[EÉ]S COLECTIVO)\b"
)
# Palabras que no identifican a una empresa concreta.
PALABRAS_GENERICAS = {
    "SOCIEDAD",
    "CORPORACION",
    "CONSORCIO",
    "COMPANIA",
    "GRUPO",
    "NACIONAL",
    "INDUSTRIAL",
    "INDUSTRIAS",
    "PROCESADORA",
    "DISTRIBUIDORA",
    "COMERCIAL",
    "SERVICIOS",
    "SISTEMA",
    "TIENDAS",
    "EMPRESA",
    "ECUADOR",
    "ECUATORIANA",
    "ECUATORIANO",
    "DEL",
    "LA",
    "LAS",
    "LOS",
    "EL",
    "DE",
    "Y",
    "E",
    "EN",
    "PARA",
}


def configurar_registro(detallado: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if detallado else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def sha256_bytes(contenido: bytes) -> str:
    """Hash del contenido tal como llegó.

    Las páginas se guardan y se verifican por bytes, no por texto. Leer un
    archivo en modo texto traduce `\r\n` a `\n`, así que el texto leído no
    sería idéntico al capturado y el hash no verificaría.
    """
    return hashlib.sha256(contenido).hexdigest()


def sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn"
    )


def normalizar(texto: Any) -> str:
    """Mayúsculas, sin tildes ni signos, con espacios simples."""
    if not isinstance(texto, str):
        return ""
    return " ".join(re.sub(r"[^A-Z0-9 ]+", " ", sin_tildes(texto).upper()).split())


def partes_nombre(razon_social: str) -> tuple[str, str]:
    """Separa la razón social en (base, nombre comercial).

    Muchas razones sociales llevan el nombre comercial después de la forma
    jurídica: "CONSORCIO ECUATORIANO DE TELECOMUNICACIONES S.A. CONECEL".
    """
    texto = sin_tildes(razon_social).upper()
    marcas = list(re.finditer(FORMAS_JURIDICAS, texto))
    comercial = normalizar(texto[marcas[-1].end() :]) if marcas else ""
    sin_forma = texto[: marcas[-1].start()] if marcas and comercial else texto
    return normalizar(re.sub(FORMAS_JURIDICAS, " ", sin_forma)), comercial


def tokens_distintivos(razon_social: str) -> list[str]:
    """Palabras del nombre que sirven para identificar a la empresa."""
    base, comercial = partes_nombre(razon_social)
    palabras = ([comercial] if comercial else []) + base.split()
    return [p for p in palabras if len(p) > 3 and p not in PALABRAS_GENERICAS]


def guardar_json(ruta: Path, datos: dict) -> None:
    Path(ruta).write_text(
        json.dumps(datos, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def leer_jsonl(ruta: Path) -> list[dict]:
    if not Path(ruta).exists():
        return []
    return [
        json.loads(linea) for linea in Path(ruta).read_text(encoding="utf-8").splitlines() if linea
    ]
