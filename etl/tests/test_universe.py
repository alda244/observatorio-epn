"""Delimitación del universo y del piloto (docs/universo.md)."""

import pandas as pd
import pytest

from etl.pipeline import universe


@pytest.mark.parametrize(
    ("ciiu", "grupo"),
    [
        ("J6110.01", "TEC"),
        ("J6201.01", "TEC"),
        ("J6311.01", "TEC"),
        ("J5820.01", "TEC"),
        ("J5811.01", None),  # edición de libros no es núcleo tecnológico
        ("G4711.01", "G"),
        ("C1010.11", "C"),
        ("M7010.01", "M"),
        ("K6420.01", "K"),
        ("A0126.01", None),
        ("H4921.01", None),
    ],
)
def test_grupo_segun_el_ciiu(ciiu, grupo):
    assert universe.grupo_de(ciiu) == grupo


@pytest.fixture
def plata() -> pd.DataFrame:
    filas = [
        (10, "TEC MICRO S.A.", "J6201.01", "micro_pequena", 5e5, False),
        (11, "TEC GRANDE S.A.", "J6201.01", "grande", 9e6, False),
        (12, "COMERCIO MICRO S.A.", "G4711.01", "micro_pequena", 5e5, False),
        (13, "COMERCIO GRANDE S.A.", "G4711.01", "grande", 8e6, False),
        (14, "AGRO GRANDE S.A.", "A0126.01", "grande", 9e9, False),
        (15, "CARTERA HOLDING S.A.", "K6420.01", "grande", 7e6, False),
        (16, "SEGUROS K S.A.", "K6512.01", "grande", 6e6, False),
        # Sin posición de ranking asignada, pero con cifras: debe entrar
        # igual (docs/universo.md incluye estos casos; el real es PayJoy).
        (17, "SIN POSICION S.A.", "J6201.01", "grande", 9e6, True),
    ]
    df = pd.DataFrame(
        filas,
        columns=[
            "expediente",
            "nombre",
            "ciiu",
            "tamano_derivado",
            "ventas",
            "sin_posicion_ranking",
        ],
    )
    return universe.marcar(df)


def test_entran_todas_las_tecnologicas_y_solo_medianas_y_grandes_del_resto(plata):
    seleccion = universe.seleccionar(plata)
    assert set(seleccion["expediente"]) == {10, 11, 13, 15, 16, 17}


def test_no_excluye_por_sin_posicion_de_ranking(plata):
    """ "Posición"/"Año" en 0 es sobre el ranking, no sobre el ejercicio
    fiscal: 29 de 30 casos reales en 2025 tienen cifras completas."""
    assert 17 in set(universe.seleccionar(plata)["expediente"])


def test_los_holdings_quedan_en_el_universo_pero_fuera_del_top_50(plata):
    seleccion = universe.seleccionar(plata)
    assert 15 in set(seleccion["expediente"])
    tops = universe.listas_top(seleccion)
    assert 15 not in set(tops["K"]["expediente"])
    assert 16 in set(tops["K"]["expediente"])


def test_el_piloto_solo_trae_tecnologicas_medianas_y_grandes(plata):
    seleccion = universe.seleccionar(plata)
    piloto = universe.armar_piloto(seleccion, universe.listas_top(seleccion))
    tecnologicas = piloto[piloto["criterio_piloto"] == "tecnologica_mediana_grande"]
    assert set(tecnologicas["expediente"]) == {11, 17}
