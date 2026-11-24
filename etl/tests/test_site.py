"""Lectura del sitemap y de las directivas de cada sitio (sin red)."""

import pytest

from etl import site

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://ejemplo.com/</loc></url>
  <url><loc>https://ejemplo.com/nosotros</loc></url>
  <url><loc>https://ejemplo.com/productos</loc></url>
  <url><loc>https://ejemplo.com/servicios/consultoria</loc></url>
  <url><loc>https://ejemplo.com/contacto</loc></url>
  <url><loc>https://ejemplo.com/blog/2025/una-noticia</loc></url>
  <url><loc>https://ejemplo.com/politica-de-privacidad</loc></url>
  <url><loc>https://ejemplo.com/catalogo.pdf</loc></url>
  <url><loc>https://otrositio.com/nosotros</loc></url>
</urlset>
"""

INDICE = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://ejemplo.com/sitemap-paginas.xml</loc></sitemap>
  <sitemap><loc>https://ejemplo.com/sitemap-entradas.xml</loc></sitemap>
</sitemapindex>
"""


def test_lee_las_urls_del_sitemap_sin_repetir():
    urls = site.locs_de_sitemap(SITEMAP)
    assert urls[0] == "https://ejemplo.com/"
    assert len(urls) == len(set(urls))


def test_distingue_un_indice_de_un_sitemap_de_paginas():
    assert site.es_indice_de_sitemaps(INDICE)
    assert not site.es_indice_de_sitemaps(SITEMAP)


def test_toma_el_sitemap_que_declara_robots_txt():
    robots = "User-agent: *\nDisallow: /admin\nSitemap: /sitemap_index.xml\n"
    assert site.sitemaps_en_robots(robots, "https://ejemplo.com/") == [
        "https://ejemplo.com/sitemap_index.xml"
    ]


def test_sin_declaracion_no_inventa_sitemaps():
    assert site.sitemaps_en_robots("User-agent: *\nDisallow:\n", "https://ejemplo.com/") == []


@pytest.mark.parametrize(
    ("url", "tipo"),
    [
        ("https://ejemplo.com/", "portada"),
        ("https://ejemplo.com/nosotros", "nosotros"),
        ("https://ejemplo.com/quienes-somos", "nosotros"),
        ("https://ejemplo.com/productos", "servicios"),
        ("https://ejemplo.com/contacto", "contacto"),
        ("https://ejemplo.com/algo-mas", "otra"),
    ],
)
def test_clasifica_la_pagina_por_su_ruta(url, tipo):
    assert site.tipo_pagina(url) == tipo


@pytest.mark.parametrize(
    "url",
    [
        "https://ejemplo.com/blog/2025/una-noticia",
        "https://ejemplo.com/politica-de-privacidad",
        "https://ejemplo.com/catalogo.pdf",
        "https://ejemplo.com/",
        "https://ejemplo.com/algo-mas",
    ],
)
def test_no_gasta_peticiones_en_paginas_que_no_describen_la_empresa(url):
    assert site.puntuar_pagina(url) == 0


def test_entre_dos_paginas_del_mismo_tema_gana_la_mas_cercana_a_la_raiz():
    corta = site.puntuar_pagina("https://ejemplo.com/nosotros")
    larga = site.puntuar_pagina("https://ejemplo.com/es/corporativo/nuestra-empresa/historia")
    assert corta > larga


def test_elige_una_pagina_por_tema_antes_de_repetir():
    elegidas = site.elegir_paginas(site.locs_de_sitemap(SITEMAP), 3, "ejemplo.com")
    assert [t for _, t in elegidas] == ["nosotros", "servicios", "contacto"]


def test_descarta_las_paginas_de_otro_dominio():
    elegidas = site.elegir_paginas(site.locs_de_sitemap(SITEMAP), 5, "ejemplo.com")
    assert all("otrositio.com" not in u for u, _ in elegidas)


def test_respeta_el_maximo_de_paginas():
    assert len(site.elegir_paginas(site.locs_de_sitemap(SITEMAP), 2, "ejemplo.com")) == 2


@pytest.mark.parametrize(
    ("html", "archivable"),
    [
        ('<meta name="robots" content="index, follow">', True),
        ('<meta name="robots" content="noindex, follow">', False),
        ("<meta name='robots' content='noarchive'>", False),
        ('<meta name="googlebot" content="none">', False),
        ("<html><head></head></html>", True),
    ],
)
def test_obedece_la_meta_robots_de_la_pagina(html, archivable):
    assert site.puede_archivarse(html) is archivable
