FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY src/ src/
RUN uv sync --locked --no-dev

CMD ["uv", "run", "--no-sync", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
