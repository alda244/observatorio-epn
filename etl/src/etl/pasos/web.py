"""Paso `web`: captura de las webs oficiales verificadas (capa crudo).

De cada empresa se guarda la portada y hasta tres páginas institucionales
("nosotros", "servicios", "productos"), y se registran los PDF oficiales
enlazados. El HTML se guarda sin modificar; la extracción es del paso `ficha`.

Reglas (docs/investigacion-b/06-scraping-etico.md): se respeta robots.txt, el
bot se identifica, no se suplanta un navegador, una petición por dominio cada
tres segundos y no se insiste si el sitio bloquea. Solo texto institucional.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from urllib.parse import urlparse

import extruct
import pandas as pd
from scrapling.fetchers import FetcherSession
from scrapling.spiders import Request, Spider

from etl import config
from etl.comun import leer_jsonl, log, sha256_texto

INSTITUCIONAL = re.compile(
    r"nosotros|quienes|qui[eé]nes|about|empresa|historia|servicio|producto|soluci"
    r"|catalogo|cat[aá]logo|portafolio",
    re.I,
)
PDF_OFICIAL = re.compile(
    r"memoria|informe|sostenibilidad|reporte|catalogo|cat[aá]logo|brochure|folleto|portafolio", re.I
)
REDES = (
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "x.com",
    "twitter.com",
    "youtube.com",
    "tiktok.com",
)


def tipo_pagina(url: str) -> str:
    ruta = urlparse(url).path.lower()
    if ruta in ("", "/"):
        return "portada"
    if re.search(r"nosotros|quienes|about|empresa|historia", ruta):
        return "nosotros"
    if re.search(r"servicio|producto|soluci|catalogo|portafolio", ruta):
        return "servicios"
    return "otra"


def metadatos(html: str, url: str) -> dict:
    """Metadatos declarados por la propia página: Open Graph y JSON-LD."""
    try:
        datos = extruct.extract(html, base_url=url, syntaxes=["json-ld", "opengraph"], uniform=True)
    except Exception as e:  # una página malformada no debe detener la captura
        log.debug("Sin metadatos en %s: %s", url, e)
        return {}
    og = (datos.get("opengraph") or [{}])[0]
    organizacion = next(
        (d for d in datos.get("json-ld", []) if str(d.get("@type", "")).endswith("Organization")),
        {},
    )
    return {
        "og_title": og.get("og:title"),
        "og_description": og.get("og:description"),
        "og_site_name": og.get("og:site_name"),
        "og_image": og.get("og:image"),
        "jsonld_organizacion": {
            k: organizacion.get(k)
            for k in (
                "name",
                "description",
                "logo",
                "url",
                "sameAs",
                "telephone",
                "email",
                "address",
            )
            if organizacion.get(k)
        },
    }


class CapturaWeb(Spider):
    name = "captura_web"
    robots_txt_obey = True
    concurrent_requests = 4
    concurrent_requests_per_domain = config.PETICIONES_SIMULTANEAS_POR_DOMINIO
    download_delay = config.SEGUNDOS_ENTRE_PETICIONES
    max_blocked_retries = 0
    logging_level = logging.WARNING

    def __init__(self, objetivo: pd.DataFrame):
        self.objetivo = objetivo
        self.extra_por_empresa: dict[int, int] = {}
        super().__init__()

    def configure_sessions(self, manager):
        manager.add(
            "etico",
            FetcherSession(
                impersonate=None,
                stealthy_headers=False,
                headers={"User-Agent": config.USER_AGENT},
                retries=1,
                timeout=config.TIEMPO_LIMITE,
            ),
        )

    async def start_requests(self):
        for e in self.objetivo.itertuples():
            yield Request(
                e.url_oficial,
                sid="etico",
                callback=self.parse,
                meta={"expediente": int(e.expediente)},
            )

    async def parse(self, r):
        expediente = r.meta["expediente"]
        html = r.body.decode(r.encoding or "utf-8", errors="replace")
        enlaces = [
            (a.attrib.get("href", ""), " ".join(a.css("::text").getall())) for a in r.css("a[href]")
        ]
        pdfs = sorted(
            {
                r.urljoin(href)
                for href, texto in enlaces
                if href.lower().endswith(".pdf") and PDF_OFICIAL.search(href + " " + texto)
            }
        )
        redes = sorted(
            {r.urljoin(href) for href, _ in enlaces if any(red in href.lower() for red in REDES)}
        )
        yield {
            "expediente": expediente,
            "url": r.url,
            "tipo_pagina": tipo_pagina(r.url),
            "status": r.status,
            "fecha_captura": dt.datetime.now().isoformat(timespec="seconds"),
            "html": html,
            "title": r.css("title::text").get(),
            "meta_description": r.css('meta[name="description"]::attr(content)').get(),
            "h1": [t.strip() for t in r.css("h1 ::text").getall() if t.strip()][:3],
            "correos": sorted(
                {
                    h.removeprefix("mailto:").split("?")[0].strip().lower()
                    for h, _ in enlaces
                    if h.lower().startswith("mailto:")
                }
            ),
            "telefonos": sorted(
                {h.removeprefix("tel:").strip() for h, _ in enlaces if h.lower().startswith("tel:")}
            ),
            "redes": redes,
            **metadatos(html, r.url),
            "pdf_candidatos": pdfs,
        }
        if r.meta.get("es_extra"):
            return
        for href, texto in enlaces:
            destino = r.urljoin(href)
            mismo_sitio = urlparse(destino).netloc == urlparse(r.url).netloc
            if (
                mismo_sitio
                and not destino.lower().endswith(".pdf")
                and INSTITUCIONAL.search(href + " " + texto)
                and self.extra_por_empresa.get(expediente, 0) < config.PAGINAS_EXTRA_POR_EMPRESA
            ):
                self.extra_por_empresa[expediente] = self.extra_por_empresa.get(expediente, 0) + 1
                yield r.follow(destino, meta={"es_extra": True})


async def ejecutar(anio: int, limite: int | None = None) -> pd.DataFrame:
    config.preparar(anio)
    carpeta = config.ruta_web(anio)
    carpeta.mkdir(parents=True, exist_ok=True)
    manifiesto = carpeta / "manifest.jsonl"

    urls = pd.read_csv(config.ruta_plata(anio) / "urls_piloto.csv", dtype={"expediente": int})
    capturadas = {r["expediente"] for r in leer_jsonl(manifiesto)}
    objetivo = urls[
        urls["url_verificada"].isin(("si", "manual")) & ~urls["expediente"].isin(capturadas)
    ]
    if limite:
        objetivo = objetivo.head(limite)
    if objetivo.empty:
        log.info("No hay webs pendientes de capturar")
        return pd.DataFrame(leer_jsonl(manifiesto))
    log.info("Capturando %s sitios", len(objetivo))

    paginas = 0
    with manifiesto.open("a", encoding="utf-8") as registro:
        async for item in CapturaWeb(objetivo).stream():
            html = item.pop("html")
            huella = sha256_texto(html)
            (carpeta / f"{item['expediente']}_{huella}.html").write_text(html, encoding="utf-8")
            registro.write(json.dumps({**item, "sha256": huella}, ensure_ascii=False) + "\n")
            paginas += 1
    log.info("Capturadas %s páginas de %s sitios -> %s", paginas, len(objetivo), carpeta)
    return pd.DataFrame(leer_jsonl(manifiesto))
