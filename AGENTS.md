# Repository Guidelines

## Project Structure

Observatorio EPN is a monorepo for an Ecuadorian company directory and conversational assistant. Component B owns the ETL (`etl/`), public API (`api/`), and data portal (`portal-datos/`). Component A owns the assistant (`rag/`) and widget (`widget/`).

- `etl/src/etl/` contains the Typer CLI, pipeline stages in `pipeline/`, and database code in `bd/`. Tests live in `etl/tests/`, data in `etl/datos/`, and notebooks in `etl/notebooks/`. Import reusable pipeline logic from the package in notebooks.
- `rag/` has its own Python project and tests. `contracts/` is the shared API contract directory, `docs/adr/` records decisions, and `infra/postgres/init/` initializes local PostgreSQL.

## Development and Testing

Run these commands from `etl/` with Python 3.12 and uv.

- `uv sync --locked` installs the locked dependencies.
- `uv run etl --help` lists the CLI commands. Use `uv run etl ranking --anio 2025` to process one fiscal year and `uv run etl verificar` to validate on-disk outputs.
- `uv run ruff check .` and `uv run ruff format --check .` check lint and formatting.
- `uv run pytest --cov=etl --cov-report=term-missing` runs the ETL suite and reports coverage as CI does. Use `uv run pytest tests/test_consolidate.py` for a focused check.

From the repository root, `docker compose up -d db` starts PostgreSQL. Use `.env.example` as a template and keep credentials in the ignored local `.env`.

## Coding and Data Conventions

Use four-space indentation, `snake_case` for Python modules and functions, and Ruff’s 100-character ETL line length. Preserve Spanish domain names and keep pipeline stages idempotent. Name pytest files `test_<module>.py` and functions `test_*`. Use local fixtures for data and HTTP behavior.

Keep the company universe fixed to the 2025 ranking and publish fiscal years 2012–2025. Limit company-profile scraping to the 500-company pilot and follow the collection rules in `etl/src/etl/crawling.py`.

## Commits and Pull Requests

Use Spanish Conventional Commit subjects such as `fix(etl): validar el consolidado`. Omit Claude attribution from commits and PRs. Describe changes and checks run in the PR, flag changes to data outputs or contracts, and link relevant issues or ADRs. Include affected consumers in contract changes and get both students’ review for shared changes.
