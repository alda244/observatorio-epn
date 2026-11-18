"""Consolidación de los años en las tablas que publicará la API."""

import pandas as pd
import pytest

from etl import config
from etl.pasos import consolidar


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
    assert consolidar.anios_disponibles() == [2012, 2013]
    assert consolidar.anios_disponibles(2010) == [2010, 2012, 2013]


def test_una_sola_fila_por_empresa(datos):
    empresa = consolidar.tabla_empresa([2012, 2013])
    assert empresa["expediente"].is_unique
    assert set(empresa["expediente"]) == {1, 2}


def test_la_identificacion_sale_del_anio_mas_reciente(datos):
    empresa = consolidar.tabla_empresa([2012, 2013]).set_index("expediente")
    assert empresa.loc[1, "nombre"] == "UNA S.A. RENOMBRADA"
    assert empresa.loc[1, "anio_identificacion"] == 2013
    # La empresa 2 salió del universo en 2013: su identificación es la de 2012.
    assert empresa.loc[2, "anio_identificacion"] == 2012


def test_la_serie_trae_los_anios_en_que_la_empresa_existio(datos):
    cifras = consolidar.tabla_cifras({1, 2}, [2012, 2013])
    assert not cifras.duplicated(["expediente", "anio"]).any()
    assert sorted(cifras[cifras["expediente"] == 1]["anio"]) == [2012, 2013]
    # La 2 no estuvo en el universo 2013, pero sus cifras de ese año sí sirven.
    assert sorted(cifras[cifras["expediente"] == 2]["anio"]) == [2012, 2013]


def test_no_entran_empresas_fuera_del_universo(datos):
    cifras = consolidar.tabla_cifras({1, 2}, [2012, 2013])
    assert 3 not in set(cifras["expediente"])


def test_la_presencia_dice_en_que_anio_y_quien_tiene_ficha(datos):
    presencia = consolidar.tabla_presencia([2012, 2013])
    assert len(presencia) == 3  # 1 y 2 en 2012; solo 1 en 2013
    assert set(presencia[presencia["en_piloto"]]["expediente"]) == {1}


def test_el_consolidado_no_deja_filas_huerfanas(datos):
    resumen = consolidar.ejecutar()
    empresa = pd.read_parquet(config.ORO / "empresa.parquet")
    cifras = pd.read_parquet(config.ORO / "cifras_anuales.parquet")
    presencia = pd.read_parquet(config.ORO / "universo_por_anio.parquet")
    assert resumen["empresa"] == len(empresa) == 2
    assert cifras["expediente"].isin(empresa["expediente"]).all()
    assert presencia["expediente"].isin(empresa["expediente"]).all()


def test_sin_capa_oro_el_paso_avisa_en_vez_de_escribir_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ORO", tmp_path / "oro")
    (tmp_path / "oro").mkdir()
    with pytest.raises(FileNotFoundError, match="capa oro"):
        consolidar.ejecutar()
