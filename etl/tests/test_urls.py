"""Descubrimiento y verificación de la web oficial."""

import pandas as pd
import pytest

from etl.comun import partes_nombre, tokens_distintivos
from etl.pasos import urls


@pytest.mark.parametrize(
    ("razon_social", "base", "comercial"),
    [
        (
            "CONSORCIO ECUATORIANO DE TELECOMUNICACIONES S.A. CONECEL",
            "CONSORCIO ECUATORIANO DE TELECOMUNICACIONES",
            "CONECEL",
        ),
        (
            "PROCESADORA NACIONAL DE ALIMENTOS C.A. PRONACA",
            "PROCESADORA NACIONAL DE ALIMENTOS",
            "PRONACA",
        ),
        ("OTECEL S.A.", "OTECEL", ""),
    ],
)
def test_separa_la_razon_social_del_nombre_comercial(razon_social, base, comercial):
    assert partes_nombre(razon_social) == (base, comercial)


def test_descarta_las_palabras_que_no_identifican():
    tokens = tokens_distintivos("CORPORACION NACIONAL DE TELECOMUNICACIONES S.A.")
    assert "CORPORACION" not in tokens and "NACIONAL" not in tokens
    assert "TELECOMUNICACIONES" in tokens


def test_propone_el_nombre_comercial_primero():
    candidatos = urls.candidatos_de("PROCESADORA NACIONAL DE ALIMENTOS C.A. PRONACA")
    assert candidatos[0].startswith("pronaca")
    assert "pronaca.com" in candidatos


def test_no_propone_dominios_genericos():
    candidatos = urls.candidatos_de("SOCIEDAD NACIONAL DE GALAPAGOS CA")
    assert not any(c.startswith("sociedad.") for c in candidatos)


def visita(texto="", title="", dominio="ejemplo.com"):
    return {"texto": texto, "title": title, "og_site_name": "", "dominio": dominio}


def empresa(nombre="FERTISA AGIF C.L.", ruc="0990000000001"):
    return pd.Series({"nombre": nombre, "ruc": ruc})


def test_el_ruc_en_la_pagina_es_prueba_suficiente():
    resultado = urls.puntuar(visita(texto="RUC 0990000000001"), empresa())
    assert resultado["puntaje"] == 100
    assert resultado["evidencia"] == "ruc"
    assert "ruc" in resultado["senales"]


def test_anota_las_senales_para_la_revision_a_mano():
    resultado = urls.puntuar(
        visita(
            texto="Somos la mejor empresa del Ecuador", title="Fertisa", dominio="fertisa.com.ec"
        ),
        empresa(ruc=""),
    )
    assert "menciona_ecuador" in resultado["senales"]
    assert "tld_ec" in resultado["senales"]
    assert "nombre_en_titulo" in resultado["senales"]
    assert resultado["titulo"] == "Fertisa"


def test_el_nombre_comercial_en_el_titulo_verifica():
    resultado = urls.puntuar(
        visita(title="CONECEL | Inicio"),
        empresa("CONSORCIO ECUATORIANO DE TELECOMUNICACIONES S.A. CONECEL", ruc=""),
    )
    assert resultado["evidencia"] == "nombre_comercial"
    assert resultado["puntaje"] == 100


def test_el_dominio_que_coincide_con_el_nombre_no_alcanza_por_si_solo():
    resultado = urls.puntuar(visita(dominio="fertisa.com"), empresa(ruc=""))
    assert resultado["evidencia"] == "dominio_coincide_con_nombre"
    assert urls.clasificar(resultado["puntaje"]) == "revisar"


@pytest.mark.parametrize(
    ("puntaje", "estado"),
    [(100, "si"), (85, "si"), (70, "revisar"), (59, "no_encontrada"), (None, "no_encontrada")],
)
def test_clasificacion_por_puntaje(puntaje, estado):
    assert urls.clasificar(puntaje) == estado


@pytest.mark.parametrize(
    ("entrada", "salida"),
    [
        ("https://www.directvla.com:443/ec", "https://www.directvla.com/ec"),
        ("http://ejemplo.com:80", "http://ejemplo.com/"),
        ("https://Ejemplo.COM.EC", "https://ejemplo.com.ec/"),
        ("https://ejemplo.com/#inicio", "https://ejemplo.com/"),
        ("https://ejemplo.com/es/?lang=es", "https://ejemplo.com/es/?lang=es"),
    ],
)
def test_normaliza_la_direccion_verificada(entrada, salida):
    assert urls.normalizar_url(entrada) == salida
