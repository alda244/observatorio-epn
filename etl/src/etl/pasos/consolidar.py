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

Las tres reglas de la consolidación, que vienen de la delimitación aprobada
([docs/universo.md](../../../../docs/universo.md)):

- **El universo se fija con un año de referencia**, `config.ANIO_UNIVERSO`:
  «El universo se fija con el ranking 2025. Si una empresa sale del ranking en
  años posteriores, conserva su ficha con la fecha de captura». Los otros años
  no agregan empresas; recalcular el universo año por año y unirlo daría un
  conjunto distinto del aprobado.
- **La serie trae todos los años comparables** de esas mismas empresas. Una
  empresa del universo 2025 aporta sus cifras de 2012 en adelante, que es lo
  que permite proyectar.
- **La presencia dice en qué años apareció cada empresa** y si ese año cumplía
  la delimitación, sin cambiar quién está en el universo.
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
PRESENCIA = [
    "anio",
    "expediente",
    "grupo",
    "en_universo_ese_anio",
    "en_piloto",
    "criterio_piloto",
    "en_top50_tec",
]


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


def tabla_empresa(anio_universo: int) -> pd.DataFrame:
    """Las empresas del universo del año de referencia, una fila cada una."""
    universo = _leer(anio_universo, "universo.parquet")
    if universo.empty:
        raise FileNotFoundError(
            f"Falta el universo {anio_universo}: ejecute `etl universo --anio {anio_universo}`"
        )
    universo = universo.assign(anio_identificacion=anio_universo)
    columnas = [c for c in IDENTIFICACION if c in universo.columns] + ["anio_identificacion"]
    return (
        universo.drop_duplicates("expediente")[columnas]
        .sort_values("expediente")
        .reset_index(drop=True)
    )


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


def tabla_presencia(anios: list[int], empresa: pd.DataFrame, piloto: pd.DataFrame) -> pd.DataFrame:
    """En qué años aparece cada empresa del universo y cuáles tienen ficha.

    El universo y el piloto son los del año de referencia; esta tabla no los
    cambia. La columna `en_universo_ese_anio` dice si además cumplía la
    delimitación en ese ejercicio, que es información de análisis.
    """
    fijas = set(empresa["expediente"])
    grupo = empresa.set_index("expediente")["grupo"]
    del_piloto = piloto.drop_duplicates("expediente").set_index("expediente")

    partes = []
    for anio in anios:
        plata = config.ruta_plata(anio) / "ranking.parquet"
        if not plata.exists():
            continue
        presentes = sorted(
            fijas & set(pd.read_parquet(plata, columns=["expediente"])["expediente"])
        )
        del_anio = _leer(anio, "universo.parquet", columns=["expediente"])
        df = pd.DataFrame({"anio": anio, "expediente": presentes})
        df["grupo"] = df["expediente"].map(grupo)
        df["en_universo_ese_anio"] = df["expediente"].isin(set(del_anio.get("expediente", [])))
        df["en_piloto"] = df["expediente"].isin(del_piloto.index)
        df["criterio_piloto"] = df["expediente"].map(del_piloto.get("criterio_piloto", pd.Series()))
        df["en_top50_tec"] = (
            df["expediente"].map(del_piloto.get("en_top50_tec", pd.Series())).fillna(False)
        )
        partes.append(df[PRESENCIA])
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


def ejecutar(desde: int | None = None, anio_universo: int | None = None) -> dict[str, int]:
    anio_universo = anio_universo or config.ANIO_UNIVERSO
    anios = anios_disponibles(desde)
    if not anios:
        raise FileNotFoundError(
            f"No hay años con capa oro desde {desde or config.ANIO_MINIMO_COMPARABLE}: "
            "ejecute antes `etl universo --anio AAAA`"
        )
    log.info(
        "Consolidando: universo fijado con %s, serie %s-%s",
        anio_universo,
        anios[0],
        anios[-1],
    )

    empresa = tabla_empresa(anio_universo)
    piloto = _leer(anio_universo, "piloto.csv")
    cifras = tabla_cifras(set(empresa["expediente"]), anios)
    presencia = tabla_presencia(anios, empresa, piloto)
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
            "anio_universo": anio_universo,
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
            # Empresas distintas, no filas: una del piloto aparece en varios años.
            "empresas_en_piloto": int(
                presencia.loc[presencia["en_piloto"], "expediente"].nunique()
            ),
            "fichas_por_estado": (
                ficha["estado"].value_counts().to_dict() if not ficha.empty else {}
            ),
        },
    )
    log.info("Consolidado -> %s: %s", destino, resumen)
    return resumen
