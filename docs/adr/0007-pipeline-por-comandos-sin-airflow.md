# 0007. Pipeline ETL por comandos, en capas Medallion y sin Airflow

| Campo | Valor |
| --- | --- |
| Estado | Propuesto |
| Fecha | 2026-11-03 |
| Componente | B |
| Decisores | Eduardo Miguel Muzo Cansigña (propone), Alicia Pereira (revisa) |
| Issue / PR | Pendiente |

## Contexto

El ETL de B procesa el ranking SCVS (anual) y las webs y PDF oficiales de las empresas (por campaña). El TIC de Defaz (EPN, 2026) usó Airflow con más de 30 DAG para 5 instituciones. La investigación de B propone capas bronce, plata y oro y un pipeline `python -m etl <paso>` ([`../investigacion-b/05`](../investigacion-b/05-arquitectura-y-pipeline.md)).

## Opciones consideradas

| Opción | A favor | En contra |
| --- | --- | --- |
| Airflow | Estándar de la industria; precedente en la EPN | Servidor, base de metadatos y workers para una carga anual |
| Prefect o Dagster | Orquestación más liviana que Airflow | Dependencia extra sin necesidad actual |
| **Comandos `etl <paso>` idempotentes + GitHub Actions** | Sin infraestructura adicional; se prueba igual en local y en la CI | Sin interfaz de monitoreo; la secuencia la define quien ejecuta |

## Decisión

Propuesta: pipeline por comandos idempotentes (`carga`, `calidad`, `universo`, `web`, `texto`, `ficha`, `indicadores`, `catalogo`), con datos organizados en bronce (crudo inmutable), plata (limpio) y oro (publicado). Prefect o Dagster quedan como evolución sobre los mismos comandos si la frecuencia crece.

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | Cero costo operativo extra; cada paso se prueba con pytest |
| Positiva | El mismo contenedor corre en local, EPN o AWS ([`../investigacion-b/07`](../investigacion-b/07-alternativa-aws.md)) |
| Negativa | La programación anual depende de `schedule` en GitHub Actions o de ejecución manual |
| Seguimiento | Compatibilizar las capas con el [ADR 0002](0002-postgresql-esquemas-roles.md) (un esquema y un rol por componente): esquemas `bronce`/`plata`/`oro` propiedad de `rol_datos`, o tablas con prefijo dentro de `datos` |
| Seguimiento | Fijar la CLI (typer o argparse) en el primer sprint del ETL |
