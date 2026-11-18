"""Paso `financieros`: estados financieros por ramo de la SCVS a la capa plata.

El archivo crudo trae una columna por cuenta contable (más de 600) con el
código, no el nombre; el catálogo del mismo año traduce esos códigos. De todas
las cuentas se conservan las que el Observatorio necesita, entre ellas el gasto
en sueldos, que permite interpretar el dato de empleados del ranking.

Fuente: Portal de Información Societario de la SCVS, "Estados financieros por
ramo". La descarga es manual porque el formulario pide verificación humana.
"""

from __future__ import annotations

import pandas as pd

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
            "cuentas_conservadas": [c for c in CUENTAS.values() if c in df.columns],
            "sin_gasto_personal": int(df["sin_gasto_personal"].sum()),
        },
    )
    log.info("Financieros %s: %s empresas -> %s", anio, f"{len(df):,}", destino)
    return df
