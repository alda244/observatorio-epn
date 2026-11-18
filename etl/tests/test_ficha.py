"""Extracción del Company Profile y reglas de datos personales."""

import pandas as pd
import pytest

from etl.pasos import ficha


def test_quita_correos_y_telefonos_del_texto():
    limpio = ficha.limpiar("Escríbanos a juan.perez@empresa.com o al 0991234567 hoy")
    assert "@" not in limpio and "0991234567" not in limpio


def test_descarta_los_parrafos_con_cargos_directivos():
    texto = (
        "El gerente general dirige la empresa desde 2010 y la ha llevado al liderazgo del sector.\n"
        "Fabricamos envases de vidrio para la industria de alimentos desde hace cuarenta años."
    )
    parrafos = ficha.parrafos_utiles(texto)
    assert len(parrafos) == 1
    assert parrafos[0].startswith("Fabricamos")


def test_descarta_los_parrafos_demasiado_cortos():
    assert ficha.parrafos_utiles("Inicio\nContacto\n") == []


def test_recorta_en_el_fin_de_oracion():
    texto = "Somos una empresa de software. Trabajamos en todo el país desde hace veinte años."
    assert ficha.recortar(texto, 40) == "Somos una empresa de software."


def test_recorta_sin_cortar_una_palabra():
    assert ficha.recortar("palabras " * 30, 50).endswith("…")


def test_no_recorta_lo_que_ya_cabe():
    assert ficha.recortar("Corto", 150) == "Corto"


@pytest.mark.parametrize(
    ("titulo", "es_producto"),
    [
        ("Asesoría Técnica Personalizada", True),
        ("Transferencia de Tecnología", True),
        ("Nuestros Servicios", False),
        ("Misión", False),
        ("Contacto", False),
        ("Política de privacidad", False),
    ],
)
def test_distingue_un_producto_de_un_titulo_de_seccion(titulo, es_producto):
    descartado = bool(ficha.SECCIONES.search(titulo) or ficha.RUIDO.search(titulo))
    assert descartado != es_producto


@pytest.mark.parametrize(
    ("correo", "corporativo"),
    [
        ("info@empresa.com", True),
        ("ventas@empresa.com", True),
        ("juan.perez@empresa.com", False),
        ("maria@empresa.com", False),
    ],
)
def test_solo_guarda_correos_corporativos(correo, corporativo):
    assert bool(ficha.CORREO_CORPORATIVO.match(correo)) == corporativo


def test_el_tagline_sale_de_la_descripcion_declarada_por_la_pagina():
    empresa = pd.DataFrame(
        [
            {
                "tipo_pagina": "portada",
                "url": "https://empresa.com/",
                "jsonld_organizacion": {"description": "Fabricamos envases de vidrio en Ecuador."},
                "og_description": None,
                "meta_description": None,
            }
        ]
    )
    texto, fuente = ficha.tagline(empresa)
    assert texto == "Fabricamos envases de vidrio en Ecuador."
    assert fuente == "https://empresa.com/"


def test_sin_descripcion_declarada_no_inventa_tagline():
    empresa = pd.DataFrame(
        [
            {
                "tipo_pagina": "portada",
                "url": "https://empresa.com/",
                "jsonld_organizacion": None,
                "og_description": None,
                "meta_description": None,
            }
        ]
    )
    assert ficha.tagline(empresa) == ("", "")


def test_una_celda_vacia_no_rompe_la_identificacion():
    """`NaN or []` devuelve NaN y `list(NaN)` falla: el caso real del manifiesto."""
    assert ficha.lista(float("nan")) == []
    assert ficha.lista(None) == []
    assert ficha.lista(["a", "b"]) == ["a", "b"]
    assert ficha.lista("https://ejemplo.com") == ["https://ejemplo.com"]


def test_la_identificacion_tolera_paginas_sin_datos_de_contacto():
    paginas = pd.DataFrame(
        [
            {
                "expediente": 1,
                "url": "https://ejemplo.com/",
                "correos": ["info@ejemplo.com", "juan.perez@ejemplo.com"],
                "telefonos": float("nan"),
                "redes": float("nan"),
                "jsonld_organizacion": float("nan"),
                "og_image": None,
            }
        ]
    )
    datos = ficha.identificacion(paginas)
    assert datos["correo_corporativo"] == "info@ejemplo.com"
    assert datos["telefono"] is None
    assert datos["redes"] is None


def test_la_pagina_se_lee_identica_a_como_se_capturo(tmp_path):
    """Leer en modo texto traduce CRLF a LF y el hash deja de verificar."""
    from etl.comun import sha256_bytes

    original = "<html>\r\n<body>Hola</body>\r\n</html>"
    cuerpo = original.encode("utf-8")
    huella = sha256_bytes(cuerpo)
    (tmp_path / f"1_{huella}.html").write_bytes(cuerpo)

    pagina = pd.Series({"expediente": 1, "sha256": huella, "encoding": "utf-8"})
    assert ficha.html_de(tmp_path, pagina) == original
    assert sha256_bytes((tmp_path / f"1_{huella}.html").read_bytes()) == huella


def test_la_pagina_se_decodifica_con_la_codificacion_registrada(tmp_path):
    from etl.comun import sha256_bytes

    cuerpo = "<html>Año Ñandú</html>".encode("latin-1")
    huella = sha256_bytes(cuerpo)
    (tmp_path / f"2_{huella}.html").write_bytes(cuerpo)

    pagina = pd.Series({"expediente": 2, "sha256": huella, "encoding": "latin-1"})
    assert "Año Ñandú" in ficha.html_de(tmp_path, pagina)
