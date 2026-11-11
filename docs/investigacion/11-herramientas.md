# 11. Herramientas del Componente A

Corte: 03-nov-2026. Se listan las herramientas del Componente A por ámbito, con su función y el origen de la decisión. Las compartidas con B se marcan en la última columna.

## Gestión del proyecto y trazabilidad

| Herramienta | Función | Origen | Compartida |
| --- | --- | --- | --- |
| Scrum | Marco de trabajo: Product Backlog, sprints e incrementos verificables | Plan F_AA_234A | Sí |
| Linear | Backlog, sprints (ciclos), épicas (proyectos) y métricas de avance | Decisión del equipo; [configuración](#configuración-de-linear) | Sí |
| GitHub (`alda244/observatorio-epn`) | Código, revisión por PR, CODEOWNERS, issues de cambio de contrato | ADR 0001 | Sí |
| GitHub Actions + `dorny/paths-filter` | CI por módulo | Arquitectura del monorepo | Sí |
| `docs/sprints/A/` y `docs/evidencias/A/` | Informe de sprint y registro de evidencias `EV-A-NNN` | Convenciones de `docs/` | No |

## Backend, RAG y datos

| Herramienta | Función | Origen |
| --- | --- | --- |
| Python 3.12 + uv | Lenguaje y gestión de dependencias | Plan F_AA_234A; ADR 0001 |
| FastAPI + uvicorn | API `/chat` y `/salud` | Plan F_AA_234A |
| LlamaIndex | Fragmentación, recuperación y orquestación del RAG | Plan F_AA_234A |
| BGE-M3 (`FlagEmbedding` o `sentence-transformers`) | Embeddings multilingües densos y dispersos en CPU | Plan F_AA_234A; Chen et al. (2024) |
| PostgreSQL 16 + pgvector | Índice vectorial y tablas de trazabilidad en el esquema `asistente` | ADR 0002 |
| SQLAlchemy Core + Alembic + psycopg 3 | Acceso a la base y migraciones | Stack del monorepo |
| Cliente `openai` | Interfaz única hacia el LLM, sea Bedrock u otro proveedor | ADR 0004; ADR 0008 |
| httpx | Cliente de la API de B (`src/rag/cliente_b`) | Arquitectura del monorepo |
| pydantic-settings | Configuración por variables de entorno | Buenas prácticas de FastAPI |

## Calidad, evaluación y trazabilidad

| Herramienta | Función | Origen |
| --- | --- | --- |
| pytest + pytest-cov | Pruebas unitarias e integración con LLM, embeddings y API de B simulados | `rag/README.md` |
| ruff | Lint y formato | `rag/README.md` |
| RAGAS | Métricas de fidelidad, pertinencia y precisión de contexto | Plan F_AA_234A; Es et al. (2024) |
| Escala SUS | Usabilidad percibida con al menos 30 usuarios | Plan F_AA_234A; Brooke (1996) |
| Tabla `asistente.traza` | Registro propio por respuesta: pregunta, fragmentos, fuentes, modelo, tokens, latencia | Plan F_AA_234A (trazabilidad) |
| Langfuse | Visualización de trazas en desarrollo; complementa la tabla propia | Plan F_AA_234A |
| Locust | Pruebas de rendimiento y carga del endpoint `/chat` | Plan F_AA_234A, sprint 8 |

## Contrato e integración

| Herramienta | Función | Compartida |
| --- | --- | --- |
| OpenAPI 3.1 (`contracts/openapi.yaml`) | Contrato entre A, B y el widget | Sí |
| Spectral | Validación del contrato en la CI | Sí |
| Prism | API simulada de B para desarrollar A sin depender de B | Sí |

## Widget

| Herramienta | Función | Origen |
| --- | --- | --- |
| React 19 + TypeScript | Widget embebible | ADR 0005 (alineación con FragUI) |
| tsup | Empaquetado del widget | ADR 0005 |
| Storybook | Documentación visual de componentes | ADR 0005 |
| Vitest + axe-core | Pruebas y accesibilidad WCAG 2.1 AA | ADR 0005 |
| ESLint 9 + Prettier | Lint y formato | ADR 0005 |

## Infraestructura

| Herramienta | Función | Origen | Compartida |
| --- | --- | --- | --- |
| Docker + Docker Compose | Mismo entorno en local, EPN y AWS | Plan F_AA_234A; ADR 0008 | Sí |
| AWS EC2, RDS, S3 | Cómputo, base y archivos | ADR 0008 | Sí |
| Amazon Bedrock | LLM por API dentro de la cuenta de la EPN | ADR 0008 | Sí |
| Caddy | TLS y proxy inverso | ADR 0008 | Sí |
| AWS Systems Manager Parameter Store | Secretos | ADR 0008 | Sí |
| AWS Budgets | Tope y alertas de costo | ADR 0008 | Sí |
| Ollama (opcional) | Modelo abierto local para desarrollo sin costo | Plan F_AA_234A (alternativa local) | No |

## Documentación y memoria

| Herramienta | Función |
| --- | --- |
| Markdown + Mermaid en `docs/` | Documentación viva junto al código |
| MkDocs Material (por decidir en ADR) | Publicación de `docs/` como sitio web, según el precedente de FragUI ([RN-01](../reuniones/RN-01-ficha-alcance-antecedentes.md), P4) |
| Zotero | Gestión de referencias en formato IEEE |
| Plantilla oficial EPN | Memoria del TIC |
| Declaración de uso de IA | Sección de certificaciones de la memoria, según el patrón del Data Hub ([09](09-antecedentes-reinoso-datahub.md)) |

## Configuración de Linear

| Elemento de Linear | Uso en el proyecto | Valor |
| --- | --- | --- |
| Espacio de trabajo | Proyecto completo | `Observatorio EPN` |
| Equipos | Uno por componente, porque cada plan F_AA_234A tiene sus propios sprints | `ASI` (Asistente, A) y `DAT` (Datos, B) |
| Ciclos | Sprints del plan | 9 ciclos por equipo, de 4 semanas |
| Proyectos | Épicas alineadas con los objetivos específicos | Ver tabla siguiente |
| Estados | Flujo Scrum | Backlog → Sprint Backlog → En curso → En revisión → Hecho · Cancelado |
| Estimación | Puntos de historia | Fibonacci (1, 2, 3, 5, 8) |
| Etiquetas de tipo | Clasificación de issues | `historia`, `tarea`, `investigación`, `documentación`, `evidencia`, `bug`, `adr` |
| Etiquetas de módulo | Carpeta del monorepo afectada | `rag`, `widget`, `contracts`, `infra`, `docs` |
| Etiqueta transversal | Issues que requieren al otro estudiante | `compartido` |
| Integración GitHub | Rama y PR enlazados al issue | Rama `asi-12-titulo`; PR con `Closes ASI-12` |

| Proyecto (épica) de `ASI` | Objetivo específico del plan | Sprint |
| --- | --- | --- |
| Investigación y arquitectura | Analizar enfoques y alternativas tecnológicas | 1 |
| Corpus y protocolo de evaluación | Definir corpus, casos de uso y protocolo | 1 |
| Pipeline de ingesta e índice | Implementar ingesta e indexación semántica | 2 |
| Motor RAG con citación | Desarrollar el motor e integrarlo con B | 3, 6 |
| Widget conversacional | Desarrollar la interfaz web | 4 |
| Salvaguardas y trazabilidad | Mitigación de alucinaciones, filtros y registro | 5 |
| Evaluación con usuarios | Evaluar con al menos 30 usuarios | 7 |
| Despliegue y documentación | Desplegar en la EPN y documentar | 8 |
| Memoria del TIC | Informe final | 9 |
| Integración A–B (compartido con `DAT`) | Contrato, mock y pruebas de integración | 1–6 |

### Plantilla de historia de usuario

| Campo | Contenido |
| --- | --- |
| Título | Verbo + resultado (por ejemplo, "Responder con la cita de la fuente") |
| Historia | Como *rol*, se requiere *capacidad* para *beneficio* |
| Criterios de aceptación | Lista verificable, en formato Dado / Cuando / Entonces |
| Definición de hecho | Pruebas en verde, PR revisado, documentación actualizada, evidencia registrada |
| Evidencia | Identificador `EV-A-NNN` y ruta en `docs/evidencias/A/sprint-NN/` |
