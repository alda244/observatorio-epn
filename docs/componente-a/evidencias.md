# Evidencias

| Código | Fecha | Sprint | Evidencia | Ubicación |
| --- | --- | --- | --- | --- |
| EV-A-001 | 2026-11-09 | 1 | Descarga del ranking SCVS 2025 y del catálogo CIIU con hash SHA-256 | [`MANIFEST.csv`](../../etl/datos/crudo/MANIFEST.csv) |
| EV-A-002 | 2026-11-09 | 1 | Script de selección del universo y reporte de calidad | [`seleccionar_universo.py`](../../etl/universo/seleccionar_universo.py), [`calidad_2025.json`](../../etl/datos/universo/2025/calidad_2025.json) |
| EV-A-003 | 2026-11-09 | 1 | Listas top 50 por grupo y piloto de 500 | [`etl/datos/universo/2025/`](../../etl/datos/universo/2025/) |
| EV-A-004 | 2026-11-09 | 1 | Justificación del universo | [justificacion-universo.md](../justificacion-universo.md) |
| EV-A-005 | 2026-11-09 | 2 | Prototipo de ingesta, índice y consulta con pruebas | [`rag/`](../../rag/), [`rag/evidencias/`](../../rag/evidencias/) |
| EV-A-006 | 2026-11-18 | 1 | Casos de uso, protocolo de evaluación y 50 preguntas de referencia | [casos-de-uso.md](casos-de-uso.md), [protocolo-evaluacion.md](protocolo-evaluacion.md), [`preguntas_referencia.json`](../../rag/evaluacion/preguntas_referencia.json) |
| EV-A-007 | 2026-11-18 | 1 | Revisión bibliográfica | [estado-del-arte.md](estado-del-arte.md) |
| EV-A-008 | 2026-11-18 | 1 | Borrador del contrato OpenAPI, validado contra respuestas reales | [`contracts/openapi.yaml`](../../contracts/openapi.yaml) |
| EV-A-009 | 2026-11-18 | 2 | Índice en pgvector: 500 empresas en 1,7 s, segunda corrida sin reprocesar, misma evaluación que con archivos | [`ingesta_pgvector.json`](../../rag/evidencias/ingesta_pgvector.json), [`eval50_hash_pgvector.json`](../../rag/evidencias/eval50_hash_pgvector.json) |
| EV-A-010 | 2026-11-18 | 2 | Evaluación con 50 preguntas y salvaguarda de campo pedido | [`eval50_hash.json`](../../rag/evidencias/eval50_hash.json) |
| EV-A-011 | 2026-11-18 | 1 | Script de comparación de LLM, probado con un servidor simulado | [`comparar_llm.py`](../../rag/src/rag/comparar_llm.py) |
| EV-A-012 | 2026-11-18 | 2 | 17 pruebas automáticas y CI con PostgreSQL | [`rag/tests/`](../../rag/tests/), [`rag.yml`](../../.github/workflows/rag.yml) |
| EV-A-013 | 2026-11-18 | 2 | Comparación de embeddings (léxico, MiniLM, BGE-M3) y recalibración de umbrales | [comparacion-embeddings.md](comparacion-embeddings.md), [`eval50_minilm.json`](../../rag/evidencias/eval50_minilm.json), [`eval50_bge_m3.json`](../../rag/evidencias/eval50_bge_m3.json), [`eval50_bge_m3_calibrado.json`](../../rag/evidencias/eval50_bge_m3_calibrado.json) |
| EV-A-014 | 2026-11-24 | 1 | Actor Gobierno y casos CU-08 y CU-09 | [casos-de-uso.md](casos-de-uso.md) |
| EV-A-015 | 2026-11-24 | 2 | Fichas del Company Profile en el índice, cliente HTTP de la API de B y corrección de la salvaguarda de campo pedido | [`cliente_b`](../../rag/src/rag/cliente_b/__init__.py), [`test_cliente_b.py`](../../rag/tests/test_cliente_b.py), [`ingesta_bge_m3_fichas.json`](../../rag/evidencias/ingesta_bge_m3_fichas.json) |
| EV-A-016 | 2026-11-24 | 2 | Evaluación con 50 preguntas, con y sin fichas | [evaluacion.md](evaluacion.md#con-el-company-profile), [`eval50_bge_m3_fichas.json`](../../rag/evidencias/eval50_bge_m3_fichas.json), [`eval50_bge_m3_salvaguarda.json`](../../rag/evidencias/eval50_bge_m3_salvaguarda.json), [`eval50_hash_fichas.json`](../../rag/evidencias/eval50_hash_fichas.json) |
| EV-A-017 | 2026-11-24 | 1 | Comparación de LLM lista para Ollama, Anthropic, OpenAI y Google, con conteo de errores y listado de ids | [`modelos_llm.json`](../../rag/evaluacion/modelos_llm.json), [`comparar_llm.py`](../../rag/src/rag/comparar_llm.py) |
| EV-A-018 | 2026-11-24 | 1 | Primera ronda de la comparación de LLM: GPT-6 Luna, Gemini 3.1 y 3.5 Flash-Lite, y Qwen2.5 7B en Ollama | [evaluacion.md](evaluacion.md#primera-ronda-24-nov-2026), [`llm.json`](../../rag/evidencias/llm.json), [`llm_ollama.json`](../../rag/evidencias/llm_ollama.json) |

Las capturas de pantalla se guardan en `docs/componente-a/evidencias/` con el nombre `EV-A-NNN-descripcion.png`.
