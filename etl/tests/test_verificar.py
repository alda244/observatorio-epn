"""Verificación de punta a punta: debe encontrar lo que está mal."""

import json

import pandas as pd
import pytest

from etl import config
from etl.comun import sha256_archivo, sha256_bytes
from etl.pasos import verificar


def fila(expediente: int, ventas: float = 9e6, **extra) -> dict:
    base = {
        "expediente": expediente,
        "anio": 2025,
        "nombre": f"EMPRESA {expediente} S.A.",
        "ciiu": "J6201.01",
        "seccion_ciiu": "J",
        "division_ciiu": "J62",
        "grupo": "TEC",
        "empleados": 10,
        "activo": 1e6,
        "ventas": ventas,
        "ingreso_total": ventas,
        "tamano_derivado": "grande",
        "anio_cero": False,
    }
    return base | extra


@pytest.fixture
def arbol(tmp_path, monkeypatch):
    """Un año completo y correcto en disco."""
    monkeypatch.setattr(config, "DATOS", tmp_path)
    monkeypatch.setattr(config, "CRUDO", tmp_path / "crudo")
    monkeypatch.setattr(config, "PLATA", tmp_path / "plata")
    monkeypatch.setattr(config, "ORO", tmp_path / "oro")
    monkeypatch.setattr(config, "WEB", tmp_path / "crudo" / "web")
    config.preparar(2025)
    config.ruta_crudo(2025).mkdir(parents=True, exist_ok=True)

    descarga = config.ruta_crudo(2025) / "ranking_2025.xlsx"
    descarga.write_bytes(b"contenido de la descarga oficial")
    pd.DataFrame(
        [
            {
                "archivo": "2025/ranking_2025.xlsx",
                "url_origen": "https://appscvsmovil.supercias.gob.ec/ranking/ranking_2025.xlsx",
                "sha256": sha256_archivo(descarga),
            }
        ]
    ).to_csv(config.CRUDO / "MANIFEST.csv", index=False)

    plata = pd.DataFrame([fila(1), fila(2), fila(3, ventas=5e5)])
    plata.to_parquet(config.ruta_plata(2025) / "ranking.parquet", index=False)
    (config.ruta_plata(2025) / "calidad_ranking.json").write_text(
        json.dumps(
            {
                "filas_crudo": 5,
                "filas_identicas_quitadas": 1,
                "expedientes_con_conflicto": [],
                "filas_descartadas": 1,
                "filas_plata": 3,
            }
        )
    )
    universo = plata[plata["ventas"] > 1e6]
    universo.to_parquet(config.ruta_oro(2025) / "universo.parquet", index=False)
    universo.assign(criterio_piloto="tecnologica_mediana_grande", en_top50_tec=True).to_csv(
        config.ruta_oro(2025) / "piloto.csv", index=False
    )
    return tmp_path


def estados(informe) -> dict:
    return informe.tabla()["estado"].value_counts().to_dict()


def test_un_arbol_correcto_no_tiene_fallas(arbol):
    informe = verificar.ejecutar(2025)
    assert informe.fallas == [], [vars(f) for f in informe.fallas]


def test_detecta_un_expediente_repetido_en_plata(arbol):
    plata = pd.read_parquet(config.ruta_plata(2025) / "ranking.parquet")
    pd.concat([plata, plata.head(1)]).to_parquet(
        config.ruta_plata(2025) / "ranking.parquet", index=False
    )
    informe = verificar.ejecutar(2025)
    assert any("único" in f.comprobacion for f in informe.fallas)


def test_detecta_que_las_filas_no_cuadran_con_el_crudo(arbol):
    ruta = config.ruta_plata(2025) / "calidad_ranking.json"
    calidad = json.loads(ruta.read_text()) | {"filas_crudo": 99}
    ruta.write_text(json.dumps(calidad))
    informe = verificar.ejecutar(2025)
    assert any("cuadran" in f.comprobacion for f in informe.fallas)


def test_detecta_una_empresa_del_universo_que_no_esta_en_plata(arbol):
    universo = pd.read_parquet(config.ruta_oro(2025) / "universo.parquet")
    intrusa = pd.DataFrame([fila(999)])
    pd.concat([universo, intrusa]).to_parquet(
        config.ruta_oro(2025) / "universo.parquet", index=False
    )
    informe = verificar.ejecutar(2025)
    assert any("sale de la capa plata" in f.comprobacion for f in informe.fallas)


def test_detecta_una_fila_con_anio_cero_en_el_universo(arbol):
    plata = pd.read_parquet(config.ruta_plata(2025) / "ranking.parquet")
    plata.loc[plata["expediente"] == 1, "anio_cero"] = True
    plata.to_parquet(config.ruta_plata(2025) / "ranking.parquet", index=False)
    informe = verificar.ejecutar(2025)
    assert any("año en cero" in f.comprobacion for f in informe.fallas)


def test_detecta_ventas_mayores_que_el_ingreso_reportado(arbol):
    plata = pd.read_parquet(config.ruta_plata(2025) / "ranking.parquet")
    plata.loc[plata["expediente"] == 1, "ingreso_total"] = 1.0
    plata.to_parquet(config.ruta_plata(2025) / "ranking.parquet", index=False)
    informe = verificar.ejecutar(2025)
    assert any("no superan el ingreso" in f.comprobacion for f in informe.fallas)


def test_detecta_un_archivo_crudo_que_cambio(arbol):
    archivo = config.ruta_crudo(2025) / "ranking_2025.xlsx"
    archivo.write_bytes(b"alguien lo edito")
    informe = verificar.ejecutar(2025)
    assert any("hash" in f.comprobacion for f in informe.fallas)


def test_detecta_una_pagina_del_manifiesto_que_no_esta_en_disco(arbol):
    carpeta = config.ruta_web(2025)
    carpeta.mkdir(parents=True, exist_ok=True)
    cuerpo = b"<html>hola</html>"
    huella = sha256_bytes(cuerpo)
    (carpeta / "manifest.jsonl").write_text(
        json.dumps({"expediente": 1, "sha256": huella, "status": 200}) + "\n"
    )
    informe = verificar.ejecutar(2025)
    assert any("está en disco" in f.comprobacion for f in informe.fallas)

    (carpeta / f"1_{huella}.html").write_bytes(cuerpo)
    assert verificar.ejecutar(2025).fallas == []


def test_avisa_cuando_el_anio_no_tiene_cobertura_de_ventas(arbol):
    plata = pd.read_parquet(config.ruta_plata(2025) / "ranking.parquet")
    plata["ventas"] = 0.0
    plata["ingreso_total"] = 0.0
    plata.to_parquet(config.ruta_plata(2025) / "ranking.parquet", index=False)
    informe = verificar.ejecutar(2025)
    assert any("cobertura de ventas" in a.comprobacion for a in informe.avisos)


def test_sin_capa_plata_avisa_en_vez_de_decir_que_todo_esta_bien(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PLATA", tmp_path / "plata")
    with pytest.raises(FileNotFoundError, match="capa plata"):
        verificar.ejecutar()
