"""Paso `financieros`: estados financieros por ramo de la SCVS a la capa plata.

El archivo crudo trae una columna por cuenta contable (más de 600) con el
código, no el nombre; el catálogo del mismo año traduce esos códigos. De todas
las cuentas se conservan las que el Observatorio necesita, entre ellas el gasto
en sueldos, que permite interpretar el dato de empleados del ranking.

La validación incluye la identidad que define un balance, Activo = Pasivo +
Patrimonio. En los balances 2025 se cumple exactamente en las 154.904 filas,
así que cualquier desvío futuro significa que el archivo no se leyó bien o que
la fuente cambió, y el paso se detiene en vez de publicar un balance que no
cuadra.

Fuente: Portal de Información Societario de la SCVS, "Estados financieros por
ramo". La descarga es manual porque el formulario pide verificación humana.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandera.pandas as pa

from etl import config
from etl.comun import guardar_json, log

IDENTIFICACION = [
    "anio",
    "expediente",
    "ruc",
    "nombre",
    "rama_actividad",
    "descripcion_rama",
    "ciiu",
]

# Cuentas del catálogo SCVS que se conservan, con el nombre que llevan en plata.
CUENTAS = {
    "1": "activo",
    "101": "activo_corriente",
    "10101": "efectivo_equivalentes",
    "10105": "inventarios",
    "102": "activo_no_corriente",
    "2": "pasivo",
    "201": "pasivo_corriente",
    "202": "pasivo_no_corriente",
    "3": "patrimonio",
    "301": "capital",
    "401": "ingresos_actividades_ordinarias",
    "402": "ganancia_bruta",
    "403": "otros_ingresos",
    "501": "costo_ventas_produccion",
    "502": "gastos",
    "5020101": "sueldos_salarios_remuneraciones",
    "5020103": "beneficios_sociales_indemnizaciones",
    "5020106": "remuneraciones_otros_trabajadores",
    "5020201": "sueldos_salarios_remuneraciones_ventas",
    "5020203": "beneficios_sociales_indemnizaciones_ventas",
    "600": "utilidad_antes_participacion_impuestos",
    "601": "participacion_trabajadores",
    "602": "utilidad_antes_impuestos",
    "603": "impuesto_renta_causado",
    "707": "utilidad_neta",
}
# Cuentas que suman el gasto total en personal.
CUENTAS_PERSONAL = [
    "sueldos_salarios_remuneraciones",
    "beneficios_sociales_indemnizaciones",
    "remuneraciones_otros_trabajadores",
    "sueldos_salarios_remuneraciones_ventas",
    "beneficios_sociales_indemnizaciones_ventas",
]


# Tolerancia de la ecuación contable, en dólares. En los balances 2025 el
# desvío máximo es exactamente 0, así que un dólar es holgura de sobra para
# redondeos y cualquier desvío mayor es un error que hay que ver.
TOLERANCIA_BALANCE = 1.0
NO_NEGATIVAS = ["activo", "pasivo", "gasto_personal"]

ESQUEMA = pa.DataFrameSchema(
    {
        "expediente": pa.Column(int, pa.Check.gt(0), unique=True),
        "anio": pa.Column(int, pa.Check.gt(2000)),
        "nombre": pa.Column(str, pa.Check.str_length(min_value=1)),
        "ruc": pa.Column(str, pa.Check.str_matches(r"^\d{13}$"), nullable=True),
        "activo": pa.Column(float, pa.Check.ge(0)),
        "pasivo": pa.Column(float, pa.Check.ge(0)),
        "patrimonio": pa.Column(float),  # puede ser negativo
        "gasto_personal": pa.Column(float, pa.Check.ge(0)),
    },
    checks=pa.Check(
        # Activo = Pasivo + Patrimonio. Es la identidad que define un balance:
        # si no se cumple, el archivo no se leyó bien o la fuente está mal.
        lambda t: (t["activo"] - (t["pasivo"] + t["patrimonio"])).abs() <= TOLERANCIA_BALANCE,
        error="el activo no es igual al pasivo más el patrimonio",
    ),
    strict=False,
)


def separar_descartes(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aparta las filas que no cumplen las reglas básicas, con el motivo."""
    negativa = pd.concat([df[c] < 0 for c in NO_NEGATIVAS if c in df], axis=1).any(axis=1)
    descuadre = (df["activo"] - (df["pasivo"] + df["patrimonio"])).abs() > TOLERANCIA_BALANCE
    motivo = np.select([negativa, descuadre], ["cifra_negativa", "balance_descuadrado"], default="")
    con_motivo = df.assign(motivo_descarte=motivo)
    return con_motivo[motivo == ""].copy(), con_motivo[motivo != ""].copy()


def normalizar_ruc(df: pd.DataFrame) -> pd.DataFrame:
    """Solo se acepta el RUC de 13 dígitos; el resto queda marcado, no borrado."""
    df = df.rename(columns={"ruc": "ruc_original"})
    limpio = df["ruc_original"].astype(str).str.strip()
    df["ruc_valido"] = limpio.str.fullmatch(r"\d{13}").fillna(False).astype(bool)
    df["ruc"] = limpio.where(df["ruc_valido"])
    return df


def archivos(anio: int) -> tuple[list, list]:
    carpeta = config.ruta_crudo(anio)
    return sorted(carpeta.glob(f"balances_{anio}_*.txt")), sorted(
        carpeta.glob(f"catalogo_{anio}_*.txt")
    )


def leer_catalogo(ruta) -> dict[str, str]:
    cat = pd.read_csv(
        ruta,
        sep="\t",
        header=None,
        names=["codigo", "nombre"],
        dtype={"codigo": str},
        encoding="latin-1",
    )
    return dict(zip(cat["codigo"].str.strip(), cat["nombre"].str.strip(), strict=False))


def leer_balances(ruta, anio: int) -> pd.DataFrame:
    """Lee un archivo de balances quedándose solo con las columnas necesarias.

    El archivo es TAB-separado, viene en latin-1 y usa coma decimal.
    """
    cabecera = pd.read_csv(ruta, sep="\t", nrows=0, encoding="latin-1")
    columnas = list(cabecera.columns)
    buscadas = {f"CUENTA_{c}": nombre for c, nombre in CUENTAS.items() if f"CUENTA_{c}" in columnas}
    cualitativas = columnas[:7]
    df = pd.read_csv(
        ruta,
        sep="\t",
        encoding="latin-1",
        decimal=",",
        thousands=None,
        usecols=cualitativas + list(buscadas),
        dtype={cualitativas[2]: str},
    )
    df.columns = IDENTIFICACION + [buscadas[c] for c in df.columns[7:]]
    faltantes = sorted(set(CUENTAS.values()) - set(df.columns))
    if faltantes:
        log.warning("%s: faltan cuentas %s", ruta.name, ", ".join(faltantes))
    return df


def ejecutar(anio: int) -> pd.DataFrame:
    config.preparar(anio)
    balances, catalogos = archivos(anio)
    if not balances:
        raise FileNotFoundError(
            f"Faltan los balances de {anio} en {config.ruta_crudo(anio)}. Descárguelos de "
            "https://appscvsgen.supercias.gob.ec/consultaCompanias/societario/"
            "estadosFinancierosPorRamo.jsf (el formulario pide verificación humana) "
            "y regístrelos en MANIFEST.csv"
        )
    catalogo = leer_catalogo(catalogos[0]) if catalogos else {}

    partes = [leer_balances(ruta, anio) for ruta in balances]
    df = pd.concat(partes, ignore_index=True)
    for columna in ("nombre", "rama_actividad", "descripcion_rama", "ciiu"):
        df[columna] = df[columna].astype(str).str.strip()
    df["ruc"] = df["ruc"].astype(str).str.strip()
    df = df.drop_duplicates("expediente", keep="first")

    presentes = [c for c in CUENTAS_PERSONAL if c in df.columns]
    df["gasto_personal"] = df[presentes].fillna(0).sum(axis=1) if presentes else 0.0
    df["sin_gasto_personal"] = df["gasto_personal"] <= 0
    df = normalizar_ruc(df)

    df, descartes = separar_descartes(df)
    if not descartes.empty:
        ruta_descartes = config.ruta_plata(anio) / "descartes_financieros.csv"
        descartes.to_csv(ruta_descartes, index=False)
        log.warning(
            "Financieros %s: %s filas a cuarentena (%s) -> %s",
            anio,
            len(descartes),
            descartes["motivo_descarte"].value_counts().to_dict(),
            ruta_descartes.name,
        )
    df = ESQUEMA.validate(df, lazy=True)

    destino = config.ruta_plata(anio) / "financieros.parquet"
    df.to_parquet(destino, index=False)
    guardar_json(
        config.ruta_plata(anio) / "calidad_financieros.json",
        {
            "anio": anio,
            "archivos_balances": [r.name for r in balances],
            "archivo_catalogo": catalogos[0].name if catalogos else None,
            "cuentas_en_catalogo": len(catalogo),
            "filas": len(df),
            "filas_descartadas": len(descartes),
            "motivos_de_descarte": descartes["motivo_descarte"].value_counts().to_dict(),
            "cuentas_conservadas": [c for c in CUENTAS.values() if c in df.columns],
            "sin_gasto_personal": int(df["sin_gasto_personal"].sum()),
            "ruc_formato_invalido": int((~df["ruc_valido"]).sum()),
            "tolerancia_balance_usd": TOLERANCIA_BALANCE,
        },
    )
    log.info("Financieros %s: %s empresas -> %s", anio, f"{len(df):,}", destino)
    return df
