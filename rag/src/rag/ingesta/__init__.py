"""Ingesta: convierte las fuentes en documentos normalizados con procedencia.

Fuentes del prototipo:

1. Empresas del piloto (vía ``cliente_b``): se redacta una ficha de
   identificación a partir de los campos oficiales de la SCVS. El texto
   **no contiene cifras**: las cifras se consultan a B en el momento de
   responder (salvaguarda "cifras solo de la API de B").
2. Fichas del Company Profile (vía ``cliente_b``): lema, descripción,
   productos y contacto corporativo tomados de la web oficial de cada
   empresa. Un documento por ficha, citado con la URL oficial y la fecha de
   captura. Las fichas ``pendiente`` no entran.
3. Documentos de texto en ``rag/datos/documentos/`` (Markdown con
   encabezado de metadatos): reportes del Observatorio.

Cada documento lleva ``fuente_url``, ``fuente_tipo``, ``fecha`` y el
``sha256`` de su texto; el hash permite que la ingesta sea idempotente.
"""

from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

GRUPOS = {
    "TEC": "tecnológicas (telecomunicaciones, software y servicios de información)",
    "G": "comercio",
    "C": "manufactura",
    "M": "actividades profesionales, científicas y técnicas",
    "K": "actividades financieras y de seguros",
}
TAMANOS = {"grande": "grande", "mediana": "mediana", "micro_pequena": "micro o pequeña"}


@dataclass
class Documento:
    doc_id: str
    titulo: str
    texto: str
    fuente_url: str
    fuente_tipo: str
    fecha: str
    origen: str = "literal"  # literal | derivado
    metadatos: dict = field(default_factory=dict)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.texto.encode("utf-8")).hexdigest()


def normalizar(texto: str) -> str:
    """Unicode NFC, sin caracteres de control y con espacios simples."""
    texto = unicodedata.normalize("NFC", texto)
    texto = "".join(c for c in texto if c in "\n\t" or unicodedata.category(c)[0] != "C")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def oracion(texto: str) -> str:
    """'VENTA AL POR MAYOR DE X.' -> 'Venta al por mayor de x'."""
    t = texto.strip().rstrip(".").lower()
    return t[:1].upper() + t[1:]


def cargar_catalogo_ciiu(ruta: Path) -> dict[str, str]:
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        return {r["ciiu"].strip(): r["descripcion"].strip() for r in csv.DictReader(f)}


def ficha_identificacion(empresa: dict, ciiu: dict[str, str]) -> Documento:
    """Redacta la ficha de identificación de una empresa (sin cifras)."""
    codigo = empresa["ciiu"]
    division = ciiu.get(codigo[:3], "")
    grupo_ciiu = ciiu.get(codigo[:4], "")
    lineas = [
        empresa["nombre"].rstrip(".") + ".",
        f"Empresa {TAMANOS.get(empresa['tamano_derivado'], '')} del grupo "
        f"{GRUPOS.get(empresa['grupo'], empresa['grupo'])}.",
        f"Actividad principal (CIIU {codigo}): {oracion(empresa['ciiu_descripcion'])}.",
    ]
    if grupo_ciiu:
        lineas.append(f"Grupo de actividad: {oracion(grupo_ciiu)}.")
    if division:
        lineas.append(f"División: {oracion(division)}.")
    lineas.append(
        f"Ubicación: {empresa['ciudad'].title()}, provincia de {empresa['provincia'].title()}, "
        f"región {empresa['region'].title()}."
    )
    lineas.append(f"Tipo de compañía: {empresa['tipo_compania'].lower()}.")
    lineas.append(f"Expediente SCVS: {empresa['expediente']}.")
    return Documento(
        doc_id=f"empresa:{empresa['expediente']}",
        titulo=empresa["nombre"],
        texto=normalizar("\n".join(lineas)),
        fuente_url=empresa["fuente_url"],
        fuente_tipo=empresa["fuente_tipo"],
        fecha=empresa["fecha_corte"],
        origen="derivado",  # redactado a partir de campos oficiales
        metadatos={
            "expediente": empresa["expediente"],
            "grupo": empresa["grupo"],
            "tamano": empresa["tamano_derivado"],
            "provincia": empresa["provincia"],
            "ciudad": empresa["ciudad"],
            "ciiu": codigo,
        },
    )


def ficha_company_profile(empresa: dict, ficha: dict) -> Documento | None:
    """Redacta el documento del Company Profile de una empresa a partir de su ficha.

    Se cita la URL oficial; la URL de cada campo queda en ``metadatos["fuentes"]``.
    """
    if ficha.get("estado") == "pendiente":
        return None
    lineas = [empresa["nombre"].rstrip(".") + "."]
    for etiqueta, campo in (("Lema", "tagline"), ("Descripción", "descripcion"),
                            ("Productos y servicios", "productos_servicios")):
        if ficha.get(campo):
            lineas.append(f"{etiqueta}: {ficha[campo].rstrip('.…')}.")
    contacto = [v for v in (ficha.get("correo_corporativo"), ficha.get("telefono")) if v]
    if contacto:
        lineas.append(f"Contacto corporativo: {'; '.join(contacto)}.")
    if ficha.get("direccion"):
        lineas.append(f"Dirección: {ficha['direccion']}.")
    if ficha.get("url_oficial"):
        lineas.append(f"Sitio web oficial: {ficha['url_oficial']}")
    if len(lineas) == 1:
        return None
    return Documento(
        doc_id=f"perfil:{empresa['expediente']}",
        titulo=empresa["nombre"],
        texto=normalizar("\n".join(lineas)),
        fuente_url=ficha.get("url_oficial") or empresa["fuente_url"],
        fuente_tipo="company_profile",
        fecha=ficha.get("fecha_captura") or empresa["fecha_corte"],
        origen="literal",
        metadatos={
            "expediente": empresa["expediente"],
            "grupo": empresa["grupo"],
            "tamano": empresa["tamano_derivado"],
            "provincia": empresa["provincia"],
            "ciudad": empresa["ciudad"],
            "ciiu": empresa["ciiu"],
            "estado_ficha": ficha.get("estado"),
            "fuentes": ficha.get("fuentes") or {},
        },
    )


_ENCABEZADO = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def leer_documento_markdown(ruta: Path) -> Documento:
    """Lee un .md con encabezado ``clave: valor`` entre líneas ``---``.

    Claves obligatorias: ``titulo``, ``fuente_url``, ``fuente_tipo``, ``fecha``.
    Opcionales: ``origen`` (literal/derivado), ``expediente``.
    """
    crudo = Path(ruta).read_text(encoding="utf-8").replace("\r\n", "\n")
    m = _ENCABEZADO.match(crudo)
    if not m:
        raise ValueError(f"{ruta}: falta el encabezado de metadatos entre '---'")
    meta: dict[str, str] = {}
    for linea in m.group(1).splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            meta[k.strip()] = v.strip()
    faltan = {"titulo", "fuente_url", "fuente_tipo", "fecha"} - meta.keys()
    if faltan:
        raise ValueError(f"{ruta}: faltan metadatos {sorted(faltan)}")
    extra = {k: v for k, v in meta.items() if k not in {"titulo", "fuente_url", "fuente_tipo", "fecha", "origen"}}
    return Documento(
        doc_id=f"doc:{Path(ruta).stem}",
        titulo=meta["titulo"],
        texto=normalizar(m.group(2)),
        fuente_url=meta["fuente_url"],
        fuente_tipo=meta["fuente_tipo"],
        fecha=meta["fecha"],
        origen=meta.get("origen", "literal"),
        metadatos=extra,
    )


def cargar_documentos(carpeta: Path) -> list[Documento]:
    carpeta = Path(carpeta)
    if not carpeta.exists():
        return []
    return [leer_documento_markdown(p) for p in sorted(carpeta.glob("*.md")) if p.name != "README.md"]
