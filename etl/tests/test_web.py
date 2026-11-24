"""Plan de captura: qué URL se pide de cada empresa."""

import pandas as pd

from etl.pipeline import web


def objetivo():
    return pd.DataFrame(
        [
            {"expediente": 1, "url_oficial": "https://una.com.ec/"},
            {"expediente": 2, "url_oficial": "https://otra.com.ec/inicio"},
        ]
    )


def test_la_portada_siempre_entra_en_el_plan():
    plan = web.armar_plan(objetivo(), [])
    portadas = plan[~plan["es_extra"]]
    assert set(portadas["url"]) == {"https://una.com.ec/", "https://otra.com.ec/inicio"}


def test_sin_sitemap_se_vuelven_a_seguir_los_enlaces_de_la_portada():
    plan = web.armar_plan(objetivo(), [])
    assert plan[~plan["es_extra"]]["seguir_enlaces"].all()
    assert plan["origen"].unique().tolist() == ["sin_exploracion"]


def test_con_sitemap_no_se_siguen_enlaces_y_se_piden_las_paginas_elegidas():
    hallazgos = [
        {
            "expediente": 1,
            "raiz": "https://una.com.ec",
            "origen": "robots.txt",
            "motivo": "sitemap",
            "candidatas": ["https://una.com.ec/nosotros", "https://una.com.ec/servicios"],
        }
    ]
    plan = web.armar_plan(objetivo(), hallazgos)
    de_una = plan[plan["expediente"] == 1]
    assert not de_una[~de_una["es_extra"]]["seguir_enlaces"].any()
    assert set(de_una[de_una["es_extra"]]["url"]) == {
        "https://una.com.ec/nosotros",
        "https://una.com.ec/servicios",
    }


def test_se_juntan_las_candidatas_de_varios_sitemap_del_mismo_sitio():
    hallazgos = [
        {
            "expediente": 1,
            "raiz": "https://una.com.ec",
            "origen": "robots.txt",
            "motivo": "sitemap",
            "candidatas": ["https://una.com.ec/nosotros"],
        },
        {
            "expediente": 1,
            "raiz": "https://una.com.ec",
            "origen": "robots.txt",
            "motivo": "sitemap",
            "candidatas": ["https://una.com.ec/contacto"],
        },
    ]
    plan = web.armar_plan(objetivo(), hallazgos)
    extras = plan[(plan["expediente"] == 1) & plan["es_extra"]]
    assert set(extras["tipo_previsto"]) == {"nosotros", "contacto"}


def test_nunca_se_piden_mas_paginas_extra_que_el_limite():
    hallazgos = [
        {
            "expediente": 1,
            "raiz": "https://una.com.ec",
            "origen": "robots.txt",
            "motivo": "sitemap",
            "candidatas": [f"https://una.com.ec/servicios/{i}" for i in range(20)],
        }
    ]
    plan = web.armar_plan(objetivo(), hallazgos)
    assert len(plan[(plan["expediente"] == 1) & plan["es_extra"]]) <= 3
