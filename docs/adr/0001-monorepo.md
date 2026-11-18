# 0001. Un solo repositorio con módulos independientes

| Campo | Valor |
| --- | --- |
| Estado | Aceptado |
| Fecha | 2026-11-17 |
| Componente | Compartido |

## Contexto

A y B se desarrollan en paralelo y dependen uno del otro a través de la API. Con repositorios separados, el contrato y los cambios que afectan a ambos se desincronizan.

## Decisión

Un solo repositorio, `observatorio-epn`, con una carpeta por módulo (`etl/`, `api/`, `portal-datos/`, `rag/`, `widget/`) y carpetas compartidas (`docs/`, `contracts/`, `infra/`). Cada módulo tiene sus propias dependencias y pruebas.

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | El contrato y los dos lados que lo usan cambian en el mismo PR |
| Positiva | Una sola documentación y un solo historial para la memoria |
| Negativa | Lo compartido necesita la revisión de ambos estudiantes |
