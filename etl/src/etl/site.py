"""Lectura del mapa de un sitio y de sus directivas, sin tocar la red.

Antes de capturar, conviene preguntarle al sitio qué páginas tiene en vez de
adivinar URL. La guía de crawlers éticos de AWS lo pone así: «usa el sitemap,
que lo desarrolla el dueño del sitio, para centrarte en las páginas
importantes». Eso baja el número de peticiones y mejora lo que se obtiene.

Todo lo de este módulo son funciones puras sobre texto: reciben el XML o el
HTML ya descargado y devuelven datos. La red la maneja `pipeline/web.py`, y así
estas reglas se pueden probar sin salir a internet.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

# Qué busca el Bloque 2 del Company Profile, con su peso.
TEMAS: dict[str, tuple[str, int]] = {
    "nosotros": (
        r"nosotros|quienes|qui[eé]nes|about|about-us|empresa|historia|mision|misi[oó]n",
        10,
    ),
    "servicios": (r"servicio|producto|soluci|catalogo|cat[aá]logo|portafolio|portfolio", 8),
    "contacto": (r"contacto|contact|ubicacion|ubicaci[oó]n|sucursal", 6),
    "sostenibilidad": (r"sostenibilidad|responsabilidad|rse|memoria|informe-anual", 4),
}
# Secciones que no describen a la empresa: no vale gastar una petición en ellas.
RUIDO = re.compile(
    r"/blog|/noticia|/news|/prensa|/evento|/vacante|/empleo|/trabaja|/carrera"
    r"|/tag/|/categor|/author|/wp-|/feed|/cart|/carrito|/checkout|/login|/cuenta"
    r"|/politica|/privacidad|/terminos|/cookies|/mapa-del-sitio|/sitemap"
    r"|\.(pdf|jpg|jpeg|png|gif|svg|webp|zip|xml|css|js)$",
    re.I,
)
SITEMAP_POR_CONVENCION = "/sitemap.xml"
MAXIMO_SITEMAPS_ANIDADOS = 2


def sitemaps_en_robots(texto: str, base: str) -> list[str]:
    """URL de los sitemap que declara el propio `robots.txt`."""
    encontrados = [
        urljoin(base, m.group(1).strip())
        for m in re.finditer(r"(?im)^\s*sitemap\s*:\s*(\S+)\s*$", texto or "")
    ]
    return list(dict.fromkeys(encontrados))


def es_indice_de_sitemaps(xml: str) -> bool:
    """Un índice no lista páginas: lista otros sitemap."""
    return "<sitemapindex" in (xml or "").lower()


def locs_de_sitemap(xml: str) -> list[str]:
    """Las URL que lista un sitemap, en el orden en que aparecen."""
    crudas = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml or "", re.I)
    return list(dict.fromkeys(u.strip() for u in crudas))


def tipo_pagina(url: str) -> str:
    """Para qué sirve una página, según su ruta."""
    ruta = urlparse(url).path.lower()
    if ruta in ("", "/", "/index.html", "/home"):
        return "portada"
    for tema, (patron, _) in TEMAS.items():
        if re.search(patron, ruta):
            return tema
    return "otra"


def _profundidad(url: str) -> int:
    return len([p for p in urlparse(url).path.split("/") if p])


def puntuar_pagina(url: str) -> int:
    """Cuánto aporta una página a la ficha. Cero significa no visitarla."""
    partes = urlparse(url)
    if RUIDO.search(partes.path + ("?" + partes.query if partes.query else "")):
        return 0
    tipo = tipo_pagina(url)
    if tipo == "portada":
        return 0  # la portada se pide siempre, aparte
    if tipo == "otra":
        return 0
    base = TEMAS[tipo][1]
    # Entre dos páginas del mismo tema gana la más cercana a la raíz:
    # /nosotros antes que /es/corporativo/nuestra-empresa/historia/2019.
    return max(1, base * 10 - _profundidad(url) - len(url) // 50)


def elegir_paginas(
    urls: list[str], maximo: int, dominio: str | None = None
) -> list[tuple[str, str]]:
    """Las páginas institucionales que vale la pena pedir, sin repetir tema.

    Primero una de cada tema, de mayor a menor peso; si sobran turnos, se
    rellena con las mejores que queden. Así una empresa no gasta sus tres
    peticiones en tres páginas de productos.
    """
    candidatas = []
    for u in dict.fromkeys(urls):
        if dominio and urlparse(u).netloc.removeprefix("www.") != dominio.removeprefix("www."):
            continue
        puntaje = puntuar_pagina(u)
        if puntaje > 0:
            candidatas.append((puntaje, tipo_pagina(u), u))
    candidatas.sort(key=lambda c: (-c[0], len(c[2])))

    elegidas: list[tuple[str, str]] = []
    temas_usados: set[str] = set()
    for _, tema, u in candidatas:
        if len(elegidas) >= maximo:
            break
        if tema not in temas_usados:
            temas_usados.add(tema)
            elegidas.append((u, tema))
    for _, tema, u in candidatas:
        if len(elegidas) >= maximo:
            break
        if u not in [e[0] for e in elegidas]:
            elegidas.append((u, tema))
    return elegidas


def directivas_robots(html: str) -> set[str]:
    """Directivas de la etiqueta `<meta name="robots">` de la página.

    AWS recomienda revisar las `meta` del HTML por directivas de rastreo: una
    página puede pedir que no se indexe o que no se archive aunque robots.txt
    permita leerla.
    """
    etiquetas = re.findall(
        r"""<meta[^>]+name\s*=\s*["']?(?:robots|googlebot)["']?[^>]*>""", html or "", re.I
    )
    directivas: set[str] = set()
    for etiqueta in etiquetas:
        contenido = re.search(r"""content\s*=\s*["']([^"']*)["']""", etiqueta, re.I)
        if contenido:
            directivas |= {d.strip().lower() for d in contenido.group(1).split(",") if d.strip()}
    return directivas


def puede_archivarse(html: str) -> bool:
    """Si la página pide que no se archive, no se guarda su HTML."""
    return not (directivas_robots(html) & {"noindex", "noarchive", "none"})
