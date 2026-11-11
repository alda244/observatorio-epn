# etl · Componente B

Dueño: Eduardo Muzo. Lleva las descargas oficiales de la SCVS y las webs oficiales de las empresas a datos limpios y publicables, con la metodología Medallion: carga, calidad, universo, Company Profile (Bloque 2), indicadores, proyecciones y metadatos DCAT.

Alcance y decisiones propuestas: [`docs/investigacion-b/`](../docs/investigacion-b/README.md). En revisión: pipeline por comandos en capas Medallion ([ADR 0007](../docs/adr/0007-pipeline-por-comandos-sin-airflow.md)) y recolección del Bloque 2 del Company Profile ([ADR 0006](../docs/adr/0006-bloque2-company-profile-en-b.md)).

## Capas de datos (Medallion)

```
datos/
├── crudo/      bronce: tal como llega, nunca se edita
│   ├── 2025/          descargas oficiales de la SCVS
│   ├── web/           páginas de las webs oficiales + manifest.jsonl
│   └── MANIFEST.csv   procedencia y hash de cada descarga
├── plata/      limpio y validado
├── oro/        listo para publicar
└── universo/   selección inicial del Componente A (09-nov-2026), sin cambios
```

En git van los manifiestos, los CSV y los reportes; no van los parquet ni los HTML (se regeneran) ni `bi_compania.csv` (54 MB; su hash queda en el MANIFEST).

## Notebooks

| Notebook | Capa | Qué hace |
| --- | --- | --- |
| [`01_exploracion_ranking`](notebooks/01_exploracion_ranking.ipynb) | Crudo | Procedencia por hash, completitud, duplicados, cifras extremas y caso de empleados |
| [`02_bronce_a_plata`](notebooks/02_bronce_a_plata.ipynb) | Crudo → Plata | Limpieza, CIIU, tamaño derivado, alerta de empleados con causa, RUC y validación con pandera |
| [`03_plata_a_oro`](notebooks/03_plata_a_oro.ipynb) | Plata → Oro | Universo, piloto de 500 y top 50 (RN-02), con validación cruzada contra la selección de A |
| [`04_urls_oficiales`](notebooks/04_urls_oficiales.ipynb) | Plata | Dominios candidatos + PeeringDB, filtro DNS y verificación ética con Scrapling |
| [`05_captura_web`](notebooks/05_captura_web.ipynb) | Crudo | Portada y páginas institucionales de las webs verificadas, con metadatos y PDF candidatos |
| [`06_ficha_bloque2`](notebooks/06_ficha_bloque2.ipynb) | Crudo → Plata | Tagline, descripción y productos/servicios del Company Profile, con su fuente |

Los notebooks 04 y 05 corren por tandas (`LIMITE_POR_CRITERIO`) y no repiten lo ya verificado o capturado.

## Stack

| Ámbito | Herramienta |
| --- | --- |
| Lenguaje | Python 3.12 |
| Paquetes | uv (`pyproject.toml` + `uv.lock`), proyecto propio de este módulo |
| Datos | pandas + python-calamine (Excel/ODS) + pyarrow (parquet) |
| Calidad | pandera |
| Recolección web | Scrapling (configuración ética), extruct, trafilatura, pdfplumber, rapidfuzz |
| Base (pipeline) | SQLAlchemy Core + Alembic + psycopg 3 |
| Pruebas / lint | pytest / ruff |

## Uso (desde `etl/`)

```bash
uv sync   # crea etl/.venv con las dependencias y el grupo dev (incluye ipykernel)
```

En VS Code se abren los `.ipynb` de `notebooks/` y se elige el kernel `etl/.venv/bin/python`.
```
