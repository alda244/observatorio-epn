# 0003. Contrato OpenAPI antes que el código

| Campo | Valor |
| --- | --- |
| Estado | Aceptado |
| Fecha | 2026-11-17 |
| Componente | Compartido |

## Contexto

A consume la API de B, pero los dos se construyen al mismo tiempo. A no puede esperar a que B termine para desarrollar.

## Decisión

El contrato se escribe primero en `contracts/openapi.yaml` (OpenAPI 3.1). B lo implementa y A lo consume. Mientras la API de B no exista, A usa un servidor simulado generado desde el contrato.

| Cambio | Versión |
| --- | --- |
| Campo opcional o ruta nueva | Menor |
| Cambio incompatible | Mayor, con ADR |

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | A y B avanzan en paralelo |
| Positiva | El contrato documenta la API para terceros |
| Negativa | Cada cambio de la API pasa primero por el contrato |
