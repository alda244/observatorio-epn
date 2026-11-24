"""Consolidación de los años en las tablas que publicará la API."""

import pandas as pd
import pytest

from etl import config
from etl.pipeline import consolidate


def fila_ranking(expediente: int, anio: int, nombre: str, ventas: float) -> dict:
    return {
        "expediente": expediente,
        "anio": anio,
        "nombre": nombre,
        "ruc": "1790000000001",
        "ciiu": "J6201.01",
        "ciiu_descripcion": "Programacion informatica",
        "seccion_ciiu": "J",
        "division_ciiu": "J62",
        "tipo_compania": "ANONIMA",
        "region": "SIERRA",
        "provincia": "PICHINCHA",
        "ciudad": "QUITO",
        "empleados": 10,
        "activo": 1e6,
        "patrimonio": 5e5,
        "ventas": ventas,
        "utilidad_neta": 1e5,
        "ingreso_total": ventas,
        "tamano_derivado": "grande",
        "alerta_empleados": "",
        "nueva_en_ranking": False,
        "ingreso_total_no_reportado": False,
        "utilidad_no_reportada": False,
    }


@pytest.fixture
def datos(tmp_path, monkeypatch):
    """Dos años de capa plata y oro: la empresa 1 cambia de nombre en 2013."""
    monkeypatch.setattr(config, "DATOS", tmp_path)
    monkeypatch.setattr(config, "PLATA", tmp_path / "plata")
    monkeypatch.setattr(config, "ORO", tmp_path / "oro")
    monkeypatch.setattr(config, "CRUDO", tmp_path / "crudo")

    poblacion = {
        2012: [
            fila_ranking(1, 2012, "UNA S.A.", 9e6),
            fila_ranking(2, 2012, "DOS S.A.", 8e6),
            fila_ranking(3, 2012, "FUERA DEL UNIVERSO S.A.", 1e5),
        ],
        2013: [
            fila_ranking(1, 2013, "UNA S.A. RENOMBRADA", 1e7),
            fila_ranking(2, 2013, "DOS S.A.", 7e6),
        ],
    }
    en_universo = {2012: [1, 2], 2013: [1]}
    for anio, filas in poblacion.items():
        config.preparar(anio)
        df = pd.DataFrame(filas)
        df.to_parquet(config.ruta_plata(anio) / "ranking.parquet", index=False)
        universo = df[df["expediente"].isin(en_universo[anio])].assign(grupo="TEC", rank_grupo=1)
        universo.to_parquet(config.ruta_oro(anio) / "universo.parquet", index=False)
        piloto = universo.head(1).assign(
            criterio_piloto="tecnologica_mediana_grande", en_top50_tec=True
        )
        piloto.to_csv(config.ruta_oro(anio) / "piloto.csv", index=False)
    return tmp_path


def test_solo_entran_los_anios_comparables(datos, monkeypatch):
    config.preparar(2010)
    pd.DataFrame([fila_ranking(9, 2010, "VIEJA S.A.", 9e6)]).assign(grupo="TEC").to_parquet(
        config.ruta_oro(2010) / "universo.parquet", index=False
    )
    assert consolidate.anios_disponibles() == [2012, 2013]
    assert consolidate.anios_disponibles(2010) == [2010, 2012, 2013]


def test_el_universo_es_el_del_anio_de_referencia(datos):
    """docs/universo.md: «El universo se fija con el ranking 2025»."""
    empresa = consolidate.tabla_empresa(2013)
    assert empresa["expediente"].is_unique
    # La empresa 2 estuvo en el universo 2012 pero no en el de referencia:
    # no entra, y recalcular por año y unir daría un universo distinto.
    assert set(empresa["expediente"]) == {1}


def test_la_identificacion_es_la_del_anio_de_referencia(datos):
    empresa = consolidate.tabla_empresa(2013).set_index("expediente")
    assert empresa.loc[1, "nombre"] == "UNA S.A. RENOMBRADA"
    assert empresa.loc[1, "anio_identificacion"] == 2013
    anterior = consolidate.tabla_empresa(2012).set_index("expediente")
    assert anterior.loc[1, "nombre"] == "UNA S.A."


def test_la_serie_trae_los_anios_en_que_la_empresa_existio(datos):
    cifras = consolidate.tabla_cifras({1, 2}, [2012, 2013])
    assert not cifras.duplicated(["expediente", "anio"]).any()
    assert sorted(cifras[cifras["expediente"] == 1]["anio"]) == [2012, 2013]
    # La 2 no estuvo en el universo 2013, pero sus cifras de ese año sí sirven.
    assert sorted(cifras[cifras["expediente"] == 2]["anio"]) == [2012, 2013]


def test_no_entran_empresas_fuera_del_universo(datos):
    cifras = consolidate.tabla_cifras({1, 2}, [2012, 2013])
    assert 3 not in set(cifras["expediente"])


def test_empresa_trae_lo_estatico_del_piloto(datos):
    """en_piloto, criterio_piloto y en_top50_tec viven en empresa, no en una
    tabla separada por año: son del universo fijado, no cambian por año."""
    empresa = consolidate.tabla_empresa(2013).set_index("expediente")
    assert bool(empresa.loc[1, "en_piloto"])
    assert empresa.loc[1, "criterio_piloto"] == "tecnologica_mediana_grande"
    assert bool(empresa.loc[1, "en_top50_tec"])


def test_cifras_distingue_aparecer_de_cumplir_la_delimitacion(datos):
    """en_universo_ese_anio vive en cifras_anuales, por (expediente, año)."""
    cifras = consolidate.tabla_cifras({1, 2}, [2012, 2013]).set_index(["expediente", "anio"])
    assert bool(cifras.loc[(1, 2012), "en_universo_ese_anio"])
    assert bool(cifras.loc[(1, 2013), "en_universo_ese_anio"])
    # La empresa 2 aparece en 2013 (tiene cifras) pero no cumplía la
    # delimitación ese año (no estaba en universo.parquet de 2013).
    assert not bool(cifras.loc[(2, 2013), "en_universo_ese_anio"])


def test_el_consolidado_no_deja_filas_huerfanas(datos):
    resumen = consolidate.ejecutar(anio_universo=2013)
    empresa = pd.read_parquet(config.ORO / "empresa.parquet")
    cifras = pd.read_parquet(config.ORO / "cifras_anuales.parquet")
    assert resumen["empresa"] == len(empresa) == 1
    assert cifras["expediente"].isin(empresa["expediente"]).all()
    assert not (config.ORO / "universo_por_anio.parquet").exists()


def test_sin_capa_oro_el_paso_avisa_en_vez_de_escribir_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ORO", tmp_path / "oro")
    (tmp_path / "oro").mkdir()
    with pytest.raises(FileNotFoundError, match="capa oro"):
        consolidate.ejecutar()


def test_sin_el_universo_del_anio_de_referencia_no_consolida(datos):
    with pytest.raises(FileNotFoundError, match="universo 2020"):
        consolidate.ejecutar(anio_universo=2020)


def test_la_columna_anio_es_el_ejercicio_del_archivo_no_el_de_la_fila(datos):
    """Caso real: PayJoy y Refricor tienen "Año" (posición del ranking) en 0
    aunque reportaron el ejercicio completo. Esa columna cruda no debe llegar
    como el año en cifras_anuales."""
    config.preparar(2012)
    sin_posicion = pd.DataFrame(
        [fila_ranking(99, 0, "SIN POSICION S.A.", 5e5)]  # anio crudo = 0
    )
    plata_2012 = pd.read_parquet(config.ruta_plata(2012) / "ranking.parquet")
    pd.concat([plata_2012, sin_posicion], ignore_index=True).to_parquet(
        config.ruta_plata(2012) / "ranking.parquet", index=False
    )

    cifras = consolidate.tabla_cifras({99}, [2012])
    assert cifras["anio"].tolist() == [2012]
    assert 0 not in set(cifras["anio"])
