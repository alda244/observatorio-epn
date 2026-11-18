"""Línea de comandos del ETL: `etl <paso> --anio <año>`.

Cada paso es idempotente: repetirlo no duplica filas ni vuelve a visitar las
webs ya capturadas. El orden normal es

    ranking → financieros → universo → urls → web → ficha → bd

y `etl todo` lo corre completo.
"""

from __future__ import annotations

import asyncio

import typer

from etl import config
from etl.comun import configurar_registro, log

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
    from etl.pasos import ranking as paso

    paso.ejecutar(anio)


@app.command()
def financieros(anio: int = OpcionAnio) -> None:
    """Estados financieros por ramo: de crudo a plata."""
    from etl.pasos import financieros as paso

    paso.ejecutar(anio)


@app.command()
def universo(anio: int = OpcionAnio) -> None:
    """Universo, piloto y listas top 50: de plata a oro."""
    from etl.pasos import universo as paso

    paso.ejecutar(anio)


@app.command()
def urls(
    anio: int = OpcionAnio,
    limite: int | None = typer.Option(
        None, "--limite", "-l", help="Empresas por criterio del piloto en esta corrida."
    ),
) -> None:
    """Busca y verifica la web oficial de las empresas del piloto."""
    from etl.pasos import urls as paso

    asyncio.run(paso.ejecutar(anio, limite))


@app.command()
def web(
    anio: int = OpcionAnio,
    limite: int | None = typer.Option(None, "--limite", "-l", help="Sitios en esta corrida."),
) -> None:
    """Captura portada y páginas institucionales de las webs verificadas."""
    from etl.pasos import web as paso

    asyncio.run(paso.ejecutar(anio, limite))


@app.command()
def ficha(anio: int = OpcionAnio) -> None:
    """Arma el Company Profile a partir de lo capturado."""
    from etl.pasos import ficha as paso

    paso.ejecutar(anio)


@app.command()
def bd(
    anio: int = OpcionAnio,
    url: str | None = typer.Option(
        None, "--url", help="Cadena de conexión; por defecto ETL_BASE_DE_DATOS."
    ),
) -> None:
    """Carga la capa oro en PostgreSQL."""
    from etl.pasos import carga as paso

    paso.ejecutar(anio, url)


@app.command()
def todo(
    anio: int = OpcionAnio,
    limite: int | None = typer.Option(
        None, "--limite", "-l", help="Empresas por tanda en urls y web."
    ),
    con_bd: bool = typer.Option(False, "--con-bd", help="Carga también en PostgreSQL."),
) -> None:
    """Corre el pipeline completo del año."""
    from etl.pasos import carga, ficha, financieros, ranking, universo, urls, web

    ranking.ejecutar(anio)
    try:
        financieros.ejecutar(anio)
    except FileNotFoundError as e:
        log.warning("Se omiten los estados financieros: %s", e)
    universo.ejecutar(anio)
    asyncio.run(urls.ejecutar(anio, limite))
    asyncio.run(web.ejecutar(anio, limite))
    ficha.ejecutar(anio)
    if con_bd:
        carga.ejecutar(anio)


if __name__ == "__main__":
    app()
