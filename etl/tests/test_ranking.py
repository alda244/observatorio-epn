"""Reglas de limpieza y calidad del ranking."""

import pandas as pd
import pytest

from etl.pipeline import ranking


@pytest.fixture
def crudo() -> pd.DataFrame:
    filas = [
        # posicion, anio, pos_ant, anio_ant, expediente, nombre, tipo, actividad, ...
        (
            1,
            2025,
            1,
            2024,
            10,
            "GRANDE S.A.",
            "ANÓNIMA",
            "J6201.01 - PROGRAMACIÓN.",
            "SIERRA",
            "PICHINCHA",
            "QUITO",
            None,
            "SOCIETARIO",
            100,
            1e7,
            5e6,
            2e7,
            1e6,
            1e6,
            1e6,
            1e5,
            2e7,
        ),
        (
            2,
            2025,
            0,
            0,
            11,
            "MEDIANA CIA. LTDA.",
            "RESPONSABILIDAD LIMITADA",
            "G4711.01 - VENTA AL POR MENOR.",
            "COSTA",
            "GUAYAS",
            "GUAYAQUIL",
            None,
            "SOCIETARIO",
            40,
            2e6,
            1e6,
            3e6,
            1e5,
            1e5,
            1e5,
            1e4,
            3e6,
        ),
        (
            3,
            2025,
            3,
            2024,
            12,
            "PEQUEÑA S.A.S.",
            "SOCIEDAD POR ACCIONES SIMPLIFICADA",
            "C1010.11 - MATADEROS.",
            "SIERRA",
            "AZUAY",
            "CUENCA",
            None,
            "SOCIETARIO",
            5,
            1e5,
            -5e4,
            5e5,
            -1e4,
            -1e4,
            -1e4,
            0,
            5e5,
        ),
        # Grande que declara 2 empleados: el caso que motivó la alerta.
        (
            4,
            2025,
            4,
            2024,
            13,
            "POCOS EMPLEADOS S.A.",
            "ANÓNIMA",
            "G4711.01 - VENTA AL POR MENOR.",
            "COSTA",
            "GUAYAS",
            "GUAYAQUIL",
            None,
            "SOCIETARIO",
            2,
            1e8,
            5e7,
            9e8,
            1e7,
            1e7,
            1e7,
            1e6,
            9e8,
        ),
    ]
    df = pd.DataFrame(filas, columns=ranking.COLUMNAS_CRUDAS)
    return pd.concat([df, df.iloc[[0]]], ignore_index=True)  # una fila idéntica repetida


def preparar(crudo: pd.DataFrame) -> pd.DataFrame:
    df = ranking.separar_ciiu(crudo.copy())
    df, identicas, conflicto = ranking.quitar_duplicados(df)
    df = ranking.marcar_calidad(df)
    df = ranking.derivar_tamano(df)
    return ranking.alertar_empleados(df)


def test_quita_filas_identicas(crudo):
    _, identicas, conflicto = ranking.quitar_duplicados(ranking.separar_ciiu(crudo.copy()))
    assert identicas == 1
    assert conflicto == []


def test_separa_el_ciiu_en_codigo_y_descripcion(crudo):
    df = ranking.separar_ciiu(crudo.copy())
    assert df.loc[0, "ciiu"] == "J6201.01"
    assert df.loc[0, "seccion_ciiu"] == "J"
    assert df.loc[0, "division_ciiu"] == "J62"
    assert "actividad" not in df.columns


@pytest.mark.parametrize(
    ("ventas", "esperado"),
    [
        (0, "micro_pequena"),
        (1_000_000, "micro_pequena"),
        (1_000_001, "mediana"),
        (5_000_000, "mediana"),
        (5_000_001, "grande"),
    ],
)
def test_tamano_se_deriva_de_las_ventas(ventas, esperado):
    df = pd.DataFrame({"ventas": [float(ventas)]})
    assert ranking.derivar_tamano(df).loc[0, "tamano_derivado"] == esperado


def test_marca_la_empresa_grande_con_pocos_empleados(crudo):
    df = preparar(crudo).set_index("expediente")
    assert df.loc[13, "alerta_empleados"] == "grande_menos_10"
    assert df.loc[10, "alerta_empleados"] == ""


def test_conserva_el_patrimonio_negativo_como_dato_valido(crudo):
    df = preparar(crudo).set_index("expediente")
    assert df.loc[12, "patrimonio_negativo"]
    assert df.loc[12, "tamano_derivado"] == "micro_pequena"


def test_el_esquema_rechaza_ventas_mayores_que_el_ingreso():
    df = preparar(
        pd.DataFrame(
            [
                (
                    1,
                    2025,
                    1,
                    2024,
                    10,
                    "X S.A.",
                    "ANÓNIMA",
                    "J6201.01 - PROGRAMACIÓN.",
                    "SIERRA",
                    "PICHINCHA",
                    "QUITO",
                    None,
                    "SOCIETARIO",
                    10,
                    1e6,
                    1e5,
                    9e6,
                    1e5,
                    1e5,
                    1e5,
                    1e4,
                    1e6,
                )
            ],
            columns=ranking.COLUMNAS_CRUDAS,
        )
    )
    df["ruc"] = None
    with pytest.raises(Exception, match="ventas"):
        ranking.ESQUEMA.validate(df, lazy=True)
