"""Extracción del Company Profile y reglas de datos personales."""

import pandas as pd
import pytest

from etl.pipeline import profile


def test_quita_correos_y_telefonos_del_texto():
    limpio = profile.limpiar("Escríbanos a juan.perez@empresa.com o al 0991234567 hoy")
    assert "@" not in limpio and "0991234567" not in limpio


def test_descarta_los_parrafos_con_cargos_directivos():
    texto = (
        "El gerente general dirige la empresa desde 2010 y la ha llevado al liderazgo del sector.\n"
        "Fabricamos envases de vidrio para la industria de alimentos desde hace cuarenta años."
    )
    parrafos = profile.parrafos_utiles(texto)
    assert len(parrafos) == 1
    assert parrafos[0].startswith("Fabricamos")


def test_descarta_los_parrafos_demasiado_cortos():
    assert profile.parrafos_utiles("Inicio\nContacto\n") == []


def test_recorta_en_el_fin_de_oracion():
    texto = "Somos una empresa de software. Trabajamos en todo el país desde hace veinte años."
    assert profile.recortar(texto, 40) == "Somos una empresa de software."


def test_recorta_sin_cortar_una_palabra():
    assert profile.recortar("palabras " * 30, 50).endswith("…")


def test_no_recorta_lo_que_ya_cabe():
    assert profile.recortar("Corto", 150) == "Corto"


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
    descartado = bool(profile.SECCIONES.search(titulo) or profile.RUIDO.search(titulo))
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
    assert bool(profile.CORREO_CORPORATIVO.match(correo)) == corporativo


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
    texto, fuente = profile.tagline(empresa)
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
    assert profile.tagline(empresa) == ("", "")


def test_una_celda_vacia_no_rompe_la_identificacion():
    """`NaN or []` devuelve NaN y `list(NaN)` falla: el caso real del manifiesto."""
    assert profile.lista(float("nan")) == []
    assert profile.lista(None) == []
    assert profile.lista(["a", "b"]) == ["a", "b"]
    assert profile.lista("https://ejemplo.com") == ["https://ejemplo.com"]


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
    datos = profile.identificacion(paginas)
    assert datos["correo_corporativo"] == "info@ejemplo.com"
    assert datos["telefono"] is None
    assert datos["redes"] is None


def test_la_pagina_se_lee_identica_a_como_se_capturo(tmp_path):
    """Leer en modo texto traduce CRLF a LF y el hash deja de verificar."""
    from etl.common import sha256_bytes

    original = "<html>\r\n<body>Hola</body>\r\n</html>"
    cuerpo = original.encode("utf-8")
    huella = sha256_bytes(cuerpo)
    (tmp_path / f"1_{huella}.html").write_bytes(cuerpo)

    pagina = pd.Series({"expediente": 1, "sha256": huella, "encoding": "utf-8"})
    assert profile.html_de(tmp_path, pagina) == original
    assert sha256_bytes((tmp_path / f"1_{huella}.html").read_bytes()) == huella


def test_la_pagina_se_decodifica_con_la_codificacion_registrada(tmp_path):
    from etl.common import sha256_bytes

    cuerpo = "<html>Año Ñandú</html>".encode("latin-1")
    huella = sha256_bytes(cuerpo)
    (tmp_path / f"2_{huella}.html").write_bytes(cuerpo)

    pagina = pd.Series({"expediente": 2, "sha256": huella, "encoding": "latin-1"})
    assert "Año Ñandú" in profile.html_de(tmp_path, pagina)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Llámenos al 02 234 5678", ["02 234 5678"]),
        ("Celular 0991234567", ["0991234567"]),
        ("Tel: +593 2 392 2000", ["+593 2 392 2000"]),
        ("Contacto 1800 567567", ["1800 567567"]),
        ("Marque 1800 FARMACIA", ["1800 FARMACIA"]),
        # Números reales que entraban mal: no son del Ecuador.
        ("Oficina en Miami: 877.579.4929", []),
        ("Oficina Napoli +390816123099", []),
        ("Oficina Panamá +5073803626", []),
        # Ni los que no son teléfonos.
        ("Factura 620660 del 7201800", []),
    ],
)
def test_solo_toma_telefonos_ecuatorianos(texto, esperado):
    assert profile.telefonos_de(texto) == esperado


def test_no_publica_el_telefono_de_una_persona():
    """LOPDP: el teléfono junto a un cargo es dato personal."""
    assert profile.telefonos_de("El gerente general Juan Pérez, 0991234567") == []
    assert profile.telefonos_de("Central telefónica 0991234567") == ["0991234567"]


def test_no_guarda_mas_telefonos_que_el_maximo():
    texto = " ".join(f"02 234 56{n:02d}" for n in range(10))
    assert len(profile.telefonos_de(texto)) == profile.MAXIMO_TELEFONOS


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Escríbanos a info@empresa.com", ["info@empresa.com"]),
        ("ventas@empresa.com y VENTAS@EMPRESA.COM", ["ventas@empresa.com"]),
        ("Contacte a juan.perez@empresa.com", []),
        ("gerente@empresa.com", []),
    ],
)
def test_solo_toma_buzones_institucionales(texto, esperado):
    assert profile.correos_de(texto) == esperado


def test_lee_la_direccion_de_la_etiqueta_address():
    html = "<html><body><address>Av. Amazonas N37-29 y Villalengua, Quito</address></body></html>"
    assert profile.direccion_de(html) == "Av. Amazonas N37-29 y Villalengua, Quito"


def test_no_confunde_cualquier_texto_con_una_direccion():
    html = "<html><body><address>Síganos en redes sociales</address></body></html>"
    assert profile.direccion_de(html) == ""


def test_no_confunde_una_palabra_que_empieza_igual_con_una_direccion():
    html = "<html><body><address>Avance de obra en el sector norte</address></body></html>"
    # «sector» sí es palabra de dirección, así que este caso debe reconocerla.
    assert profile.direccion_de(html) == "Avance de obra en el sector norte"
    html = "<html><body><address>Suscríbase a nuestro boletín mensual</address></body></html>"
    assert profile.direccion_de(html) == ""
