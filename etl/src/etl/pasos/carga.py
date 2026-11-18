"""Paso `bd`: carga la capa oro en PostgreSQL.

No calcula nada: inserta los archivos que dejó `etl consolidar`, que ya tienen
la forma de las tablas. Lo único que se lee por año son los documentos, porque
el texto vive en los HTML de `crudo/web/AAAA/`.

El paso es idempotente: cada tabla se escribe con `INSERT ... ON CONFLICT DO
UPDATE`, así que repetirlo no duplica filas. La API solo lee estas tablas; las
crea y las escribe el ETL.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert

from etl import config
from etl.bd import esquema
from etl.comun import leer_jsonl, log


def motor(url: str | None = None):
    return create_engine(url or config.BASE_DE_DATOS, future=True)


def crear_esquema(conexion) -> None:
    """Crea los esquemas que falten y las tablas de oro.

    En la base del proyecto los esquemas ya vienen creados por
    `infra/postgres/init/01-esquemas.sh`, y `rol_datos` es su dueño pero no
    puede crear esquemas nuevos: por eso se comprueba antes de intentarlo.
    """
    existentes = {
        fila[0]
        for fila in conexion.execute(text("SELECT schema_name FROM information_schema.schemata"))
    }
    for nombre in (esquema.ESQUEMA_PLATA, esquema.ESQUEMA_ORO):
        if nombre not in existentes:
            conexion.execute(text(f'CREATE SCHEMA "{nombre}"'))
    esquema.metadata.create_all(conexion)


def _vaciar_nulos(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def guardar(conexion, tabla: Table, df: pd.DataFrame) -> int:
    """Inserta o actualiza las filas según la clave primaria de la tabla.

    Se envía por lotes porque PostgreSQL admite 65.535 parámetros por consulta.
    """
    columnas = [c.name for c in tabla.columns if c.name in df.columns]
    filas = _vaciar_nulos(df[columnas].drop_duplicates())
    if not filas:
        return 0
    claves = [c.name for c in tabla.primary_key.columns]
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
    paginas = paginas[paginas["status"] == 200]
    if "sha256" in paginas:
        paginas = paginas[paginas["sha256"].astype(str) != ""]
    paginas = paginas.drop_duplicates(["expediente", "sha256"])
    if paginas.empty:
        return paginas
    paginas = paginas.assign(
        fecha_captura=paginas["fecha_captura"].str[:10], titulo=paginas["title"]
    )
    paginas["texto"] = [
        (carpeta / f"{e}_{h}.html").read_text(encoding="utf-8")[:200_000]
        for e, h in zip(paginas["expediente"], paginas["sha256"], strict=True)
    ]
    return paginas


def ejecutar(anio: int | None = None, url: str | None = None) -> dict[str, int]:
    """Carga el consolidado y, si se indica un año, los documentos de ese año."""
    consolidado = {
        "empresa": config.ORO / "empresa.parquet",
        "cifras_anuales": config.ORO / "cifras_anuales.parquet",
        "universo": config.ORO / "universo_por_anio.parquet",
    }
    faltantes = [str(r) for r in consolidado.values() if not r.exists()]
    if faltantes:
        raise FileNotFoundError(f"Faltan {', '.join(faltantes)}: ejecute antes `etl consolidar`")

    tablas = {
        esquema.empresa: pd.read_parquet(consolidado["empresa"]),
        esquema.cifras_anuales: pd.read_parquet(consolidado["cifras_anuales"]),
        esquema.universo: pd.read_parquet(consolidado["universo"]),
    }
    ruta_ficha = config.ORO / "ficha.csv"
    if ruta_ficha.exists():
        tablas[esquema.ficha] = pd.read_csv(ruta_ficha)
    if anio is not None:
        documentos = documentos_de(anio)
        if not documentos.empty:
            tablas[esquema.documento] = documentos
    indicadores = _indicadores_sector()
    if not indicadores.empty:
        tablas[esquema.indicador_sector] = indicadores

    resumen: dict[str, int] = {}
    with motor(url).begin() as conexion:
        crear_esquema(conexion)
        for tabla, df in tablas.items():
            resumen[tabla.name] = guardar(conexion, tabla, df)
    log.info("Base de datos: %s", resumen)
    return resumen
