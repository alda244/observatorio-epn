# rag · Componente A

Dueña: Alicia Pereira. Ingesta e indexación de texto oficial de empresas, motor RAG con citación, salvaguardas, trazabilidad y API `/chat`.

| Carpeta | Propósito |
| --- | --- |
| `datos/fichas/` | Fichas piloto en YAML y semillas de URLs oficiales |
| `src/rag/ingesta` | Captura respetuosa de webs oficiales (robots.txt, límite, URL, fecha, hash) |
| `src/rag/indice` | Fragmentación, embeddings BGE-M3, pgvector |
| `src/rag/motor` | Recuperación y generación con citas |
| `src/rag/salvaguardas` | Mitigación de alucinaciones y filtros |
| `src/rag/traza` | Registro de trazabilidad por respuesta |
| `src/rag/cliente_b` | Cliente HTTP de la API de B (nunca la base de B) |
| `src/rag/api` | FastAPI: `/chat` y `/salud` |
| `migraciones/` | Alembic del esquema `asistente` |
| `evaluacion/` | Preguntas de referencia y resultados RAGAS |
| `tests/` | Pruebas con pytest; LLM, embeddings y API de B simulados |

## Stack

| Ámbito | Herramienta | Origen |
| --- | --- | --- |
| Lenguaje / API | Python 3.12 · FastAPI | Plan F_AA_234A |
| Paquetes | uv | ADR 0001 |
| Base vectorial | PostgreSQL + pgvector, esquema `asistente` | ADR 0002 |
| LLM | Cliente compatible con OpenAI, configurado por `.env` | ADR 0004 |
| Pruebas / lint | pytest + pytest-cov / ruff | — |

Dependencias previstas, que se agregan cuando se usen: LlamaIndex, el modelo BGE-M3, el cliente `openai`, RAGAS y, opcionalmente, Langfuse.

## Uso (PowerShell, desde la raíz)

```powershell
.\scripts\dev.ps1 -Modulo mock-b   # API de B simulada desde el contrato (puerto 4010)
.\scripts\dev.ps1 -Modulo rag      # http://localhost:8002/docs
.\scripts\test.ps1 -Modulo rag
```
