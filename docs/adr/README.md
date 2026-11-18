# Decisiones de arquitectura (ADR)

Cada decisión que cambia la estructura, el stack o el contrato se registra con la [plantilla](plantilla.md). La numeración es global; los ADR de un solo componente viven en la rama de ese componente.

| Nº | Decisión | Componente | Estado |
| --- | --- | --- | --- |
| [0001](0001-monorepo.md) | Un solo repositorio con módulos independientes | Compartido | Aceptado |
| [0002](0002-postgresql-esquemas-roles.md) | Un PostgreSQL con esquemas y roles por componente | Compartido | Aceptado |
| [0003](0003-contrato-primero.md) | Contrato OpenAPI antes que el código | Compartido | Aceptado |
| [0006](0006-bloque2-company-profile-en-b.md) | B recolecta las webs y produce el Company Profile | Compartido | Aceptado |
| [0008](0008-infraestructura.md) | Docker Compose en local y en AWS, LLM por API | Compartido | Aceptado |

Un ADR aceptado no se edita: se reemplaza con uno nuevo.
