# 0008. Infraestructura de desarrollo y despliegue con LLM por API

| Campo | Valor |
| --- | --- |
| Estado | Propuesto |
| Fecha | 2026-11-03 |
| Componente | Compartido |
| Decisores | Alicia Dayana Pereira Tuqueres (propone), Eduardo Miguel Muzo Cansigña (revisa), director |
| Issue / PR | Pendiente |

## Contexto

La EPN adquirió infraestructura AWS y se requiere dimensionar los requerimientos. La investigación de A proponía servicios gestionados en AWS; la de B, local y EPN por defecto ([10](../investigacion/10-coherencia-con-componente-b.md), I3). El plan F_AA_234A de A fija un LLM de bajo costo por interfaz compatible con OpenAI y BGE-M3 en ejecución local. El detalle está en [`../investigacion/07`](../investigacion/07-infraestructura-aws.md).

## Opciones consideradas

| Opción | A favor | En contra |
| --- | --- | --- |
| Modelo autoalojado en EC2 con GPU | Control total del modelo | Costo fijo superior a USD 300 al mes; mantenimiento |
| Servicios gestionados completos (ECS Fargate, ALB, RDS, Bedrock) | Escala con el uso | Más piezas que operar y documentar; costo fijo del balanceador |
| **EC2 con Docker Compose + RDS + S3 + LLM por API** | Mismo artefacto en local, EPN y AWS; respaldos gestionados de la base; USD 88–135 al mes | Un solo servidor de aplicación, sin alta disponibilidad |

## Decisión

Propuesta: desarrollo local con Docker Compose y producción en la cuenta AWS de la EPN (`us-east-1`) con una EC2 `t4g.large`, RDS PostgreSQL 16 `db.t4g.small` con pgvector compartido por A y B, un bucket S3 con versionado y el LLM por API. El proveedor del LLM es Amazon Bedrock cuando el modelo elegido en la evaluación del sprint 1 está disponible ahí; en caso contrario, la API del proveedor con cuenta institucional y tope de gasto. Los embeddings se calculan con BGE-M3 en CPU.

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | No requiere GPU; el costo del LLM en el pico de evaluación es de USD 3–50 al mes |
| Positiva | B ejecuta sus comandos ETL en la misma instancia, en coherencia con el ADR 0007 |
| Negativa | La disponibilidad depende de una sola EC2; se acepta para un servicio académico |
| Seguimiento | Verificar precios en AWS Pricing Calculator antes de la solicitud formal |
| Seguimiento | Confirmar qué modelos de Bedrock admiten el endpoint compatible con OpenAI |
| Seguimiento | Registrar el modelo elegido en un ADR que complete el ADR 0004 |
