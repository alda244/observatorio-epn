"""Paso `ranking`: del ranking SCVS crudo a la capa plata.

Limpia, normaliza y valida el ranking empresarial de un año. No borra nada en
silencio: cada decisión queda como columna de marca o en el reporte de calidad.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandera.pandas as pa

from etl import config
from etl.comun import guardar_json, log, sha256_archivo

COLUMNAS_CRUDAS = [
    "posicion",
    "anio",
    "posicion_anterior",
    "anio_anterior",
    "expediente",
    "nombre",
    "tipo_compania",
    "actividad",
    "region",
    "provincia",
    "ciudad",
    "tamano_scvs",
    "sector_scvs",
    "empleados",
    "activo",
    "patrimonio",
    "ventas",
    "utilidad_antes_impuesto",
    "utilidad_ejercicio",
    "utilidad_neta",
    "ir_causado",
    "ingreso_total",
]
TEXTO = ["nombre", "tipo_compania", "actividad", "region", "provincia", "ciudad", "sector_scvs"]
CIFRAS = ["empleados", "activo", "patrimonio", "ventas", "utilidad_neta", "ingreso_total"]

ESQUEMA = pa.DataFrameSchema(
    {
        "expediente": pa.Column(int, pa.Check.gt(0), unique=True),
        "anio": pa.Column(int),
        "nombre": pa.Column(str, pa.Check.str_length(min_value=1)),
        "ciiu": pa.Column(str, pa.Check.str_matches(r"^[A-U]\d{4}")),
        "seccion_ciiu": pa.Column(str, pa.Check.isin(list("ABCDEFGHIJKLMNOPQRSTU"))),
        "region": pa.Column(str, pa.Check.isin(["COSTA", "SIERRA", "ORIENTE", "GALAPAGOS"])),
        "provincia": pa.Column(str, nullable=False),
        "empleados": pa.Column(int, pa.Check.ge(0)),
        "activo": pa.Column(float, pa.Check.ge(0)),
        "ventas": pa.Column(float, pa.Check.ge(0)),
        "ingreso_total": pa.Column(float, pa.Check.ge(0)),
        "tamano_derivado": pa.Column(str, pa.Check.isin(["micro_pequena", "mediana", "grande"])),
        "ruc": pa.Column(str, pa.Check.str_matches(r"^\d{13}$"), nullable=True),
    },
    checks=pa.Check(
        lambda t: t["ingreso_total"] + 1 >= t["ventas"], error="ventas mayores que el ingreso total"
    ),
    strict=False,
)


def leer_crudo(anio: int) -> tuple[pd.DataFrame, str]:
    """Lee el ranking del año. El encabezado ocupa dos filas: título y nombres."""
    archivo = config.ruta_crudo(anio) / f"ranking_{anio}.xlsx"
    if not archivo.exists():
        raise FileNotFoundError(
            f"Falta {archivo}. Descárguelo de "
            "https://appscvsmovil.supercias.gob.ec/ranking/reporte.html\n"
            "y regístrelo en MANIFEST.csv"
        )
    titulo = str(pd.read_excel(archivo, engine="calamine", header=None, nrows=1).iloc[0, 0])
    df = pd.read_excel(archivo, engine="calamine", header=1)
    df.columns = COLUMNAS_CRUDAS
    return df, titulo.replace("Fecha de corte - ", "").strip()


def separar_ciiu(df: pd.DataFrame) -> pd.DataFrame:
    partes = df["actividad"].str.split(" - ", n=1)
    df["ciiu"] = partes.str[0].str.strip()
    df["ciiu_descripcion"] = partes.str[1].str.strip()
    df["seccion_ciiu"] = df["ciiu"].str[0]
    df["division_ciiu"] = df["ciiu"].str[:3]
    return df.drop(columns=["actividad", "tamano_scvs"])  # tamano_scvs viene vacía


def quitar_duplicados(df: pd.DataFrame) -> tuple[pd.DataFrame, int, list[int]]:
    """Quita filas idénticas y, si un expediente se repite con filas distintas,
    conserva la de mejor posición y registra cuáles fueron."""
    identicas = int(df.duplicated().sum())
    df = df.drop_duplicates()
    conflicto = sorted(
        df.loc[df["expediente"].duplicated(keep=False), "expediente"].unique().tolist()
    )
    df = df.sort_values(["expediente", "posicion"]).drop_duplicates("expediente", keep="first")
    return df, identicas, conflicto


def marcar_calidad(df: pd.DataFrame) -> pd.DataFrame:
    df["anio_cero"] = df["anio"] == 0
    df["nueva_en_ranking"] = df["anio_anterior"] == 0
    df["sin_ventas"] = df["ventas"] == 0
    df["sin_actividad"] = (df["ventas"] == 0) & (df["activo"] == 0) & (df["ingreso_total"] == 0)
    df["patrimonio_negativo"] = df["patrimonio"] < 0
    df["revisar_utilidad"] = (df["utilidad_neta"] > df["ingreso_total"]) & (df["utilidad_neta"] > 0)
    return df


def derivar_tamano(df: pd.DataFrame) -> pd.DataFrame:
    df["tamano_derivado"] = np.select(
        [df["ventas"] > config.UMBRAL_GRANDE, df["ventas"] > config.UMBRAL_MEDIANA],
        ["grande", "mediana"],
        default="micro_pequena",
    )
    return df


def alertar_empleados(df: pd.DataFrame) -> pd.DataFrame:
    """Marca el dato de empleados cuando no es creíble, indicando la causa.

    El valor no se corrige: no hay fuente para el número real. El caso que
    originó la regla es Tiendas Tuti (8 empleados y más de USD 1.000 millones).
    """
    df["ventas_por_empleado"] = df["ventas"] / df["empleados"].replace(0, np.nan)
    mediana = (
        df[df["empleados"] >= config.EMPLEADOS_MINIMO_GRANDE]
        .groupby("division_ciiu")["ventas_por_empleado"]
        .median()
    )
    df["veces_mediana_division"] = df["ventas_por_empleado"] / df["division_ciiu"].map(mediana)
    df["alerta_empleados"] = np.select(
        [
            df["empleados"] > config.EMPLEADOS_IMPOSIBLE,
            (df["tamano_derivado"] == "grande")
            & (df["empleados"] < config.EMPLEADOS_MINIMO_GRANDE),
            df["veces_mediana_division"] > config.VECES_MEDIANA_DIVISION,
        ],
        ["imposible", "grande_menos_10", "fuera_de_rango_division"],
        default="",
    )
    return df


def agregar_ruc(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Cruza con el directorio de compañías para traer el RUC.

    El directorio trae RUC con espacios, letras o puntos: solo se acepta el de
    13 dígitos y el resto queda marcado.
    """
    archivos = sorted(config.CRUDO.glob("*/bi_compania*.csv"), reverse=True)
    if not archivos:
        log.warning("Sin directorio de compañías: las filas quedan sin RUC")
        return df.assign(ruc_original=pd.NA, ruc_valido=False, ruc=pd.NA)
    directorio = pd.read_csv(archivos[0], usecols=["expediente", "ruc"], dtype={"ruc": str})
    directorio = directorio.drop_duplicates("expediente").rename(columns={"ruc": "ruc_original"})
    df = df.merge(directorio, on="expediente", how="left")
    limpio = df["ruc_original"].str.strip()
    df["ruc_valido"] = limpio.str.fullmatch(r"\d{13}").fillna(False).astype(bool)
    df["ruc"] = limpio.where(df["ruc_valido"])
    return df


def ejecutar(anio: int) -> pd.DataFrame:
    config.preparar(anio)
    crudo, fecha_corte = leer_crudo(anio)
    filas_crudo = len(crudo)
    log.info("Ranking %s: %s filas crudas, corte %s", anio, f"{filas_crudo:,}", fecha_corte)

    df = crudo.copy()
    for columna in TEXTO:
        df[columna] = df[columna].str.strip().str.replace(r"\s+", " ", regex=True)
    df = separar_ciiu(df)
    df, identicas, conflicto = quitar_duplicados(df)
    df = marcar_calidad(df)
    df = derivar_tamano(df)
    df = alertar_empleados(df)
    df = agregar_ruc(df, anio)

    plata = ESQUEMA.validate(df, lazy=True).sort_values("posicion").reset_index(drop=True)
    destino = config.ruta_plata(anio) / "ranking.parquet"
    plata.to_parquet(destino, index=False)

    marcas = [
        "anio_cero",
        "nueva_en_ranking",
        "sin_ventas",
        "sin_actividad",
        "patrimonio_negativo",
        "revisar_utilidad",
    ]
    guardar_json(
        config.ruta_plata(anio) / "calidad_ranking.json",
        {
            "anio": anio,
            "fuente": f"crudo/{anio}/ranking_{anio}.xlsx",
            "sha256_fuente": sha256_archivo(config.ruta_crudo(anio) / f"ranking_{anio}.xlsx"),
            "fecha_corte": fecha_corte,
            "filas_crudo": filas_crudo,
            "filas_identicas_quitadas": identicas,
            "expedientes_con_conflicto": conflicto,
            "filas_plata": len(plata),
            "marcas": {m: int(plata[m].sum()) for m in marcas},
            "tamano_derivado": plata["tamano_derivado"].value_counts().to_dict(),
            "alerta_empleados": plata["alerta_empleados"]
            .replace("", "sin_alerta")
            .value_counts()
            .to_dict(),
            "sin_ruc_en_directorio": int(plata["ruc_original"].isna().sum()),
            "ruc_formato_invalido": int(
                (plata["ruc_original"].notna() & ~plata["ruc_valido"]).sum()
            ),
            "reglas": {
                "umbral_mediana_usd": config.UMBRAL_MEDIANA,
                "umbral_grande_usd": config.UMBRAL_GRANDE,
                "veces_mediana_division": config.VECES_MEDIANA_DIVISION,
            },
        },
    )
    log.info("Plata %s: %s empresas -> %s", anio, f"{len(plata):,}", destino)
    return plata
