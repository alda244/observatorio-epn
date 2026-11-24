"""Carga en PostgreSQL. Se omite si no hay una base disponible."""

import os

import pandas as pd
import pytest
from sqlalchemy import select, text

from etl.bd import schema
from etl.pipeline import load

URL = os.getenv("ETL_BASE_DE_DATOS")


@pytest.fixture(scope="module")
def conexion():
    if not URL:
        pytest.skip("Sin ETL_BASE_DE_DATOS: no hay base de datos para la prueba")
    with load.motor(URL).begin() as conexion:
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


def test_la_migracion_publica_solo_las_vistas(conexion):
    assert conexion.scalar(text("SELECT to_regnamespace('oro') IS NULL"))
    existentes = {
        fila[0]
        for fila in conexion.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
    }
    tablas = {"empresa", "cifras_anuales", "ficha", "documento", "indicador_sector"}
    vistas = {"v_empresa", "v_cifras_anuales", "ficha_vigente", "v_documento", "v_indicador_sector"}
    assert existentes == tablas | vistas | {"alembic_version"}
    for nombre in tablas | vistas:
        lectura = conexion.scalar(
            text("SELECT has_table_privilege('rol_api', :relacion, 'SELECT')"),
            {"relacion": f"public.{nombre}"},
        )
        assert lectura == (nombre in vistas)


def test_guarda_las_filas(conexion):
    assert load.guardar(conexion, schema.empresa, empresas()) == 2
    assert conexion.execute(select(schema.empresa)).rowcount == 2


def test_repetir_la_carga_no_duplica_ni_pierde_cambios(conexion):
    load.guardar(conexion, schema.empresa, empresas())
    cambiadas = empresas()
    cambiadas.loc[0, "nombre"] = "UNA S.A. RENOMBRADA"
    load.guardar(conexion, schema.empresa, cambiadas)

    filas = conexion.execute(select(schema.empresa.c.expediente, schema.empresa.c.nombre)).all()
    assert len(filas) == 2
    assert dict(filas)[1] == "UNA S.A. RENOMBRADA"


def test_los_nulos_llegan_como_nulos(conexion):
    load.guardar(conexion, schema.empresa, empresas())
    ruc = conexion.execute(
        select(schema.empresa.c.ruc).where(schema.empresa.c.expediente == 2)
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
                "tiene_alerta": False,
                "en_universo_ese_anio": True,
            },
            {
                "expediente": 1,
                "anio": 2025,
                "ventas": 2e6,
                "empleados": 12,
                "tamano_derivado": "mediana",
                "tiene_alerta": False,
                "en_universo_ese_anio": True,
            },
        ]
    )
    load.guardar(conexion, schema.empresa, empresas())
    assert load.guardar(conexion, schema.cifras_anuales, cifras) == 2
    anios = (
        conexion.execute(
            select(schema.cifras_anuales.c.anio).where(schema.cifras_anuales.c.expediente == 1)
        )
        .scalars()
        .all()
    )
    assert sorted(anios) == [2024, 2025]
