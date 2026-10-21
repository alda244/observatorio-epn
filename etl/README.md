# etl · Componente B

Dueño: Eduardo Muzo. Lleva las descargas oficiales de la SCVS al esquema `datos`: carga, calidad, indicadores, proyecciones y metadatos DCAT.

| Carpeta | Propósito |
| --- | --- |
| `datos/crudo/` | Descargas manuales versionadas por año y `MANIFEST.csv` |
| `src/etl/carga` | Lectura de archivos crudos y carga a `datos` |
| `src/etl/calidad` | Limpieza, normalización y reglas de calidad |
| `src/etl/indicadores` | Agregados por CIIU, tamaño y año |
| `src/etl/proyecciones` | Tendencias y proyecciones |
| `src/etl/catalogo` | Metadatos DCAT |
| `migraciones/` | Alembic del esquema `datos` (tabla de versiones en `datos`) |
| `notebooks/` | Exploración de series y evidencia de análisis |
| `tests/` | Pruebas con pytest |

## Stack

| Ámbito | Herramienta |
| --- | --- |
| Lenguaje | Python 3.12 |
| Paquetes | uv (`pyproject.toml` + `uv.lock`) |
| Base | SQLAlchemy Core + Alembic + psycopg 3 |
| Pruebas / lint | pytest + pytest-cov / ruff |

Dependencias previstas, que se agregan cuando se usen: pandas, openpyxl y odfpy (lectura de archivos), statsmodels (proyecciones) y rdflib (DCAT).

## Uso (PowerShell, desde la raíz)

```powershell
.\scripts\test.ps1 -Modulo etl                      # lint + pruebas
uv run --directory etl python -m etl                # hola mundo
uv run --directory etl alembic upgrade head         # migraciones (requiere la base local en marcha)
```

Antes de usar `alembic`, se cargan las variables de `.env` con `. .\scripts\comun.ps1; Import-Env`.
