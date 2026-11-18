"""Paso `consolidar`: junta todos los años en las tablas que publicará la API.

Los pasos anteriores trabajan un año a la vez, que es como se descarga y como
se revisa. Pero la BD y la API no se consultan por año: se consultan por
empresa, con su serie de cifras. Este paso hace ese giro sin tocar la base,
dejando los archivos con **la misma forma que las tablas** descritas en
[base-de-datos.md](../../../base-de-datos.md):

| Archivo en `datos/oro/` | Tabla | Una fila por |
| --- | --- | --- |
| `empresa.parquet` | `oro.empresa` | empresa |
| `cifras_anuales.parquet` | `oro.cifras_anuales` | empresa y año |
| `universo_por_anio.parquet` | `oro.universo` | año y empresa |
| `ficha.parquet` | `oro.ficha` | empresa y fecha de captura |

Así `etl bd` no vuelve a calcular nada: solo inserta. Y se puede revisar que
los datos estén limpios antes de que exista la base.

Dos reglas de la consolidación:

- **La identificación sale del año más reciente** en que la empresa aparece.
  Una empresa cambia de nombre o de actividad; lo vigente es lo último.
- **La serie trae todos los años comparables**, no solo los años en que la
  empresa estuvo en el universo. Si entró al universo en 2025, sus cifras de
  2018 igual sirven para proyectar.
"""

from __future__ import annotations

import pandas as pd

from etl import config
from etl.comun import guardar_json, log

IDENTIFICACION = [
    "expediente",
    "ruc",
    "nombre",
    "ciiu",
    "ciiu_descripcion",
    "seccion_ciiu",
    "division_ciiu",
    "grupo",
    "tipo_compania",
    "region",
    "provincia",
    "ciudad",
    "es_holding",
]
CIFRAS = [
    "expediente",
    "anio",
    "empleados",
    "activo",
    "patrimonio",
    "ventas",
    "utilidad_neta",
    "ingreso_total",
    "tamano_derivado",
    "alerta_empleados",
    "nueva_en_ranking",
    "ingreso_total_no_reportado",
    "utilidad_no_reportada",
]
PRESENCIA = ["anio", "expediente", "grupo", "en_piloto", "criterio_piloto", "en_top50_tec"]


def anios_disponibles(minimo: int | None = None) -> list[int]:
    """Años con capa oro, de menor a mayor, desde el primero comparable."""
    minimo = config.ANIO_MINIMO_COMPARABLE if minimo is None else minimo
    anios = sorted(
        int(c.name)
        for c in config.ORO.iterdir()
        if c.is_dir() and c.name.isdigit() and (c / "universo.parquet").exists()
    )
    return [a for a in anios if a >= minimo]


def _leer(anio: int, archivo: str, **kwargs) -> pd.DataFrame:
    ruta = config.ruta_oro(anio) / archivo
    if not ruta.exists():
        return pd.DataFrame()
    lector = pd.read_parquet if ruta.suffix == ".parquet" else pd.read_csv
    return lector(ruta, **kwargs)


def tabla_empresa(anios: list[int]) -> pd.DataFrame:
    """Una fila por empresa, con la identificación del año más reciente."""
    universos = [
        _leer(a, "universo.parquet").assign(anio_identificacion=a) for a in reversed(anios)
    ]
    juntas = pd.concat([u for u in universos if not u.empty], ignore_index=True)
    # `reversed` pone el año más nuevo primero: la primera fila de cada
    # expediente es la identificación vigente.
    vigentes = juntas.drop_duplicates("expediente", keep="first")
    columnas = [c for c in IDENTIFICACION if c in vigentes.columns] + ["anio_identificacion"]
    return vigentes[columnas].sort_values("expediente").reset_index(drop=True)


def tabla_cifras(expedientes: set[int], anios: list[int]) -> pd.DataFrame:
    """Serie anual completa de las empresas del universo."""
    partes = []
    for anio in anios:
        plata = config.ruta_plata(anio) / "ranking.parquet"
        if not plata.exists():
            continue
        df = pd.read_parquet(plata)
        df = df[df["expediente"].isin(expedientes)]
        rangos = _leer(anio, "universo.parquet", columns=["expediente", "rank_grupo"])
        if not rangos.empty:
            df = df.merge(rangos, on="expediente", how="left")
        partes.append(df[[c for c in CIFRAS + ["rank_grupo"] if c in df.columns]])
    if not partes:
        return pd.DataFrame(columns=CIFRAS)
    cifras = pd.concat(partes, ignore_index=True)
    return cifras.sort_values(["expediente", "anio"]).reset_index(drop=True)


def tabla_presencia(anios: list[int]) -> pd.DataFrame:
    """En qué años el Observatorio abarca a cada empresa y cuáles tienen ficha."""
    partes = []
    for anio in anios:
        universo = _leer(anio, "universo.parquet", columns=["expediente", "grupo"])
        if universo.empty:
            continue
        piloto = _leer(anio, "piloto.csv")
        universo = universo.assign(anio=anio, en_piloto=False, criterio_piloto=pd.NA)
        universo["en_top50_tec"] = False
        if not piloto.empty:
            marcas = piloto.drop_duplicates("expediente")[
                ["expediente", "criterio_piloto", "en_top50_tec"]
            ]
            universo = universo.drop(columns=["criterio_piloto", "en_top50_tec"]).merge(
                marcas, on="expediente", how="left"
            )
            universo["en_piloto"] = universo["criterio_piloto"].notna()
            universo["en_top50_tec"] = universo["en_top50_tec"].fillna(False)
        partes.append(universo[PRESENCIA])
    if not partes:
        return pd.DataFrame(columns=PRESENCIA)
    return pd.concat(partes, ignore_index=True).sort_values(["anio", "expediente"])


def tabla_ficha(anios: list[int]) -> pd.DataFrame:
    """Company Profile de todos los años, una fila por empresa y captura."""
    partes = []
    for anio in anios:
        ruta = config.ruta_plata(anio) / "ficha_company_profile.csv"
        if ruta.exists():
            partes.append(pd.read_csv(ruta).assign(anio_captura=anio))
    if not partes:
        return pd.DataFrame()
    ficha = pd.concat(partes, ignore_index=True)
    return ficha.drop_duplicates(["expediente", "fecha_captura"], keep="last").reset_index(
        drop=True
    )


def ejecutar(desde: int | None = None) -> dict[str, int]:
    anios = anios_disponibles(desde)
    if not anios:
        raise FileNotFoundError(
            f"No hay años con capa oro desde {desde or config.ANIO_MINIMO_COMPARABLE}: "
            "ejecute antes `etl universo --anio AAAA`"
        )
    log.info("Consolidando %s años: %s-%s", len(anios), anios[0], anios[-1])

    empresa = tabla_empresa(anios)
    cifras = tabla_cifras(set(empresa["expediente"]), anios)
    presencia = tabla_presencia(anios)
    ficha = tabla_ficha(anios)

    destino = config.ORO
    empresa.to_parquet(destino / "empresa.parquet", index=False)
    cifras.to_parquet(destino / "cifras_anuales.parquet", index=False)
    presencia.to_parquet(destino / "universo_por_anio.parquet", index=False)
    if not ficha.empty:
        ficha.to_csv(destino / "ficha.csv", index=False)

    resumen = {
        "anios": len(anios),
        "empresa": len(empresa),
        "cifras_anuales": len(cifras),
        "universo_por_anio": len(presencia),
        "ficha": len(ficha),
    }
    guardar_json(
        destino / "calidad_consolidado.json",
        {
            "desde": anios[0],
            "hasta": anios[-1],
            "filas": resumen,
            "empresas_por_grupo": empresa["grupo"].value_counts().to_dict(),
            "anios_por_empresa": {
                "promedio": round(float(cifras.groupby("expediente").size().mean()), 2),
                "con_un_solo_anio": int((cifras.groupby("expediente").size() == 1).sum()),
            },
            "cifras_sin_ventas": int((cifras["ventas"] == 0).sum()),
            "ingreso_total_no_reportado": int(cifras["ingreso_total_no_reportado"].sum()),
            "empresas_en_piloto": int(presencia["en_piloto"].sum()),
            "fichas_por_estado": (
                ficha["estado"].value_counts().to_dict() if not ficha.empty else {}
            ),
        },
    )
    log.info("Consolidado -> %s: %s", destino, resumen)
    return resumen
