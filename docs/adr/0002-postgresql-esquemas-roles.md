# 0002. Un PostgreSQL con esquemas y roles por componente

| Campo | Valor |
| --- | --- |
| Estado | Aceptado |
| Fecha | 2026-11-17 |
| Componente | Compartido |

## Contexto

A necesita una base vectorial y B una base relacional. Dos motores distintos duplican la operación y el costo. A no debe depender de la estructura interna de B.

## Decisión

Un solo PostgreSQL 16 con pgvector. B es dueño de sus esquemas con `rol_datos`; A es dueño del esquema `asistente` con `rol_asistente`. Ningún rol tiene permisos sobre los esquemas del otro: A obtiene los datos de B solo por la API.

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | Un solo servidor que respaldar y pagar |
| Positiva | B puede cambiar sus tablas sin romper a A mientras respete el contrato |
| Negativa | La extensión `vector` y los roles se configuran al crear la base |
