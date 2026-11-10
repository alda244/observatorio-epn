# Sprints del Componente A

Seguimiento de los sprints del plan F_AA_234A. Cada sprint enlaza sus entregables y evidencias (`EV-A-NNN`, en [`../evidencias/registro.md`](../../evidencias/registro.md)).

| Sprint | Objetivo | Estado | Entregables | Evidencias |
| --- | --- | --- | --- | --- |
| 1 | Investigación, arquitectura, corpus y protocolo | En curso | Investigación 01–13, universo aprobado y piloto de 500, RN-01 y RN-02 | EV-A-001 a EV-A-004 |
| 2 | Pipeline de ingesta, fragmentación e indexación | **Prototipo adelantado** | Prototipo en [`rag/`](../../../rag/README.md): ingesta idempotente, índice, motor con cita, evaluación de 30 preguntas | EV-A-005 |
| 3 | Motor RAG con citación | Pendiente | — | — |
| 4 | Interfaz conversacional (widget) | Pendiente | — | — |
| 5 | Salvaguardas | Pendiente | — | — |
| 6 | Integración con la API de B | Pendiente | — | — |
| 7 | Evaluación con ≥ 30 usuarios | Pendiente | — | — |
| 8 | Despliegue | Pendiente | — | — |
| 9 | Informe final | Pendiente | — | — |

## Pendientes del Sprint 1

| Pendiente | Estado |
| --- | --- |
| Revisión bibliográfica formal de RAG | Falta |
| Casos de uso del asistente | Falta (las 30 preguntas del prototipo sirven de punto de partida) |
| Protocolo de evaluación (50 preguntas, métricas, SUS) | Falta |
| Comparación de LLM con preguntas reales | Falta |
| ADR 0001–0005 | Falta |

## Pendientes del Sprint 2 que deja el prototipo

| Pendiente | Motivo |
| --- | --- |
| Almacén pgvector en el esquema `asistente` | El prototipo guarda el índice en archivos |
| Cambiar a BGE-M3 y recalibrar los umbrales | El prototipo usa MiniLM multilingüe |
| Ingerir textos del Company Profile cuando B los exponga | Hallazgos H2 y H3 de [`rag/evidencias`](../../../rag/evidencias/README.md) |
| Configurar `uv` y CI | uv no está instalado en el equipo de desarrollo |
