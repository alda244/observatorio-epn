# API del Componente B

FastAPI publica los datos abiertos de Observatorio EPN. Se conecta a PostgreSQL
como `rol_api`, con acceso de lectura a las vistas de `public`.

## Desarrollo local

Desde la raíz, `docker compose up -d --build` carga los datos de desarrollo
y levanta la API en `http://127.0.0.1:8001/docs`. Consulta la
[guía del ETL](../etl/database.md) para ver qué incluye la copia.

Para ejecutar FastAPI directamente con `uv`, levanta la base y ejecuta la carga
con `docker compose up -d --build etl`, y luego, desde la raíz:

```sh
uv sync --directory api --locked
uv run --directory api uvicorn api.main:app --reload --port 8001
```

Abre `http://127.0.0.1:8001/docs` para probar las rutas.

- `GET /v1/empresas` lista empresas con filtros, orden y paginación. Usa
  `limit` (1–100, por defecto 50) y `offset`. `total` cuenta todas las empresas
  que cumplen los filtros.
- `GET /v1/empresas/{expediente}` devuelve identificación, cifras por
  ejercicio y ficha vigente, si existe. Devuelve HTTP 404 si el expediente
  queda fuera del universo.

Prueba el listado con `/v1/empresas?grupo=TEC&limit=5`.

El detalle obtiene la procedencia de `etl/datos/crudo/MANIFEST.csv`. Puedes
indicar otra ubicación del manifiesto con `API_RANKING_MANIFEST`.

La conexión local usa el puerto 5432. Para cambiarla, configura
`API_DATABASE_URL` con la conexión de `rol_api`.

```sh
uv run --directory api pytest
uv run --directory api ruff check .
```
