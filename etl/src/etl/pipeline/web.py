"""Paso `web`: captura de las webs oficiales verificadas (capa crudo).

El paso tiene dos fases, y la primera es la que cambia el resultado:

1. **Explorar.** Se le pregunta al sitio qué páginas tiene: primero su
   `robots.txt`, que suele declarar el `Sitemap:`, y luego el sitemap. De ahí
   se eligen las páginas institucionales que de verdad existen.
2. **Capturar.** Se pide la portada y las páginas elegidas. Si el sitio no
   tiene sitemap, y solo entonces, se cae al método anterior: seguir los
   enlaces de la portada que parezcan institucionales.

Adivinar URL gastaba peticiones en páginas que no existen; el sitemap es la
recomendación de la guía de crawlers éticos de AWS y da mejor material con
menos tráfico.

El HTML se guarda sin modificar en `crudo/web/AAAA/`: la extracción es del
paso `ficha`, así que mejorar el extractor no obliga a volver a visitar nada.

Reglas que no se negocian: se respeta `robots.txt` y la etiqueta
`<meta name="robots">` de cada página, el bot se identifica con contacto, no
se suplanta un navegador, una sola petición por dominio a la vez con pausa
adaptativa, y si el sitio responde 429 o 503 se deja de insistir.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from urllib.parse import urljoin, urlparse

import extruct
import pandas as pd
from scrapling.spiders import Request

from etl import config, site
from etl.common import leer_jsonl, log, sha256_bytes
from etl.crawling import SIN_ENTRADA, Etico

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
PAGINAS_EXTRA_POR_EMPRESA = 3

MAXIMO_CANDIDATAS = 200

tipo_pagina = site.tipo_pagina


def raiz_de(url: str) -> str:
    partes = urlparse(url)
    return f"{partes.scheme or 'https'}://{partes.netloc}"


class ExploradorDeSitio(Etico):
    """Fase 1: `robots.txt` y sitemap de cada sitio, sin capturar nada."""

    name = "explorador_de_sitio"

    def __init__(self, objetivo: pd.DataFrame):
        self.objetivo = objetivo
        super().__init__()

    async def start_requests(self):
        for e in self.objetivo.itertuples():
            raiz = raiz_de(e.url_oficial)
            yield Request(
                urljoin(raiz, "/robots.txt"),
                sid="etico",
                dont_filter=True,
                meta={"expediente": int(e.expediente), "raiz": raiz},
            )

    async def parse(self, r):
        """Primera parada: el `robots.txt`, que suele declarar el sitemap."""
        raiz = r.meta["raiz"]
        texto = self.texto_de(r) if r.status == 200 else ""
        declarados = site.sitemaps_en_robots(texto, raiz)
        origen = "robots.txt" if declarados else "convencion"
        for direccion in declarados[:1] or [urljoin(raiz, site.SITEMAP_POR_CONVENCION)]:
            yield Request(
                direccion,
                sid="etico",
                callback=self.desde_sitemap,
                dont_filter=True,
                meta={**r.meta, "origen": origen, "nivel": 0},
            )

    async def desde_sitemap(self, r):
        nivel = r.meta["nivel"]
        if r.status != 200:
            yield self._hallazgo(r.meta, [], f"sin_sitemap_{r.status}")
            return
        xml = self.texto_de(r)
        if site.es_indice_de_sitemaps(xml):
            anidados = site.locs_de_sitemap(xml)[: site.MAXIMO_SITEMAPS_ANIDADOS]
            if nivel < site.MAXIMO_SITEMAPS_ANIDADOS and anidados:
                for direccion in anidados:
                    yield Request(
                        direccion,
                        sid="etico",
                        callback=self.desde_sitemap,
                        dont_filter=True,
                        meta={**r.meta, "nivel": nivel + 1},
                    )
                return
            yield self._hallazgo(r.meta, [], "indice_demasiado_profundo")
            return
        dominio = urlparse(r.meta["raiz"]).netloc
        candidatas = [
            u
            for u in site.locs_de_sitemap(xml)
            if site.puntuar_pagina(u) > 0
            and urlparse(u).netloc.removeprefix("www.") == dominio.removeprefix("www.")
        ]
        yield self._hallazgo(r.meta, candidatas[:MAXIMO_CANDIDATAS], "sitemap")

    @staticmethod
    def _hallazgo(meta: dict, candidatas: list[str], motivo: str) -> dict:
        return {
            "expediente": meta["expediente"],
            "raiz": meta["raiz"],
            "origen": meta.get("origen", ""),
            "motivo": motivo,
            "candidatas": candidatas,
        }


class CapturaWeb(Etico):
    """Fase 2: pide la portada y las páginas del plan, y nada más."""

    name = "captura_web"

    def __init__(self, plan: pd.DataFrame):
        self.plan = plan
        self.extra_por_empresa: dict[int, int] = {}
        self.sin_entrada: set[str] = set()
        super().__init__()

    async def start_requests(self):
        for p in self.plan.itertuples():
            yield Request(
                p.url,
                sid="etico",
                callback=self.parse,
                dont_filter=True,
                meta={
                    "expediente": int(p.expediente),
                    "es_extra": bool(p.es_extra),
                    "seguir_enlaces": bool(p.seguir_enlaces),
                },
            )

    async def parse(self, r):
        expediente = r.meta["expediente"]
        dominio = urlparse(r.url).netloc
        if r.status == SIN_ENTRADA:
            self.sin_entrada.add(dominio)
            log.warning("%s respondió 403: no se piden más páginas de ese dominio", r.url)
        if r.status != 200 or dominio in self.sin_entrada:
            yield {
                "expediente": expediente,
                "url": r.url,
                "tipo_pagina": tipo_pagina(r.url),
                "status": r.status,
                "fecha_captura": dt.datetime.now().isoformat(timespec="seconds"),
                "cuerpo": b"",
                "encoding": "",
                "omitida": "estado_http",
            }
            return

        cuerpo = r.body
        codificacion = r.encoding or "utf-8"
        html = cuerpo.decode(codificacion, errors="replace")
        if not site.puede_archivarse(html):
            log.info("%s pide no ser archivada (meta robots): no se guarda", r.url)
            yield {
                "expediente": expediente,
                "url": r.url,
                "tipo_pagina": tipo_pagina(r.url),
                "status": r.status,
                "fecha_captura": dt.datetime.now().isoformat(timespec="seconds"),
                "cuerpo": b"",
                "encoding": "",
                "omitida": "meta_robots",
            }
            return

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
            "cuerpo": cuerpo,
            "encoding": codificacion,
            "omitida": "",
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

        # Solo se siguen enlaces cuando el sitio no tiene sitemap utilizable.
        if r.meta.get("es_extra") or not r.meta.get("seguir_enlaces"):
            return
        for href, texto in enlaces:
            destino = r.urljoin(href)
            if urlparse(destino).netloc != dominio or destino.lower().endswith(".pdf"):
                continue
            if not INSTITUCIONAL.search(href + " " + texto):
                continue
            if self.extra_por_empresa.get(expediente, 0) >= PAGINAS_EXTRA_POR_EMPRESA:
                break
            self.extra_por_empresa[expediente] = self.extra_por_empresa.get(expediente, 0) + 1
            yield r.follow(destino, meta={**r.meta, "es_extra": True})


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


def armar_plan(objetivo: pd.DataFrame, hallazgos: list[dict]) -> pd.DataFrame:
    """Qué URL se va a pedir de cada empresa: portada más páginas elegidas.

    Las candidatas de todos los sitemap de un mismo sitio se juntan antes de
    elegir, para que un sitio partido en varios sitemap no quede peor servido.
    """
    por_empresa: dict[int, list[str]] = {}
    origen: dict[int, str] = {}
    for h in hallazgos:
        por_empresa.setdefault(h["expediente"], []).extend(h["candidatas"])
        if h["candidatas"] or h["expediente"] not in origen:
            origen[h["expediente"]] = h["motivo"]

    filas = []
    for e in objetivo.itertuples():
        expediente = int(e.expediente)
        raiz = raiz_de(e.url_oficial)
        elegidas = site.elegir_paginas(
            por_empresa.get(expediente, []),
            PAGINAS_EXTRA_POR_EMPRESA,
            urlparse(raiz).netloc,
        )
        filas.append(
            {
                "expediente": expediente,
                "url": e.url_oficial,
                "tipo_previsto": "portada",
                "es_extra": False,
                # Sin páginas del sitemap se vuelve a seguir enlaces de la portada.
                "seguir_enlaces": not elegidas,
                "origen": origen.get(expediente, "sin_exploracion"),
            }
        )
        filas += [
            {
                "expediente": expediente,
                "url": url,
                "tipo_previsto": tema,
                "es_extra": True,
                "seguir_enlaces": False,
                "origen": origen.get(expediente, ""),
            }
            for url, tema in elegidas
        ]
    return pd.DataFrame(filas)


async def ejecutar(anio: int, limite: int | None = None) -> pd.DataFrame:
    config.preparar(anio)
    carpeta = config.ruta_web(anio)
    carpeta.mkdir(parents=True, exist_ok=True)
    manifiesto = carpeta / "manifest.jsonl"

    urls = pd.read_csv(config.ruta_plata(anio) / "urls_piloto.csv", dtype={"expediente": int})
    capturadas = {r["expediente"] for r in leer_jsonl(manifiesto)}
    objetivo = urls[
        urls["url_verificada"].isin(("si", "manual"))
        & urls["url_oficial"].notna()
        & ~urls["expediente"].isin(capturadas)
    ]
    if limite:
        objetivo = objetivo.head(limite)
    if objetivo.empty:
        log.info("No hay webs pendientes de capturar")
        return pd.DataFrame(leer_jsonl(manifiesto))

    log.info("Fase 1 de 2: explorando el sitemap de %s sitios", len(objetivo))
    hallazgos = [h async for h in ExploradorDeSitio(objetivo).stream()]
    plan = armar_plan(objetivo, hallazgos)
    plan.to_csv(config.ruta_plata(anio) / "plan_captura.csv", index=False)
    con_sitemap = int((plan["origen"] == "sitemap").sum())
    log.info(
        "Plan: %s páginas de %s sitios (%s desde sitemap) -> plan_captura.csv",
        len(plan),
        plan["expediente"].nunique(),
        con_sitemap,
    )

    log.info("Fase 2 de 2: capturando")
    guardadas, omitidas = 0, 0
    with manifiesto.open("a", encoding="utf-8") as registro:
        async for item in CapturaWeb(plan).stream():
            cuerpo = item.pop("cuerpo")
            if not cuerpo:
                omitidas += 1
                registro.write(json.dumps({**item, "sha256": ""}, ensure_ascii=False) + "\n")
                continue
            # Se guarda el cuerpo tal como llegó: el hash es de esos bytes.
            huella = sha256_bytes(cuerpo)
            (carpeta / f"{item['expediente']}_{huella}.html").write_bytes(cuerpo)
            registro.write(json.dumps({**item, "sha256": huella}, ensure_ascii=False) + "\n")
            guardadas += 1
    log.info("Capturadas %s páginas, omitidas %s -> %s", guardadas, omitidas, carpeta)
    return pd.DataFrame(leer_jsonl(manifiesto))
