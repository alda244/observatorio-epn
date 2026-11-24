# Repository Guidelines

## Project structure

This directory contains Component B’s Python ETL. Run ETL commands from `etl/`. The Typer CLI lives in `src/etl/cli.py`, pipeline steps in `src/etl/pipeline/`, and database models in `src/etl/bd/`. Keep reusable logic in the package and import it from `notebooks/`. Tests live in `tests/`. Data layers live under `datos/`. At the repository root, `docs/` holds project decisions, `contracts/` holds the API contract, and `infra/postgres/` holds PostgreSQL initialization.

## Development commands

- `uv sync --locked` installs the locked dependencies with Python 3.12.
- `uv run etl --help` lists commands. Use `uv run etl ranking --anio 2025` to run one stage against the 2025 exercise.
- `uv run etl consolidar` rebuilds consolidated outputs. Run `uv run etl verificar` to check the artifacts on disk.
- `uv run ruff check .` checks lint and import order. Run `uv run ruff format --check .` to check formatting.
- `uv run pytest --cov=etl --cov-report=term-missing` runs the suite and reports coverage as CI does.

## Style and testing

Use four-space indentation, snake_case for Python functions and modules, and Ruff’s configured 100-character line length. Follow existing Spanish names for SCVS fields and ETL steps. Keep stage commands idempotent. Put regression tests in `tests/test_<module>.py` with descriptive `test_*` names. Use local fixtures for data and HTTP behavior. Run `uv run pytest tests/test_consolidate.py` for a focused check.

## Data and configuration

Keep the universe fixed to the 2025 ranking and published fiscal years within 2012–2025. Limit company-profile collection to the 500-company pilot and follow the shared robots and rate-limit rules in `src/etl/crawling.py`. Keep credentials in an ignored local `.env` and use the root `.env.example` as a template.

## Commits and pull requests

Follow the history’s Spanish Conventional Commit style, such as `fix(etl): validar el consolidado`. Omit Claude attribution from commits and PRs. In PRs, describe the change, list the checks you ran, and call out changes to data outputs or contracts. Link related issues or ADRs when applicable.
