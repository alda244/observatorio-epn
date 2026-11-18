"""Carga en PostgreSQL. Se omite si no hay una base disponible."""

import os

import pandas as pd
import pytest
from sqlalchemy import select, text

from etl.bd import esquema
from etl.pasos import carga

URL = os.getenv("ETL_BASE_DE_DATOS")


@pytest.fixture(scope="module")
def conexion():
    if not URL:
        pytest.skip("Sin ETL_BASE_DE_DATOS: no hay base de datos para la prueba")
    motor = carga.motor(URL)
    try:
        with motor.connect() as prueba:
            prueba.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001 - la causa exacta no cambia la decisión
        pytest.skip(f"Base de datos no disponible: {e}")
    with motor.begin() as conexion:
        carga.crear_esquema(conexion)
        for tabla in (esquema.cifras_anuales, esquema.empresa):
            conexion.execute(tabla.delete())
        yield conexion
        conexion.rollback()


def empresas() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "expediente": 1,
                "ruc": "1790000000001",
                "nombre": "UNA S.A.",
                "ciiu": "J6201.01",
                "seccion_ciiu": "J",
                "division_ciiu": "J62",
                "grupo": "TEC",
                "provincia": "PICHINCHA",
                "es_holding": False,
            },
            {
                "expediente": 2,
                "ruc": None,
                "nombre": "OTRA S.A.",
                "ciiu": "G4711.01",
                "seccion_ciiu": "G",
                "division_ciiu": "G47",
                "grupo": "G",
                "provincia": "GUAYAS",
                "es_holding": False,
            },
        ]
    )


def test_crea_los_esquemas_y_las_tablas(conexion):
    existentes = {
        fila[0]
        for fila in conexion.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'oro'")
        )
    }
    assert {"empresa", "cifras_anuales", "universo", "ficha", "documento"} <= existentes


def test_guarda_las_filas(conexion):
    assert carga.guardar(conexion, esquema.empresa, empresas()) == 2
    assert conexion.execute(select(esquema.empresa)).rowcount == 2


def test_repetir_la_carga_no_duplica_ni_pierde_cambios(conexion):
    carga.guardar(conexion, esquema.empresa, empresas())
    cambiadas = empresas()
    cambiadas.loc[0, "nombre"] = "UNA S.A. RENOMBRADA"
    carga.guardar(conexion, esquema.empresa, cambiadas)

    filas = conexion.execute(select(esquema.empresa.c.expediente, esquema.empresa.c.nombre)).all()
    assert len(filas) == 2
    assert dict(filas)[1] == "UNA S.A. RENOMBRADA"


def test_los_nulos_llegan_como_nulos(conexion):
    carga.guardar(conexion, esquema.empresa, empresas())
    ruc = conexion.execute(
        select(esquema.empresa.c.ruc).where(esquema.empresa.c.expediente == 2)
    ).scalar()
    assert ruc is None


def test_una_empresa_puede_tener_varios_anios(conexion):
    cifras = pd.DataFrame(
        [
            {
                "expediente": 1,
                "anio": 2024,
                "ventas": 1e6,
                "empleados": 10,
                "tamano_derivado": "mediana",
                "alerta_empleados": "",
            },
            {
                "expediente": 1,
                "anio": 2025,
                "ventas": 2e6,
                "empleados": 12,
                "tamano_derivado": "mediana",
                "alerta_empleados": "",
            },
        ]
    )
    carga.guardar(conexion, esquema.empresa, empresas())
    assert carga.guardar(conexion, esquema.cifras_anuales, cifras) == 2
    anios = (
        conexion.execute(
            select(esquema.cifras_anuales.c.anio).where(esquema.cifras_anuales.c.expediente == 1)
        )
        .scalars()
        .all()
    )
    assert sorted(anios) == [2024, 2025]
