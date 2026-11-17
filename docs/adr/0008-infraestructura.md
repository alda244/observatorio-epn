# 0008. Docker Compose en local y en AWS, LLM por API

| Campo | Valor |
| --- | --- |
| Estado | Aceptado |
| Fecha | 2026-11-03 |
| Componente | Compartido |

## Contexto

La EPN dispone de una cuenta AWS. El asistente necesita un LLM y embeddings; B necesita ejecutar el ETL y publicar la API. Se busca el menor costo y el mismo entorno en local y en producción.

| Opción | A favor | En contra |
| --- | --- | --- |
| LLM propio en EC2 con GPU | Control del modelo | Más de USD 300 al mes |
| Servicios gestionados (Fargate, ALB, Bedrock) | Escala con el uso | Más piezas que operar |
| **EC2 con Docker Compose, RDS, S3 y LLM por API** | Mismo entorno en local y AWS; USD 88–135 al mes | Un solo servidor |

## Decisión

Desarrollo local con Docker Compose. Producción en `us-east-1` con una EC2 `t4g.large`, RDS PostgreSQL 16 `db.t4g.small` con pgvector, S3 con versionado y el LLM por API. Tope de USD 150 al mes. Los embeddings corren en CPU. Detalle en [infraestructura.md](../infraestructura.md).

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | No hace falta GPU |
| Positiva | Cambiar de proveedor de LLM es un cambio de configuración |
| Negativa | Sin alta disponibilidad; se acepta para un servicio académico |
