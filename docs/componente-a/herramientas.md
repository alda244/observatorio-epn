# Herramientas

| Ámbito | Herramienta | Uso |
| --- | --- | --- |
| Lenguaje y paquetes | Python 3.12, uv | Todo el backend |
| API | FastAPI, uvicorn | `/chat` y `/salud` |
| RAG | LlamaIndex | Fragmentación y recuperación, al pasar a pgvector |
| Embeddings | BGE-M3 en CPU | Vectores multilingües densos y dispersos |
| Base vectorial | PostgreSQL 16 + pgvector | Índice y trazas en el esquema `asistente` |
| Acceso a datos | SQLAlchemy Core, Alembic, psycopg 3 | Consultas y migraciones |
| LLM | Cliente `openai` | Una sola interfaz para cualquier proveedor ([ADR 0004](../adr/0004-llm-interfaz-openai.md)) |
| Cliente de B | httpx | Llamadas a la API de B |
| Configuración | Variables de entorno | Modelo, umbrales y proveedor |
| Pruebas y lint | pytest, ruff | Con embeddings y LLM simulados |
| Evaluación | RAGAS, SUS, Locust | Calidad, usabilidad y carga |
| Trazas | Tabla `asistente.traza`, Langfuse | Registro y visualización |
| Contrato | OpenAPI 3.1, Spectral, Prism | Validación y API simulada de B |
| Widget | React + TypeScript, tsup, Storybook, Vitest, axe-core, ESLint, Prettier | Igual que FragUI ([ADR 0005](../adr/0005-widget-alineado-fragui.md)) |
| Desarrollo local del LLM | Ollama | Modelo abierto sin costo |
| Gestión | Scrum, Linear (equipo `ASI`), GitHub | Backlog, sprints y revisión por PR |
| Memoria | Markdown, Mermaid, Zotero (IEEE), plantilla EPN | Documentación y referencias |
