"""Paso `ficha`: Company Profile a partir de lo capturado (capa plata).

Produce los campos que el [ADR 0006](../../../docs/adr/0006-bloque2-company-profile-en-b.md)
asigna a B y que detalla [ficha-empresa.md](../../../docs/ficha-empresa.md):

| Bloque | Campos |
| --- | --- |
| 1. Identificación | Web, correo corporativo, teléfono, redes, ubicación |
| 2. Contenido | Descripción corta, descripción detallada, productos y servicios |
| 3. Validación | Logotipo |

Todo el texto es `literal`: se copia de la fuente, recortado si hace falta. No
se guardan correos ni teléfonos personales, ni cargos directivos (LOPDP).
"""

from __future__ import annotations

import re

import pandas as pd
import pandera.pandas as pa
import trafilatura
from scrapling.parser import Selector

from etl import config
from etl.comun import leer_jsonl, log

CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
TELEFONO = re.compile(r"(\+?593|\b0)[\d\s-]{7,}\d")
CARGOS = re.compile(
    r"\b(gerente|presidente|director|directora|vicepresidente|ceo|cfo|fundador)\b", re.I
)
RUIDO = re.compile(
    r"cookies|derechos reservados|pol[ií]tica de privacidad|suscr[ií]bete|iniciar sesi[oó]n", re.I
)
# Títulos de sección o de menú que no son un producto ni un servicio.
SECCIONES = re.compile(
    r"^(nuestr[oa]s? )?(servicios|productos|soluciones|contacto|cont[aá]ctanos|nosotros"
    r"|qui[eé]nes somos|misi[oó]n|visi[oó]n|valores|historia|trayectoria|certificaciones"
    r"|compromiso|m[eé]todo|noticias|blog|soporte|informaci[oó]n.*|trabaja con nosotros"
    r"|s[ií]guenos|marcas propias|n[uú]mero.*)\b",
    re.I,
)
# Un correo corporativo es genérico; uno con nombre y apellido es dato personal.
CORREO_CORPORATIVO = re.compile(
    r"^(info|ventas|contacto|comercial|servicioalcliente|atencionalcliente|hola|hello|soporte"
    r"|marketing|rrhh|talentohumano|recursoshumanos|administracion|gerencia|secretaria)@",
    re.I,
)

ESQUEMA = pa.DataFrameSchema(
    {
        "expediente": pa.Column(int, unique=True),
        "tagline": pa.Column(str, pa.Check.str_length(max_value=151), nullable=True),
        "descripcion": pa.Column(str, pa.Check.str_length(200, 1300), nullable=True),
        "tagline_origen": pa.Column(str, pa.Check.isin(["literal", "derivado"]), nullable=True),
        "estado": pa.Column(str, pa.Check.isin(["completo", "parcial", "pendiente"])),
    },
    strict=False,
)


def limpiar(texto) -> str:
    if not isinstance(texto, str) or not texto:
        return ""
    return re.sub(r"\s+", " ", CORREO.sub("", TELEFONO.sub("", texto))).strip()


def parrafos_utiles(texto: str) -> list[str]:
    salida = []
    for parrafo in (texto or "").split("\n"):
        parrafo = limpiar(parrafo)
        if len(parrafo) >= 60 and not CARGOS.search(parrafo) and not RUIDO.search(parrafo):
            salida.append(parrafo)
    return salida


def recortar(texto: str, maximo: int) -> str:
    """Recorta en el último fin de oración que entra; si no hay, en la última palabra."""
    if len(texto) <= maximo:
        return texto
    corte = texto[:maximo]
    fin = corte.rfind(".")
    if fin >= maximo // 2:
        return corte[: fin + 1]
    return corte[: corte.rfind(" ")].rstrip(",;:") + "…"


def _organizacion(pagina: pd.Series) -> dict:
    valor = pagina.get("jsonld_organizacion")
    return valor if isinstance(valor, dict) else {}


def html_de(carpeta, pagina: pd.Series) -> str:
    return (carpeta / f"{pagina['expediente']}_{pagina['sha256']}.html").read_text(encoding="utf-8")


def tagline(empresa: pd.DataFrame) -> tuple[str, str]:
    for _, pagina in empresa[empresa["tipo_pagina"] == "portada"].iterrows():
        organizacion = _organizacion(pagina)
        candidatos = (
            organizacion.get("description"),
            pagina.get("og_description"),
            pagina.get("meta_description"),
        )
        for candidato in candidatos:
            texto = limpiar(candidato)
            if len(texto) >= 20:
                return recortar(texto, 150), pagina["url"]
    return "", ""


def descripcion(carpeta, empresa: pd.DataFrame) -> tuple[str, str]:
    for tipo in ("nosotros", "portada"):
        for _, pagina in empresa[empresa["tipo_pagina"] == tipo].iterrows():
            texto = trafilatura.extract(
                html_de(carpeta, pagina), include_comments=False, include_tables=False
            )
            parrafos = parrafos_utiles(texto or "")
            if not parrafos:
                continue
            elegidos, total = [], 0
            for parrafo in parrafos:
                if total + len(parrafo) > 1200 or len(elegidos) == 3:
                    break
                elegidos.append(parrafo)
                total += len(parrafo)
            resultado = "\n\n".join(elegidos) if elegidos else recortar(parrafos[0], 1200)
            if len(resultado) >= 200:
                return resultado, pagina["url"]
    return "", ""


def productos(carpeta, empresa: pd.DataFrame) -> tuple[list[str], str]:
    candidatas = pd.concat(
        [empresa[empresa["tipo_pagina"] == "servicios"], empresa[empresa["tipo_pagina"] == "otra"]]
    )
    for _, pagina in candidatas.iterrows():
        html = Selector(html_de(carpeta, pagina))
        vistos, lista = set(), []
        for titulo in html.css("main h2, main h3, main h4, article h2, article h3, h2, h3"):
            texto = limpiar(" ".join(titulo.css("::text").getall())).rstrip(":").strip()
            clave = texto.lower()
            if (
                3 <= len(texto) <= 60
                and clave not in vistos
                and not SECCIONES.search(texto)
                and not RUIDO.search(texto)
                and not CARGOS.search(texto)
            ):
                vistos.add(clave)
                lista.append(texto)
        if len(lista) >= 2:
            return lista[:15], pagina["url"]
    return [], ""


def identificacion(empresa: pd.DataFrame) -> dict:
    """Bloque 1: contacto corporativo, redes y ubicación, más el logotipo."""
    correos, telefonos, redes, logo, direccion = [], [], [], None, None
    for _, pagina in empresa.iterrows():
        organizacion = _organizacion(pagina)
        correos += [c for c in (pagina.get("correos") or []) if CORREO_CORPORATIVO.match(c)]
        telefonos += list(pagina.get("telefonos") or [])
        redes += list(pagina.get("redes") or [])
        enlazadas = organizacion.get("sameAs") or []
        redes += enlazadas if isinstance(enlazadas, list) else [enlazadas]
        if logo is None:
            marca = organizacion.get("logo") or pagina.get("og_image")
            logo = marca.get("url") if isinstance(marca, dict) else marca
        if direccion is None and organizacion.get("address"):
            señas = organizacion["address"]
            direccion = (
                ", ".join(str(v) for v in señas.values() if isinstance(v, str))
                if isinstance(señas, dict)
                else str(señas)
            )
    return {
        "correo_corporativo": "; ".join(dict.fromkeys(correos)) or None,
        "telefono": "; ".join(dict.fromkeys(telefonos)) or None,
        "redes": "; ".join(dict.fromkeys(redes)) or None,
        "logo_url": logo,
        "direccion": direccion,
    }


def ejecutar(anio: int) -> pd.DataFrame:
    config.preparar(anio)
    carpeta = config.ruta_web(anio)
    registros = leer_jsonl(carpeta / "manifest.jsonl")
    if not registros:
        log.warning(
            "No hay páginas capturadas en %s: ejecute antes `etl web --anio %s`", carpeta, anio
        )
        return pd.DataFrame()

    paginas = pd.DataFrame(registros).drop_duplicates(["expediente", "sha256"])
    paginas = paginas[paginas["status"] == 200]
    urls = pd.read_csv(config.ruta_plata(anio) / "urls_piloto.csv", dtype={"expediente": int})

    filas = []
    for expediente, empresa in paginas.groupby("expediente"):
        corta, corta_url = tagline(empresa)
        larga, larga_url = descripcion(carpeta, empresa)
        lista, lista_url = productos(carpeta, empresa)
        if not corta and larga:  # sin descripción en la portada, la primera oración sirve
            primera = re.split(r"(?<=\.)\s", larga, maxsplit=1)[0]
            if 20 <= len(primera) <= 150:
                corta, corta_url = primera, larga_url
        llenos = sum(bool(x) for x in (corta, larga, lista))
        filas.append(
            {
                "expediente": expediente,
                "tagline": corta or None,
                "tagline_origen": "literal" if corta else None,
                "tagline_fuente": corta_url or None,
                "descripcion": larga or None,
                "descripcion_fuente": larga_url or None,
                "productos_servicios": "; ".join(lista) or None,
                "productos_fuente": lista_url or None,
                **identificacion(empresa),
                "paginas_capturadas": len(empresa),
                "fuente_tipo": "web_oficial",
                "fecha_captura": empresa["fecha_captura"].min()[:10],
                "estado": "completo" if llenos == 3 else ("parcial" if llenos else "pendiente"),
            }
        )

    ficha = urls[["expediente", "nombre", "url_oficial"]].merge(
        pd.DataFrame(filas), on="expediente"
    )
    ficha = ESQUEMA.validate(ficha, lazy=True)
    destino = config.ruta_plata(anio) / "ficha_company_profile.csv"
    ficha.to_csv(destino, index=False)
    log.info("Ficha %s: %s -> %s", anio, ficha["estado"].value_counts().to_dict(), destino)
    return ficha
