"""Las reglas de recolección no se cambian sin darse cuenta.

No son una recomendación del README: son la condición bajo la que el proyecto
visita webs ajenas. Esta prueba falla si alguien las afloja.
"""

from etl import config
from etl.pasos import urls, web
from etl.recoleccion import BLOQUEO, SIN_ENTRADA, Etico

RECOLECTORES = [web.ExploradorDeSitio, web.CapturaWeb, urls.VerificadorPortada]


def test_los_dos_pasos_que_salen_a_internet_heredan_las_mismas_reglas():
    for recolector in RECOLECTORES:
        assert issubclass(recolector, Etico), recolector.__name__


def test_se_respeta_robots_txt():
    assert Etico.robots_txt_obey is True


def test_no_se_insiste_cuando_el_sitio_bloquea():
    assert Etico.max_blocked_retries == 0
    assert 429 in BLOQUEO and 503 in BLOQUEO
    assert SIN_ENTRADA == 403


def test_una_sola_peticion_por_dominio_a_la_vez():
    assert config.PETICIONES_SIMULTANEAS_POR_DOMINIO == 1
    assert Etico.concurrent_requests_per_domain == 1


def test_la_pausa_es_adaptativa_y_no_baja_del_minimo():
    assert Etico.autothrottle_enabled is True
    assert Etico.download_delay >= 3.0
    assert Etico.autothrottle_start_delay == config.SEGUNDOS_ENTRE_PETICIONES
    assert Etico.autothrottle_max_delay >= Etico.autothrottle_start_delay


def test_el_bot_se_identifica_con_contacto_y_en_ascii():
    assert "ObservatorioEPN-Bot" in config.USER_AGENT
    assert "https://github.com/" in config.USER_AGENT
    # Una cabecera HTTP no admite caracteres fuera de ASCII: con una tilde,
    # la petición de robots.txt falla y Scrapling asume que todo está vedado.
    assert config.USER_AGENT.isascii()
