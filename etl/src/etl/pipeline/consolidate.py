"""Paso `consolidar`: junta todos los años en las tablas que publicará la API.

Los pasos anteriores trabajan un año a la vez, que es como se descarga y como
se revisa. Pero la BD y la API no se consultan por año: se consultan por
empresa, con su serie de cifras. Este paso hace ese giro sin tocar la base,
dejando los archivos con **la misma forma que las tablas** descritas en
[database.md](../../../database.md) y en el
[diseño de base de datos](../../../database.md):

| Archivo en `datos/oro/` | Tabla | Una fila por |
| --- | --- | --- |
| `empresa.parquet` | `public.empresa` | empresa |
| `cifras_anuales.parquet` | `public.cifras_anuales` | empresa y año |
| `ficha.csv` | `public.ficha` | empresa y fecha de captura |

No hay archivo ni tabla `universo`: con el universo fijo en 2025, una tabla
por `(año, expediente)` repetía casi todo lo que ya está en `cifras_anuales`.
Sus columnas se repartieron según si cambian por año o no (ADR 0009):

| Columna | Vive en | Por qué ahí |
| --- | --- | --- |
| `grupo`, `en_piloto`, `criterio_piloto`, `en_top50_tec` | `empresa` | Del universo 2025 |
| `en_universo_ese_anio` | `cifras_anuales` | Si cumplía la delimitación ese ejercicio |

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
- **`en_universo_ese_anio` dice si cumplía la delimitación** ese ejercicio en
  particular, sin cambiar quién está en el universo.
"""

from __future__ import annotations

import pandas as pd

from etl import config
from etl.common import guardar_json, log

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
    "tiene_alerta",
    "motivo_alerta",
    "nueva_en_ranking",
    "ingreso_total_no_reportado",
    "utilidad_no_reportada",
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
    """Las empresas del universo del año de referencia, con lo que es estático.

    `en_piloto`, `criterio_piloto` y `en_top50_tec` son del universo fijado
    en `anio_universo`: no se recalculan por año, así que viven aquí y no en
    `cifras_anuales`.
    """
    universo = _leer(anio_universo, "universo.parquet")
    if universo.empty:
        raise FileNotFoundError(
            f"Falta el universo {anio_universo}: ejecute `etl universo --anio {anio_universo}`"
        )
    piloto = _leer(anio_universo, "piloto.csv")

    universo = universo.drop_duplicates("expediente").assign(anio_identificacion=anio_universo)
    columnas = [c for c in IDENTIFICACION if c in universo.columns] + ["anio_identificacion"]
    empresa = universo[columnas].copy()

    if not piloto.empty:
        del_piloto = piloto.drop_duplicates("expediente").set_index("expediente")
        empresa["en_piloto"] = empresa["expediente"].isin(del_piloto.index)
        empresa["criterio_piloto"] = empresa["expediente"].map(
            del_piloto.get("criterio_piloto", pd.Series(dtype=object))
        )
        empresa["en_top50_tec"] = (
            empresa["expediente"].map(del_piloto.get("en_top50_tec", pd.Series(dtype=bool)))
        ).fillna(False)
    else:
        empresa["en_piloto"] = False
        empresa["criterio_piloto"] = pd.NA
        empresa["en_top50_tec"] = False

    return empresa.sort_values("expediente").reset_index(drop=True)


def tabla_cifras(expedientes: set[int], anios: list[int]) -> pd.DataFrame:
    """Serie anual completa de las empresas del universo.

    `en_universo_ese_anio` se agrega aquí, no en un archivo aparte: es un
    dato por (expediente, año), igual que todo lo demás en esta tabla.
    """
    partes = []
    for anio in anios:
        plata = config.ruta_plata(anio) / "ranking.parquet"
        if not plata.exists():
            continue
        df = pd.read_parquet(plata)
        df = df[df["expediente"].isin(expedientes)].copy()
        # La columna "anio" del Parquet es la posición del ranking ("Año"),
        # no el ejercicio fiscal: viene en 0 en las filas sin posición
        # asignada (ver sin_posicion_ranking). El ejercicio es el del
        # archivo que se está leyendo, no el de esa columna.
        df["anio"] = anio
        df["motivo_alerta"] = df["alerta_empleados"].replace("", None)
        df["tiene_alerta"] = df["motivo_alerta"].notna()
        rangos = _leer(anio, "universo.parquet", columns=["expediente", "rank_grupo"])
        if not rangos.empty:
            df = df.merge(rangos, on="expediente", how="left")
        del_anio = _leer(anio, "universo.parquet", columns=["expediente"])
        df["en_universo_ese_anio"] = df["expediente"].isin(set(del_anio.get("expediente", [])))
        columnas = CIFRAS + ["rank_grupo", "en_universo_ese_anio"]
        partes.append(df[[c for c in columnas if c in df.columns]])
    if not partes:
        return pd.DataFrame(columns=[*CIFRAS, "en_universo_ese_anio"])
    cifras = pd.concat(partes, ignore_index=True)
    return cifras.sort_values(["expediente", "anio"]).reset_index(drop=True)


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
    cifras = tabla_cifras(set(empresa["expediente"]), anios)
    ficha = tabla_ficha(anios)

    destino = config.ORO
    empresa.to_parquet(destino / "empresa.parquet", index=False)
    cifras.to_parquet(destino / "cifras_anuales.parquet", index=False)
    if not ficha.empty:
        ficha.to_csv(destino / "ficha.csv", index=False)

    resumen = {
        "anios": len(anios),
        "empresa": len(empresa),
        "cifras_anuales": len(cifras),
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
            "empresas_en_piloto": int(empresa["en_piloto"].sum()),
            "fichas_por_estado": (
                ficha["estado"].value_counts().to_dict() if not ficha.empty else {}
            ),
        },
    )
    log.info("Consolidado -> %s: %s", destino, resumen)
    return resumen
