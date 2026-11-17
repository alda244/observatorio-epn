# Componente A · Asistente

Asistente conversacional que responde preguntas sobre las empresas del Observatorio y cita la fuente de cada dato. Atiende dos tipos de consulta: sobre una empresa concreta ("¿qué hace Telconet?") y de directorio ("¿qué empresas desarrollan software en Cuenca?"). Se usa desde un widget embebido en el portal, sin registro.

```mermaid
flowchart LR
    B[(API de B)] --> I[Ingesta]
    I --> X[(Índice)]
    P[Pregunta] --> M[Motor]
    X --> M
    B -- cifras --> M
    M --> R[Respuesta con citas]
    M --> T[(Traza)]
```

## Estado

| Sprint | Objetivo | Estado |
| --- | --- | --- |
| 1 | Investigación, arquitectura, corpus y protocolo de evaluación | En curso |
| 2 | Ingesta, fragmentación e índice | Prototipo funcional |
| 3 | Motor RAG con citación y API `/chat` | Pendiente |
| 4 | Widget | Pendiente |
| 5 | Salvaguardas | Pendiente |
| 6 | Integración con la API de B | Pendiente |
| 7 | Evaluación con al menos 30 usuarios | Pendiente |
| 8 | Despliegue | Pendiente |
| 9 | Memoria del TIC | Pendiente |

## Documentos

| Documento | Contenido |
| --- | --- |
| [asistente.md](asistente.md) | Cómo funciona el asistente y sus reglas |
| [evaluacion.md](evaluacion.md) | Resultados del prototipo y comparación de LLM |
| [herramientas.md](herramientas.md) | Stack del componente |
| [plan.md](plan.md) | Pendientes por sprint y dependencias con B |
| [evidencias.md](evidencias.md) | Registro de evidencias `EV-A` |

Lo compartido con B (universo, ficha, arquitectura, infraestructura) está en [`docs/`](../README.md).
