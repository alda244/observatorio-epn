"""Paso `urls`: encontrar y verificar la web oficial de cada empresa del piloto.

La SCVS no publica la web de las empresas y los buscadores prohíben la consulta
automatizada, así que las candidatas se derivan del nombre y se comprueban:

1. Se arman dominios a partir del nombre comercial y de la razón social.
2. Se descarta por DNS lo que no existe, sin tocar ningún sitio.
3. Se visita solo la portada, con la configuración ética del proyecto.
4. Se puntúa la evidencia de que el sitio es de esa empresa.

El resultado se guarda en `plata/<anio>/urls_piloto.csv` y el paso es
reanudable: lo ya verificado o corregido a mano no se vuelve a visitar.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from rapidfuzz import fuzz
from scrapling.fetchers import FetcherSession
from scrapling.spiders import Request, Spider

from etl import config
from etl.comun import log, normalizar, partes_nombre, tokens_distintivos

TLDS = (".com.ec", ".ec", ".com", ".net.ec")
ESTADOS_CERRADOS = ("si", "manual")
COLUMNAS = [
    "expediente",
    "nombre",
    "grupo",
    "criterio_piloto",
    "url_oficial",
    "url_fuente",
    "url_verificada",
    "puntaje",
    "evidencia",
    "titulo",
    "senales",
    "fecha_verificacion",
    "verificado_por",
]


def candidatos_de(nombre: str) -> list[str]:
    """Dominios plausibles para una empresa, del más probable al menos."""
    base, comercial = partes_nombre(nombre)
    tokens = [t for t in tokens_distintivos(nombre)]
    nombres: list[str] = []
    if comercial and len(comercial.replace(" ", "")) >= 4:
        nombres.append(comercial.replace(" ", ""))
    if tokens:
        nombres.append(tokens[0])
        if len(tokens) >= 2:
            nombres.append(tokens[0] + tokens[1])
        if 2 <= len(tokens) <= 3:
            nombres.append("".join(tokens))
        # Sigla con la inicial de cada palabra distintiva (mínimo tres).
        if len(tokens) >= 3:
            nombres.append("".join(t[0] for t in tokens))
    vistos, salida = set(), []
    for n in nombres:
        n = n.lower()
        if len(n) < 4 or n in vistos:
            continue
        vistos.add(n)
        salida.extend(n + tld for tld in TLDS)
    return salida


def resuelve(dominio: str) -> bool:
    try:
        socket.getaddrinfo(dominio, 443)
        return True
    except OSError:
        return False


def filtrar_por_dns(candidatos: pd.DataFrame) -> pd.DataFrame:
    with ThreadPoolExecutor(max_workers=16) as pool:
        candidatos = candidatos.assign(resuelve=list(pool.map(resuelve, candidatos["dominio"])))
    vivos = candidatos[candidatos["resuelve"]].reset_index(drop=True)
    log.info("Dominios que existen: %s de %s", len(vivos), len(candidatos))
    return vivos


class VerificadorPortada(Spider):
    """Lee la portada de cada dominio candidato respetando las reglas del proyecto."""

    name = "verificador_portada"
    robots_txt_obey = True
    concurrent_requests = 4
    concurrent_requests_per_domain = config.PETICIONES_SIMULTANEAS_POR_DOMINIO
    download_delay = config.SEGUNDOS_ENTRE_PETICIONES
    max_blocked_retries = 0  # si el sitio bloquea, no se insiste
    logging_level = logging.WARNING

    def __init__(self, candidatos: pd.DataFrame):
        self.candidatos = candidatos
        super().__init__()

    def configure_sessions(self, manager):
        manager.add(
            "etico",
            FetcherSession(
                impersonate=None,  # sin suplantar un navegador
                stealthy_headers=False,
                headers={"User-Agent": config.USER_AGENT},
                retries=1,
                timeout=config.TIEMPO_LIMITE,
            ),
        )

    async def start_requests(self):
        for c in self.candidatos.itertuples():
            yield Request(
                f"https://{c.dominio}/",
                sid="etico",
                callback=self.parse,
                dont_filter=True,
                meta={"expediente": c.expediente, "dominio": c.dominio, "origen": c.origen},
            )

    async def parse(self, r):
        yield {
            **{k: r.meta[k] for k in ("expediente", "dominio", "origen")},
            "status": r.status,
            "url_final": r.url,
            "title": r.css("title::text").get() or "",
            "og_site_name": r.css('meta[property="og:site_name"]::attr(content)').get() or "",
            "texto": " ".join(r.css("body *::text").getall())[:30_000],
        }


def puntuar(visita: dict, empresa: pd.Series) -> dict:
    """Evidencia de que la portada pertenece a la empresa.

    | Evidencia | Puntaje |
    | --- | --- |
    | El RUC aparece en la página | 100 |
    | Nombre comercial completo en el título o el nombre del sitio | 100 |
    | Razón social dentro del texto | similitud de rapidfuzz |
    | El dominio es un token distintivo del nombre y el sitio responde | 70 |

    Además se anotan las señales encontradas, aunque no suban el puntaje. No
    se usan para verificar sola: un dominio genérico como `galapagos.com`
    menciona Ecuador sin ser de la empresa. Sirven para que la revisión a mano
    de las filas en `revisar` se haga de un vistazo, con el título de la
    página al lado.
    """
    base, comercial = partes_nombre(empresa["nombre"])
    texto = normalizar(visita["texto"])
    cabecera = normalizar(f"{visita['title']} {visita['og_site_name']}")
    dominio = visita["dominio"].split(".")[0].upper()

    ruc_empresa = empresa.get("ruc")
    ruc = (
        isinstance(ruc_empresa, str)
        and len(ruc_empresa) == 13
        and ruc_empresa in re.sub(r"\D", "", visita["texto"])
    )
    por_comercial = bool(comercial) and bool(re.search(rf"\b{re.escape(comercial)}\b", cabecera))
    por_base = fuzz.partial_ratio(base, texto) if len(base) >= 8 else 0
    tokens = tokens_distintivos(empresa["nombre"])
    por_dominio = 70 if dominio in tokens else 0

    senales = []
    if ruc:
        senales.append("ruc")
    if por_comercial:
        senales.append("nombre_comercial")
    if por_base >= config.UMBRAL_VERIFICACION:
        senales.append("razon_social")
    if por_dominio:
        senales.append("dominio")
    if visita["dominio"].endswith((".ec", ".com.ec", ".net.ec")):
        senales.append("tld_ec")
    if "ECUADOR" in texto:
        senales.append("menciona_ecuador")
    if any(t in cabecera for t in tokens):
        senales.append("nombre_en_titulo")

    comun = {"titulo": (visita["title"] or "").strip()[:120], "senales": " ".join(senales)}
    if ruc:
        return {"puntaje": 100, "evidencia": "ruc", **comun}
    if por_comercial:
        return {"puntaje": 100, "evidencia": "nombre_comercial", **comun}
    mejor = max(por_base, por_dominio)
    evidencia = "razon_social" if por_base >= por_dominio else "dominio_coincide_con_nombre"
    return {"puntaje": round(mejor), "evidencia": evidencia, **comun}


def clasificar(puntaje: float | None) -> str:
    if puntaje is None or pd.isna(puntaje):
        return "no_encontrada"
    if puntaje >= config.UMBRAL_VERIFICACION:
        return "si"
    if puntaje >= config.UMBRAL_REVISION:
        return "revisar"
    return "no_encontrada"


async def ejecutar(anio: int, limite_por_criterio: int | None = None) -> pd.DataFrame:
    config.preparar(anio)
    piloto = pd.read_csv(
        config.ruta_oro(anio) / "piloto.csv", dtype={"ruc": str, "expediente": int}
    )
    salida = config.ruta_plata(anio) / "urls_piloto.csv"
    previo = (
        pd.read_csv(salida, dtype={"expediente": int})
        if salida.exists()
        else pd.DataFrame(columns=COLUMNAS)
    )

    cerradas = set(previo.loc[previo["url_verificada"].isin(ESTADOS_CERRADOS), "expediente"])
    pendientes = piloto[~piloto["expediente"].isin(cerradas)]
    if limite_por_criterio:
        pendientes = pendientes.groupby("criterio_piloto").head(limite_por_criterio)
    if pendientes.empty:
        log.info("No hay empresas pendientes de verificar")
        return previo
    log.info("Buscando la web de %s empresas", len(pendientes))

    candidatos = pd.DataFrame(
        [
            {"expediente": e.expediente, "dominio": d, "origen": "dominio_derivado"}
            for e in pendientes.itertuples()
            for d in candidatos_de(e.nombre)
        ]
    )
    vivos = filtrar_por_dns(candidatos)

    visitas = []
    if not vivos.empty:
        visitas = [item async for item in VerificadorPortada(vivos).stream()]
    log.info("Portadas leídas: %s", len(visitas))

    empresas = pendientes.set_index("expediente")
    resultados = pd.DataFrame(
        [
            {
                "expediente": v["expediente"],
                "url_oficial": v["url_final"],
                "url_fuente": v["origen"],
                **puntuar(v, empresas.loc[v["expediente"]]),
            }
            for v in visitas
            if v["status"] == 200
        ]
    )
    mejores = (
        resultados.sort_values("puntaje", ascending=False).drop_duplicates("expediente")
        if not resultados.empty
        else pd.DataFrame(
            columns=[
                "expediente",
                "url_oficial",
                "url_fuente",
                "puntaje",
                "evidencia",
                "titulo",
                "senales",
            ]
        )
    )

    nuevo = pendientes[["expediente", "nombre", "grupo", "criterio_piloto"]].merge(
        mejores, on="expediente", how="left"
    )
    nuevo["url_verificada"] = nuevo["puntaje"].map(clasificar)
    nuevo.loc[nuevo["url_verificada"] == "no_encontrada", ["url_oficial", "url_fuente"]] = pd.NA
    nuevo["fecha_verificacion"] = dt.date.today().isoformat()
    nuevo["verificado_por"] = "etl urls"

    conservar = previo[~previo["expediente"].isin(nuevo["expediente"])]
    final = pd.concat([conservar, nuevo[COLUMNAS]], ignore_index=True)
    final.to_csv(salida, index=False)
    log.info("URLs %s: %s", anio, final["url_verificada"].value_counts().to_dict())
    return final
