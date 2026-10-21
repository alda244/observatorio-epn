# Registro de decisiones de arquitectura (ADR)

Cada decisión que cambia la estructura, el stack o el contrato se registra con la [plantilla](0000-plantilla.md). La numeración es global y el componente se indica en la tabla de cada ADR.

| Nº | Decisión | Componente | Estado |
| --- | --- | --- | --- |
| [0001](0001-monorepo.md) | Monorepo único con módulos independientes | Compartido | Aceptado |
| [0002](0002-postgresql-esquemas-roles.md) | Un PostgreSQL con un esquema y un rol por componente | Compartido | Aceptado |
| [0003](0003-contrato-primero.md) | Contrato OpenAPI primero | Compartido | Aceptado |
| [0004](0004-llm-interfaz-openai.md) | Acceso al LLM mediante una interfaz compatible con OpenAI | A | Aceptado (proveedor pendiente) |
| [0005](0005-widget-alineado-fragui.md) | Widget alineado con el stack de FragUI | A | Aceptado |
| — | Portal de datos: CKAN, propio o híbrido | B | Pendiente (Sprint 1 de B) |

## Reglas

| Regla | Detalle |
| --- | --- |
| Nombre | `NNNN-titulo-en-minusculas.md` |
| Inmutabilidad | Un ADR aceptado no se edita; se reemplaza con uno nuevo |
| Revisión | Los ADR compartidos requieren la aprobación del otro estudiante |
