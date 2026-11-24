# Base de datos del Componente B

El ETL consolida las cifras de la SCVS y las fichas de empresa en `datos/oro/`.
La capa intermedia `datos/plata/` se conserva en Parquet. PostgreSQL publica
los datos de B en el esquema `public`.

## Tablas y vistas

| Tabla | Clave | Vista para la API |
| --- | --- | --- |
| `empresa` | `expediente` | `public.v_empresa` |
| `cifras_anuales` | `expediente, anio` | `public.v_cifras_anuales` |
| `ficha` | `expediente, fecha_captura` | `public.ficha_vigente`, captura más reciente por empresa |
| `documento` | `id`; único por `expediente, sha256` | `public.v_documento` |
| `indicador_sector` | `anio, seccion_ciiu, indicador` | `public.v_indicador_sector` |

El ranking fiscal 2025 fija el universo de 14.029 empresas. `empresa` conserva
`grupo`, `en_piloto`, `criterio_piloto` y `en_top50_tec`. `cifras_anuales`
cubre los ejercicios 2012–2025 y registra si cada empresa cumplió la delimitación
de su ejercicio en `en_universo_ese_anio`.

PostgreSQL exige un motivo válido cuando `tiene_alerta` es verdadero y un
motivo nulo cuando es falso. Las cifras, fichas y documentos referencian
`empresa` con `ON DELETE RESTRICT`.

`en_piloto` identifica la selección fija de 500 empresas. `v_empresa` deriva
`estado_ficha` de la captura vigente. Traduce `completo` a `completa` y
`parcial` a `parcial`. Una ficha pendiente o ausente se publica como
`sin_ficha`.

## Migrar y cargar

El script de inicialización de PostgreSQL crea los roles y concede acceso a `public`.
`rol_datos` aplica las migraciones y carga el consolidado. `rol_api` tiene
`USAGE` sobre `public` y `SELECT` explícito sobre las cinco vistas.

## Ejecutar localmente

Desde la raíz del repositorio, con el consolidado ya generado en `etl/datos/oro/`:

```sh
docker compose up -d --build
docker compose logs -f etl
```

Compose inicia PostgreSQL y espera a que acepte conexiones. Luego el servicio
`etl` aplica la migración y carga los datos, incluidos los documentos de 2025.
La carga termina y PostgreSQL sigue corriendo. El ETL lee los archivos del
equipo anfitrión a través de un montaje de solo lectura.

El ETL en Docker usa `db:5432` en la red de Compose. Si ejecutas comandos de
base de datos con `uv` desde tu equipo, usa `etl/.env.example` como plantilla
para `etl/.env` y conéctate a `127.0.0.1:5432`.

`etl bd` actualiza filas por clave dentro de una transacción. Con `--anio`
incluye los documentos web de ese ejercicio. El inventario generado a partir
del consolidado está en [database-contents.md](database-contents.md).
