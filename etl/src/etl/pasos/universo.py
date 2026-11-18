"""Paso `universo`: de plata a oro.

Aplica la delimitación aprobada el 04-nov-2026 (docs/universo.md): todas las
tecnológicas más las medianas y grandes de G, C, M y K, y un piloto de 500
empresas con ficha completa.
"""

from __future__ import annotations

import pandas as pd

from etl import config
from etl.comun import guardar_json, log

COLUMNAS = [
    "expediente",
    "ruc",
    "nombre",
    "anio",
    "grupo",
    "ciiu",
    "ciiu_descripcion",
    "seccion_ciiu",
    "division_ciiu",
    "tamano_derivado",
    "tipo_compania",
    "region",
    "provincia",
    "ciudad",
    "empleados",
    "activo",
    "patrimonio",
    "ventas",
    "utilidad_neta",
    "ingreso_total",
    "es_holding",
    "alerta_empleados",
    "nueva_en_ranking",
    "rank_grupo",
]
COLUMNAS_NOMINA = ["gasto_personal", "empleados_estimados_nomina", "diagnostico_empleados"]


def grupo_de(ciiu: str) -> str | None:
    if ciiu.startswith(config.PREFIJOS_TEC):
        return "TEC"
    return ciiu[0] if ciiu[0] in config.SECCIONES else None


def marcar(plata: pd.DataFrame) -> pd.DataFrame:
    df = plata.copy()
    df["grupo"] = df["ciiu"].map(grupo_de)
    # Sociedades de cartera: no ofrecen productos ni servicios al público.
    df["es_holding"] = df["ciiu"].str.startswith("K642") | df["nombre"].str.contains(
        "HOLDING", case=False, regex=False
    )
    return df


def seleccionar(df: pd.DataFrame) -> pd.DataFrame:
    valida = df[df["grupo"].notna() & ~df["anio_cero"]]
    universo = valida[
        (valida["grupo"] == "TEC") | (valida["tamano_derivado"] != "micro_pequena")
    ].copy()
    universo["rank_grupo"] = (
        universo.groupby("grupo")["ventas"].rank(ascending=False, method="first").astype(int)
    )
    return universo.sort_values(["grupo", "rank_grupo"]).reset_index(drop=True)


def listas_top(universo: pd.DataFrame) -> dict[str, pd.DataFrame]:
    tops = {}
    for grupo in config.GRUPOS:
        candidatos = universo[universo["grupo"] == grupo]
        if grupo == "K":  # los holdings quedan fuera del top 50, no del universo
            candidatos = candidatos[~candidatos["es_holding"]]
        if grupo == "TEC":
            candidatos = candidatos[candidatos["tamano_derivado"] != "micro_pequena"]
        tops[grupo] = candidatos.nsmallest(config.TOP_N, "rank_grupo")
    return tops


def armar_piloto(universo: pd.DataFrame, tops: dict[str, pd.DataFrame]) -> pd.DataFrame:
    tecnologicas = universo[
        (universo["grupo"] == "TEC") & (universo["tamano_derivado"] != "micro_pequena")
    ]
    piloto = pd.concat(
        [tecnologicas.assign(criterio_piloto="tecnologica_mediana_grande")]
        + [tops[g].assign(criterio_piloto=f"top50_{g.lower()}") for g in config.SECCIONES]
    )
    piloto["en_top50_tec"] = piloto["expediente"].isin(tops["TEC"]["expediente"])
    return piloto.reset_index(drop=True)


def diagnosticar_empleados(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Usa el gasto en sueldos para explicar por qué el dato de empleados falla.

    El ranking no permite distinguir una empresa sin nómina propia (personal
    tercerizado o contratado por otra sociedad del grupo) de un error de
    registro. El gasto en sueldos de los estados financieros sí: si la empresa
    paga una nómina grande y declara pocos empleados, el dato está mal escrito.
    """
    financieros = config.ruta_plata(anio) / "financieros.parquet"
    if not financieros.exists():
        return df.assign(
            gasto_personal=pd.NA,
            empleados_estimados_nomina=pd.NA,
            diagnostico_empleados="sin_estados_financieros",
        )

    nomina = pd.read_parquet(financieros, columns=["expediente", "gasto_personal"])
    df = df.merge(nomina, on="expediente", how="left")

    # Sueldo medio por empleado de cada división, sobre las empresas sin alerta.
    confiables = df[
        (df["alerta_empleados"] == "") & (df["empleados"] > 0) & (df["gasto_personal"] > 0)
    ]
    sueldo_medio = confiables.groupby("division_ciiu").apply(
        lambda g: g["gasto_personal"].sum() / g["empleados"].sum(), include_groups=False
    )
    referencia = df["division_ciiu"].map(sueldo_medio)
    df["empleados_estimados_nomina"] = (df["gasto_personal"] / referencia).round()

    con_alerta = df["alerta_empleados"] != ""
    df["diagnostico_empleados"] = "coherente"
    df.loc[df["gasto_personal"].isna(), "diagnostico_empleados"] = "sin_estados_financieros"
    df.loc[con_alerta & (df["gasto_personal"] > 0), "diagnostico_empleados"] = "error_de_registro"
    df.loc[con_alerta & (df["gasto_personal"] <= 0), "diagnostico_empleados"] = "sin_nomina_propia"
    df.loc[~con_alerta & df["gasto_personal"].notna(), "diagnostico_empleados"] = "coherente"
    return df


def ejecutar(anio: int) -> pd.DataFrame:
    config.preparar(anio)
    origen = config.ruta_plata(anio) / "ranking.parquet"
    if not origen.exists():
        raise FileNotFoundError(f"Falta {origen}: ejecute antes `etl ranking --anio {anio}`")

    plata = pd.read_parquet(origen)
    cobertura = float((plata["ventas"] > 0).mean() * 100)
    if cobertura < config.COBERTURA_MINIMA_VENTAS:
        log.warning(
            "El ranking %s solo trae ventas en %.1f %% de las filas: el universo de este año "
            "no es comparable con los demás y no debe publicarse",
            anio,
            cobertura,
        )
    df = marcar(plata)
    df = diagnosticar_empleados(df, anio)
    universo = seleccionar(df)
    tops = listas_top(universo)
    piloto = armar_piloto(universo, tops)

    oro = config.ruta_oro(anio)
    columnas = COLUMNAS + [c for c in COLUMNAS_NOMINA if c in universo.columns]
    universo[columnas].to_parquet(oro / "universo.parquet", index=False)
    universo[columnas].to_csv(oro / "universo.csv", index=False)
    piloto[columnas + ["criterio_piloto", "en_top50_tec"]].to_csv(oro / "piloto.csv", index=False)
    for grupo, tabla in tops.items():
        tabla[columnas].to_csv(oro / f"top50_{grupo.lower()}.csv", index=False)

    guardar_json(
        oro / "calidad_universo.json",
        {
            "anio": anio,
            "cobertura_ventas_pct": round(cobertura, 2),
            "comparable": bool(
                cobertura >= config.COBERTURA_MINIMA_VENTAS
                and anio >= config.ANIO_MINIMO_COMPARABLE
            ),
            "universo_total": len(universo),
            "universo_por_grupo": universo["grupo"].value_counts().to_dict(),
            "piloto_total": len(piloto),
            "piloto_por_criterio": piloto["criterio_piloto"].value_counts().to_dict(),
            "holdings_en_universo": int(universo["es_holding"].sum()),
            "piloto_con_alerta_empleados": int((piloto["alerta_empleados"] != "").sum()),
            "diagnostico_empleados": universo["diagnostico_empleados"].value_counts().to_dict(),
            "participacion_ventas_universo": round(
                float(universo["ventas"].sum() / df["ventas"].sum()), 4
            ),
            "participacion_ventas_piloto": round(
                float(piloto["ventas"].sum() / df["ventas"].sum()), 4
            ),
        },
    )
    log.info("Oro %s: universo %s, piloto %s -> %s", anio, f"{len(universo):,}", len(piloto), oro)
    return universo
