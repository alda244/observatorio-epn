# 8. Plan y agenda de negociación

## Decisiones para la reunión con el director

| Nº | Pregunta | Opciones | Propuesta |
| --- | --- | --- | --- |
| 1 | ¿Cuántas empresas llevan Bloque 2? | Universo (14.042) · piloto (~500) · solo tecnológicas | Piloto de ~500 ([01](01-fuentes-y-universo.md)) |
| 2 | ¿Quién produce el Bloque 2? | A · B | B, servido por `/empresas/{expediente}`; requiere ADR y cambio de contrato |
| 3 | ¿Cómo obtener el segmento oficial de tamaño? | Derivar por ventas · pedirlo a la SCVS | Derivar ahora y pedirlo en el convenio EPN–SCVS |
| 4 | ¿Se acepta texto `derivado` (redactado) además del `literal`? | Solo literal · ambos marcados | Ambos, marcados ([02](02-company-profile-bloque2.md)) |
| 5 | ¿Airflow o pipeline por comandos? | Airflow · comandos + CI | Comandos + CI ([05](05-arquitectura-y-pipeline.md)) |
| 6 | ¿Infraestructura? | Local/EPN · AWS | Local/EPN; AWS como alternativa ([07](07-alternativa-aws.md)) |

## Ubicación en el plan F_AA_234A

| Sprint | Tarea del plan | Aporte de esta investigación |
| --- | --- | --- |
| 1 | Estándares, alternativas, modelo inicial | Universo, fuentes, esquema `ficha_contenido`, ADR del pipeline |
| 2 | ETL: limpieza, normalización, calidad | `etl carga`, `etl calidad`, reglas de [01](01-fuentes-y-universo.md) |
| 3 | Portal y catálogo | Bloque 2 visible por empresa |
| 4 | API pública | Campos del Bloque 2 en `/empresas/{expediente}` |
| 5 | Analítica e indicadores | `etl indicadores`, proyecciones |
| 6 | Integración con la plataforma | Consumo desde el asistente de A |
| 7 | Publicación con metadatos y licencia | Catálogo DCAT del universo y de las fichas |
| 8 | Pruebas y despliegue | CI, pruebas del spider, alternativa AWS |
| 9 | Informe final | Evidencia del piloto y de calidad |

## Próximos pasos

| Tarea | Responsable | Entregable |
| --- | --- | --- |
| Versionar el ranking 2025 en `etl/datos/crudo/2025/` con su fila en `MANIFEST.csv` | Muzo | Archivo crudo + hash |
| Generar el subconjunto piloto (~500) desde `universo_bloque2.csv` | Muzo | `piloto_500.csv` |
| Encontrar y verificar las URL del piloto | Muzo | Columnas `url_*` llenas |
| Correr el spider desde la red de la EPN | Muzo | `bronce/manifest.jsonl` |
| Redactar el ADR "Pipeline por comandos sin Airflow" y el de "Bloque 2 en B" | Muzo, revisión de Pereira | 2 ADR |
| Proponer los campos del Bloque 2 en `contracts/openapi.yaml` | Muzo, Pereira | PR al contrato |
