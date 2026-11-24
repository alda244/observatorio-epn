"""Línea de comandos del ETL: `etl <paso> --anio <año>`.

Cada paso es idempotente: repetirlo no duplica filas ni vuelve a visitar las
webs ya capturadas. El orden normal es

    ranking → financieros → universo → urls → web → ficha

por año, y después `consolidar` junta todos los años y `bd` los carga.
`etl todo` corre el año completo.
"""

from __future__ import annotations

import asyncio

import typer

from etl import config
from etl.common import configurar_registro, log

app = typer.Typer(
    add_completion=False,
    help="ETL del Componente B: cifras de la SCVS y Company Profile de cada empresa.",
)

OpcionAnio = typer.Option(config.ANIO_POR_DEFECTO, "--anio", "-a", help="Año del ejercicio fiscal.")
OpcionDetalle = typer.Option(False, "--detallado", "-d", help="Registro detallado.")


@app.callback()
def principal(detallado: bool = OpcionDetalle) -> None:
    configurar_registro(detallado)


@app.command()
def ranking(anio: int = OpcionAnio) -> None:
    """Ranking SCVS: de crudo a plata, con limpieza y reglas de calidad."""
    from etl.pipeline import ranking as paso

    paso.ejecutar(anio)


@app.command()
def financieros(anio: int = OpcionAnio) -> None:
    """Estados financieros por ramo: de crudo a plata."""
    from etl.pipeline import financials as paso

    paso.ejecutar(anio)


@app.command()
def universo(anio: int = OpcionAnio) -> None:
    """Universo, piloto y listas top 50: de plata a oro."""
    from etl.pipeline import universe as paso

    paso.ejecutar(anio)


@app.command()
def urls(
    anio: int = OpcionAnio,
    limite: int | None = typer.Option(
        None, "--limite", "-l", help="Empresas por criterio del piloto en esta corrida."
    ),
) -> None:
    """Busca y verifica la web oficial de las empresas del piloto."""
    from etl.pipeline import urls as paso

    asyncio.run(paso.ejecutar(anio, limite))


@app.command()
def web(
    anio: int = OpcionAnio,
    limite: int | None = typer.Option(None, "--limite", "-l", help="Sitios en esta corrida."),
) -> None:
    """Captura portada y páginas institucionales de las webs verificadas."""
    from etl.pipeline import web as paso

    asyncio.run(paso.ejecutar(anio, limite))


@app.command()
def ficha(anio: int = OpcionAnio) -> None:
    """Arma el Company Profile a partir de lo capturado."""
    from etl.pipeline import profile as paso

    paso.ejecutar(anio)


@app.command()
def consolidar(
    desde: int | None = typer.Option(
        None,
        "--desde",
        help=f"Primer año de la serie; por defecto {config.ANIO_MINIMO_COMPARABLE}.",
    ),
    anio_universo: int | None = typer.Option(
        None,
        "--anio-universo",
        help=f"Año que fija el universo; por defecto {config.ANIO_UNIVERSO} (docs/universo.md).",
    ),
) -> None:
    """Junta todos los años en las tablas que publicará la API."""
    from etl.pipeline import consolidate as paso

    paso.ejecutar(desde, anio_universo)


@app.command()
def bd(
    anio: int | None = typer.Option(
        None, "--anio", "-a", help="Año cuyos documentos capturados se cargan también."
    ),
    url: str | None = typer.Option(
        None, "--url", help="Cadena de conexión; por defecto ETL_BASE_DE_DATOS de etl/.env."
    ),
) -> None:
    """Carga en PostgreSQL lo que dejó `etl consolidar`."""
    from etl.pipeline import load as paso

    paso.ejecutar(anio, url)


@app.command()
def documentar() -> None:
    """Escribe database-contents.md con el contenido real del consolidado."""
    from etl.pipeline import document as paso

    paso.ejecutar()


@app.command()
def verificar(
    anio: int | None = typer.Option(
        None, "--anio", "-a", help="Un solo año; por defecto, todos los que tengan capa plata."
    ),
) -> None:
    """Comprueba que todo lo que produjo el ETL cuadra. Falla si algo no cuadra."""
    from etl.pipeline import verify as paso

    informe = paso.ejecutar(anio)
    if informe.fallas:
        raise typer.Exit(code=1)


@app.command()
def todo(
    anio: int = OpcionAnio,
    limite: int | None = typer.Option(
        None, "--limite", "-l", help="Empresas por tanda en urls y web."
    ),
    con_bd: bool = typer.Option(False, "--con-bd", help="Carga también en PostgreSQL."),
) -> None:
    """Corre el pipeline completo del año."""
    from etl.pipeline import (
        consolidate,
        financials,
        load,
        profile,
        ranking,
        universe,
        urls,
        verify,
        web,
    )

    ranking.ejecutar(anio)
    try:
        financials.ejecutar(anio)
    except FileNotFoundError as e:
        log.warning("Se omiten los estados financieros: %s", e)
    universe.ejecutar(anio)
    asyncio.run(urls.ejecutar(anio, limite))
    asyncio.run(web.ejecutar(anio, limite))
    profile.ejecutar(anio)
    consolidate.ejecutar()
    verify.ejecutar(anio)
    if con_bd:
        load.ejecutar(anio)


if __name__ == "__main__":
    app()
