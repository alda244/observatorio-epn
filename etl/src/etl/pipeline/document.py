"""Paso `documentar`: escribe cómo se almacenan los datos, con datos reales.

[database.md](../../../database.md) explica el diseño: por qué las
tablas son esas y cómo se relacionan. Este paso escribe el otro documento, el
que muestra **qué hay de verdad adentro**: cuántas filas, de qué tipo, con
qué valores y qué respondería la API si se consultara hoy.

Se genera del consolidado en vez de escribirse a mano, por una razón: un
documento con cifras escritas a mano queda desactualizado en la siguiente
corrida y nadie se entera. Este se regenera con `etl documentar` y, si algo
dejó de cuadrar entre el esquema y los archivos, lo dice.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
from sqlalchemy import Table

from etl import config
from etl.bd import schema
from etl.common import log

DESTINO = "database-contents.md"

ARCHIVOS: dict[str, tuple[Table, str]] = {
    "empresa": (schema.empresa, "empresa.parquet"),
    "cifras_anuales": (schema.cifras_anuales, "cifras_anuales.parquet"),
    "ficha": (schema.ficha, "ficha.csv"),
}
PARA_QUE = {
    "empresa": ("Lo que no cambia de cada compañía.", "`GET /v1/empresas/{expediente}`"),
    "cifras_anuales": (
        "Una fila por empresa y ejercicio fiscal. Es la que permite series y proyecciones.",
        "`GET /v1/empresas` y el bloque de cifras del detalle",
    ),
    "ficha": (
        "El Company Profile, con la fuente de cada campo.",
        "`GET /v1/empresas/{expediente}` (Bloque 2)",
    ),
}


def _leer(nombre: str) -> pd.DataFrame:
    ruta = config.ORO / nombre
    if not ruta.exists():
        return pd.DataFrame()
    return pd.read_parquet(ruta) if ruta.suffix == ".parquet" else pd.read_csv(ruta)


def _miles(numero) -> str:
    """Separador de miles con punto, como se escribe en español."""
    return f"{int(numero):,}".replace(",", ".")


def _ejemplo(serie: pd.Series) -> str:
    valores = serie.dropna()
    if valores.empty:
        return "—"
    valor = valores.iloc[0]
    if isinstance(valor, float) and valor == int(valor) and abs(valor) < 1e15:
        valor = int(valor)
    texto = str(valor).replace("|", "\\|").replace("\n", " ")
    return (texto[:60] + "…") if len(texto) > 60 else texto


def _md(df: pd.DataFrame, indice: bool = False) -> str:
    """Un DataFrame como tabla Markdown, sin dependencias extra.

    El formato se decide por columna y no por celda: `iterrows` convertiría
    una fila mixta a float y los años saldrían como «2.012».
    """
    tabla = df.reset_index() if indice else df
    columnas = {}
    for nombre in tabla.columns:
        serie = tabla[nombre]
        if nombre in ("anio", "anio_identificacion", "expediente"):
            columnas[nombre] = serie.map(lambda v: "" if pd.isna(v) else str(int(v)))
        elif pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_bool_dtype(serie):
            columnas[nombre] = serie.map(lambda v: "" if pd.isna(v) else _miles(round(v)))
        else:
            columnas[nombre] = serie.map(lambda v: _ejemplo(pd.Series([v])))
    encabezado = [str(c) for c in tabla.columns]
    lineas = [
        "| " + " | ".join(encabezado) + " |",
        "| " + " | ".join("---" for _ in encabezado) + " |",
    ]
    for i in range(len(tabla)):
        lineas.append("| " + " | ".join(columnas[c].iloc[i] for c in tabla.columns) + " |")
    return "\n".join(lineas)


def tabla_de_columnas(tabla: Table, df: pd.DataFrame) -> str:
    """Columna por columna: tipo en PostgreSQL, nulos reales y un valor real."""
    lineas = [
        "| Columna | Tipo en PostgreSQL | Clave | Sin dato | Ejemplo real |",
        "| --- | --- | --- | --- | --- |",
    ]
    claves = {c.name for c in tabla.primary_key.columns}
    for columna in tabla.columns:
        if columna.name not in df.columns:
            lineas.append(
                f"| `{columna.name}` | {columna.type} | | **no está en el archivo** | — |"
            )
            continue
        serie = df[columna.name]
        vacios = float(serie.isna().mean() * 100)
        lineas.append(
            f"| `{columna.name}` | {columna.type} | {'PK' if columna.name in claves else ''} "
            f"| {vacios:.0f} % | {_ejemplo(serie)} |"
        )
    sobrantes = [c for c in df.columns if c not in tabla.columns]
    if sobrantes:
        nombres = ", ".join(f"`{c}`" for c in sobrantes)
        lineas.append("")
        lineas.append(f"Columnas del archivo que la tabla no guarda: {nombres}.")
    return "\n".join(lineas)


def filas_reales(df: pd.DataFrame, tabla: Table, cuantas: int = 2) -> str:
    """Dos filas de verdad, escritas una debajo de otra para que se puedan leer."""
    columnas = [c.name for c in tabla.columns if c.name in df.columns]
    bloques = []
    for _, fila in df[columnas].head(cuantas).iterrows():
        partes = [
            f"{nombre} = {_ejemplo(pd.Series([valor]))}"
            for nombre, valor in fila.items()
            if pd.notna(valor)
        ]
        bloques.append("- " + " · ".join(partes))
    return "\n".join(bloques)


def _consultas(empresa: pd.DataFrame, cifras: pd.DataFrame) -> str:
    """Calcula ejemplos del contrato sobre los archivos de origen."""
    anio = config.ANIO_UNIVERSO
    tecnologicas = empresa.loc[empresa["grupo"].eq("TEC"), ["expediente", "nombre"]]
    ultimo = cifras[cifras["anio"].eq(anio) & cifras["en_universo_ese_anio"]]
    listado = ultimo.merge(tecnologicas, on="expediente")
    top = listado.nlargest(3, "ventas")[["expediente", "nombre", "ventas", "empleados"]]
    partes = [
        f"### `GET /v1/empresas?anio={anio}&grupo=TEC`",
        "",
        f"Devolvería **{_miles(len(listado))} empresas**. Las tres primeras por ventas.",
        "",
        _md(top),
    ]

    if not ultimo.empty:
        expediente = int(ultimo.nlargest(1, "ventas")["expediente"].iloc[0])
        serie = cifras[cifras["expediente"].eq(expediente)].sort_values("anio")
        nombre = empresa.set_index("expediente").loc[expediente, "nombre"]
        partes.extend(
            [
                "",
                f"### `GET /v1/empresas/{expediente}`",
                "",
                f"La serie de **{nombre}** cubre {len(serie)} ejercicios.",
                "",
                _md(serie[["anio", "ventas", "utilidad_neta", "empleados"]]),
            ]
        )

    por_anio = cifras.groupby("anio").agg(
        empresas_con_cifras=("expediente", "size"),
        empresas_que_cumplian_delimitacion=("en_universo_ese_anio", "sum"),
    )
    partes.extend(["", "### Cobertura anual del universo fijo", "", _md(por_anio, indice=True)])
    return "\n".join(partes)


def ejecutar() -> str:
    datos = {nombre: _leer(archivo) for nombre, (_, archivo) in ARCHIVOS.items()}
    faltantes = [
        archivo
        for tabla, archivo in ARCHIVOS.values()
        if tabla is not schema.ficha and not (config.ORO / archivo).exists()
    ]
    if faltantes:
        raise FileNotFoundError(f"Faltan {', '.join(faltantes)}: ejecute antes `etl consolidar`")

    hoy = dt.date.today().isoformat()
    partes = [
        "# Cómo se almacenan los datos en la base",
        "",
        f"Generado el {hoy} con `etl documentar`, a partir de los archivos reales de",
        "`datos/oro/`. Las cifras de este documento no son ejemplos: son lo que hay.",
        "",
        "El diseño —por qué las tablas son estas y cómo se relacionan— está en",
        "[database.md](database.md). Aquí se ve el contenido.",
        "",
        "## Lo que se cargaría hoy",
        "",
        "| Tabla | Filas | Archivo de origen | En disco |",
        "| --- | --- | --- | --- |",
    ]
    for nombre, (_, archivo) in ARCHIVOS.items():
        ruta = config.ORO / archivo
        peso = f"{ruta.stat().st_size / 1e6:.1f} MB" if ruta.exists() else "—"
        partes.append(
            f"| `public.{nombre}` | {_miles(len(datos[nombre]))} | `{archivo}` | {peso} |"
        )
    partes += [
        "| `public.documento` | se arma al cargar | `crudo/web/AAAA/manifest.jsonl` + HTML | |",
        "| `public.indicador_sector` | se arma al cargar | `crudo/AAAA/indicadores_sector.csv` | |",
        "",
        "Las dos últimas no pasan por el consolidado: el texto de las páginas y los",
        "indicadores sectoriales se leen en el momento de la carga.",
        "",
    ]

    for nombre, (tabla, _) in ARCHIVOS.items():
        df = datos[nombre]
        para_que, ruta_api = PARA_QUE[nombre]
        partes += [
            f"## `public.{nombre}`",
            "",
            para_que,
            "",
            f"- Filas: **{_miles(len(df))}**",
            f"- Clave primaria: {', '.join(f'`{c.name}`' for c in tabla.primary_key.columns)}",
            f"- La publica: {ruta_api}",
            "",
            tabla_de_columnas(tabla, df),
            "",
            "Dos filas reales:",
            "",
            filas_reales(df, tabla),
            "",
        ]

    partes += [
        "## Qué respondería la API hoy",
        "",
        "Los ejemplos siguen el contrato y los resultados están calculados sobre",
        "estos mismos archivos.",
        "",
        _consultas(datos["empresa"], datos["cifras_anuales"]),
        "",
        "## Cómo se carga",
        "",
        "`etl bd` no calcula nada: inserta estos archivos. Tres reglas:",
        "",
        "| Regla | Por qué |",
        "| --- | --- |",
        "| `INSERT ... ON CONFLICT DO UPDATE` por clave de carga "
        "| Repetir la carga no duplica filas ni pierde correcciones |",
        "| Por lotes de unos 60.000 parámetros | PostgreSQL admite 65.535 por consulta |",
        "| Primero `empresa`, después el resto | Las demás tablas la referencian |",
        "",
        "Antes de cargar, `etl verificar` comprueba las mismas condiciones que",
        "impondrán las claves de PostgreSQL: claves únicas y cero filas huérfanas.",
        "Si algo no cuadra, falla ahí y no en la base.",
        "",
    ]

    texto = "\n".join(partes)
    (config.ETL / DESTINO).write_text(texto, encoding="utf-8")
    log.info("Documentado -> %s", config.ETL / DESTINO)
    return texto
