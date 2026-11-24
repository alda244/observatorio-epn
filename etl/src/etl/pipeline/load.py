"""Paso `bd`: carga la capa oro en PostgreSQL.

No calcula nada: inserta los archivos que dejó `etl consolidar`, que ya tienen
la forma de las tablas. Lo único que se lee por año son los documentos, porque
el texto vive en los HTML de `crudo/web/AAAA/`.

El paso es idempotente: cada tabla se escribe con `INSERT ... ON CONFLICT DO
UPDATE`, así que repetirlo no duplica filas. Alembic crea las tablas y la API
consulta las vistas publicadas.
"""

from __future__ import annotations

import pandas as pd
import trafilatura
from sqlalchemy import Table, create_engine
from sqlalchemy.dialects.postgresql import insert

from etl import config
from etl.bd import schema
from etl.common import leer_jsonl, log
from etl.pipeline import profile


def motor(url: str | None = None):
    return create_engine(url or config.database_url())


def _vaciar_nulos(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def guardar(conexion, tabla: Table, df: pd.DataFrame) -> int:
    """Inserta o actualiza las filas por su clave de carga.

    Se envía por lotes porque PostgreSQL admite 65.535 parámetros por consulta.
    """
    columnas = [c.name for c in tabla.columns if c.name in df.columns]
    claves = (
        ["expediente", "sha256"]
        if tabla is schema.documento
        else [c.name for c in tabla.primary_key.columns]
    )
    filas = _vaciar_nulos(df[columnas].drop_duplicates(subset=claves, keep="last"))
    if not filas:
        return 0
    por_lote = max(1, 60_000 // max(1, len(columnas)))
    for inicio in range(0, len(filas), por_lote):
        sentencia = insert(tabla).values(filas[inicio : inicio + por_lote])
        actualizables = {c: sentencia.excluded[c] for c in columnas if c not in claves}
        if actualizables:
            sentencia = sentencia.on_conflict_do_update(index_elements=claves, set_=actualizables)
        else:
            sentencia = sentencia.on_conflict_do_nothing(index_elements=claves)
        conexion.execute(sentencia)
    return len(filas)


def _indicadores_sector() -> pd.DataFrame:
    """Indicadores financieros por sección CIIU que publica la SCVS.

    Es una tabla de referencia con sus propios años (2018–2023), así que se
    carga completa y no se filtra por el año del pipeline.
    """
    archivos = sorted(config.CRUDO.glob("*/indicadores_sector.csv"))
    if not archivos:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(a) for a in archivos], ignore_index=True)
    fijas = ["anio", "ciiu_n1", "descripcion"]
    largo = df.melt(id_vars=fijas, var_name="indicador", value_name="valor")
    largo = largo.rename(columns={"ciiu_n1": "seccion_ciiu", "descripcion": "descripcion_seccion"})
    largo["valor"] = pd.to_numeric(largo["valor"], errors="coerce")
    return largo.dropna(subset=["valor"])


def documentos_de(anio: int) -> pd.DataFrame:
    """Páginas capturadas de un año, con su texto, para que A las indexe."""
    carpeta = config.ruta_web(anio)
    paginas = pd.DataFrame(leer_jsonl(carpeta / "manifest.jsonl"))
    if paginas.empty:
        return paginas
    huellas = paginas.get("sha256", pd.Series("", index=paginas.index))
    paginas = paginas[paginas["status"].eq(200) & huellas.fillna("").ne("")]
    paginas = paginas.drop_duplicates(["expediente", "sha256"])
    if paginas.empty:
        return paginas
    paginas = paginas.assign(
        fecha_captura=paginas["fecha_captura"].str[:10],
        titulo=paginas["title"],
        formato="html",
        tipo_fuente="web_oficial",
    )
    paginas["texto"] = [
        (trafilatura.extract(profile.html_de(carpeta, fila), include_comments=False) or "")[
            :200_000
        ]
        for _, fila in paginas.iterrows()
    ]
    return paginas


def ejecutar(anio: int | None = None, url: str | None = None) -> dict[str, int]:
    """Carga el consolidado y, si se indica un año, los documentos de ese año."""
    consolidado = {
        "empresa": config.ORO / "empresa.parquet",
        "cifras_anuales": config.ORO / "cifras_anuales.parquet",
    }
    faltantes = [str(r) for r in consolidado.values() if not r.exists()]
    if faltantes:
        raise FileNotFoundError(f"Faltan {', '.join(faltantes)}: ejecute antes `etl consolidar`")

    tablas = {
        schema.empresa: pd.read_parquet(consolidado["empresa"]),
        schema.cifras_anuales: pd.read_parquet(consolidado["cifras_anuales"]),
    }
    ruta_ficha = config.ORO / "ficha.csv"
    if ruta_ficha.exists():
        tablas[schema.ficha] = pd.read_csv(ruta_ficha)
    if anio is not None:
        documentos = documentos_de(anio)
        if not documentos.empty:
            tablas[schema.documento] = documentos
    indicadores = _indicadores_sector()
    if not indicadores.empty:
        tablas[schema.indicador_sector] = indicadores

    resumen: dict[str, int] = {}
    with motor(url).begin() as conexion:
        for tabla, df in tablas.items():
            resumen[tabla.name] = guardar(conexion, tabla, df)
    log.info("Base de datos: %s", resumen)
    return resumen
