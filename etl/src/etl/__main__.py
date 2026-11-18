"""Permite `python -m etl <paso>` además del comando `etl`."""

from etl.cli import app

if __name__ == "__main__":
    app()
