# Evaluación

El protocolo completo está en [protocolo-evaluacion.md](protocolo-evaluacion.md). Resultados en [`rag/evidencias/`](../../rag/evidencias/).

## 50 preguntas de referencia

Evaluación con el embedding léxico (`hash-512`), que no necesita descargar modelos. Da el mismo resultado con el almacén en archivos y con pgvector.

| Métrica | Resultado | Meta |
| --- | --- | --- |
| Acierto@5 (38 preguntas con respuesta) | 0,921 | ≥ 0,90 |
| MRR | 0,784 | ≥ 0,80 |
| Rechazo correcto (8 fuera de alcance) | 0,875 | 1,00 |
| Sin dato correcto (4) | 1,000 | 1,00 |
| Falsos rechazos | 0 | 0 |

| Tipo | Aciertos |
| --- | --- |
| Por nombre | 9/9 |
| Con cifras | 4/4 |
| Por actividad | 17/19 |
| Por actividad y lugar | 5/6 |
| Sin dato | 4/4 |
| Fuera de alcance | 7/8 |

Fallan "editan y publican software" (H3), "ingeniería y consultoría técnica", "supermercados en Quito" (H2) y "¿cómo está el clima mañana?". La corrida con MiniLM y BGE-M3 se hace en un equipo con acceso a Hugging Face:

```powershell
$env:PYTHONPATH = "rag/src"
$env:RAG_EMBEDDINGS = "BAAI/bge-m3"
python -m rag ingesta --reconstruir
python -m rag evaluar --salida rag/evidencias/eval50_bge_m3.json
```

## Prototipo con 30 preguntas

Primera evaluación ([`preguntas_prototipo.json`](../../rag/evaluacion/preguntas_prototipo.json)).

| Métrica | Línea base léxica | MiniLM multilingüe |
| --- | --- | --- |
| Acierto@5 (24 preguntas con respuesta) | 0,875 | 0,917 |
| MRR | 0,706 | 0,816 |
| Rechazo correcto (6 fuera de alcance) | 0,833 | 1,000 |
| Falsos rechazos | 0 | 0 |

| Tipo de pregunta | Aciertos |
| --- | --- |
| Por nombre | 5/5 |
| Con cifras | 2/2 |
| Por actividad | 12/13 |
| Por actividad y lugar | 3/4 |
| Fuera de alcance | 6/6 |

### Hallazgos

| Nº | Hallazgo | Qué se hace |
| --- | --- | --- |
| H1 | El coseno solo no separa lo fuera de alcance (encebollado: 0,52; consulta válida: 0,42) | Regla de respaldo con coincidencia léxica; se recalibra con BGE-M3 |
| H2 | "Supermercados en Quito" falla: la CIIU de Favorita dice "venta al por menor en tiendas" | Lo resuelve el texto del Company Profile |
| H3 | "Editan software" no encuentra J582, que la CIIU llama "edición de programas informáticos" | Igual que H2, más BGE-M3 |
| H4 | La búsqueda por nombre necesita su propio índice | BM25 sobre la razón social dentro de la fusión RRF |
| H5 | Dato de empleados inconsistente | Advertencia automática con `alerta_empleados` |
| H6 | Ante "¿cuál es la misión de Pronaca?" se devolvía la ficha de Pronaca, que no tiene misión | Salvaguarda de campo pedido: si ninguna fuente lo contiene, "no hay dato publicado" |

## Comparación de LLM

Se comparan varios modelos con las mismas preguntas antes de elegir uno. El modelo elegido se registra en un ADR que completa el [ADR 0004](../adr/0004-llm-interfaz-openai.md).

```powershell
$env:PYTHONPATH = "rag/src"
$env:OPENAI_API_KEY = "..."   # una variable por proveedor, según modelos_llm.json
python -m rag comparar-llm --salida rag/evidencias/llm
```

Antes de correrlo se completa el id de cada modelo en [`modelos_llm.json`](../../rag/evaluacion/modelos_llm.json). El comando omite los modelos sin id o sin clave, y escribe `llm.json` con las métricas y `llm.csv` con todas las respuestas para la revisión manual.

| Modelo | Proveedor | Entrada (USD / 1M tokens) | Salida (USD / 1M tokens) | Costo mensual en el pico |
| --- | --- | --- | --- | --- |
| Amazon Nova Lite | Bedrock | 0,06 | 0,24 | 2,76 |
| GPT-6 Luna | OpenAI | 0,10 | 0,50 | 5,00 |
| Gemini 3.1 Flash-Lite | Google | 0,25 | 1,50 | 13,50 |
| Gemini 3.5 Flash-Lite | Google | 0,30 | 2,50 | 19,00 |
| Claude Haiku 4.5 (referencia) | Bedrock | 1,00 | 5,00 | 50,00 |

Precios consultados el 03-nov-2026; se confirman en las páginas oficiales antes de contratar. El pico supone 10.000 consultas al mes, con unos 3.000 tokens de entrada y 400 de salida por consulta.

| Criterio | Peso | Medición |
| --- | --- | --- |
| Fidelidad al contexto | 35 % | RAGAS `faithfulness` |
| Pertinencia | 20 % | RAGAS `answer_relevancy` |
| Español y citas correctas | 15 % | Revisión manual de 20 respuestas |
| Costo mensual | 15 % | Escenario de pico |
| Latencia p95 | 10 % | Sobre todas las preguntas |
| Facturación en la cuenta AWS de la EPN | 5 % | Sí o no |

Si el modelo ganador está en Bedrock, se usa ahí. Ningún dato de usuarios se envía a niveles gratuitos de ningún proveedor.

## Evaluación final

| Qué | Cómo |
| --- | --- |
| Calidad de las respuestas | RAGAS sobre 50 preguntas de referencia |
| Usabilidad | Escala SUS con al menos 30 usuarios |
| Rendimiento | Pruebas de carga de `/chat` con Locust |
