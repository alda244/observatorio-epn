# Evaluación

## Prototipo de recuperación

30 preguntas de referencia ([`preguntas_prototipo.json`](../../rag/evaluacion/preguntas_prototipo.json)) sobre las 500 empresas del piloto. Resultados en [`rag/evidencias/`](../../rag/evidencias/).

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

## Comparación de LLM

Se comparan varios modelos con las mismas preguntas antes de elegir uno. El modelo elegido se registra en un ADR que completa el [ADR 0004](../adr/0004-llm-interfaz-openai.md).

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
