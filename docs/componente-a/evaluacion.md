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

Fallan "editan y publican software" (H3), "ingeniería y consultoría técnica", "supermercados en Quito" (H2) y "¿cómo está el clima mañana?".

La comparación con MiniLM y BGE-M3 está en [comparacion-embeddings.md](comparacion-embeddings.md). BGE-M3 calibrado (0,40 / 0,70) da acierto@5 0,921, MRR 0,882 y rechazo 1,000. Para repetirla:

```powershell
$env:PYTHONPATH = "rag/src"
$env:RAG_EMBEDDINGS = "BAAI/bge-m3"
python -m rag ingesta --reconstruir
python -m rag evaluar --salida rag/evidencias/eval50_bge_m3.json
```

## Con el Company Profile

El 24-nov-2026 B publicó una semilla con 57 fichas del Company Profile ([`etl/seed/profiles.csv`](../../etl/seed/profiles.csv)). El cliente de archivo de A las lee con la forma de `ficha` de la API, y la ingesta agrega un documento `perfil:{expediente}` por cada ficha no pendiente: 54 documentos, citados con la URL oficial y la fecha de captura. El índice pasa de 500 a 554 documentos; con BGE-M3, la ingesta tarda 340 s en CPU.

Las fichas destaparon un error de la salvaguarda de campo pedido: buscaba el campo en todos los fragmentos recuperados, así que el teléfono de Quifatex respaldaba la pregunta por el teléfono de Saludsa. Ahora, si la pregunta nombra a una empresa, el campo se busca solo en sus fragmentos. Con esa corrección, BGE-M3 sin fichas ya rechaza S04 (H10 de [comparacion-embeddings.md](comparacion-embeddings.md)).

| Métrica | Léxico | Léxico con fichas | BGE-M3 | BGE-M3 con fichas |
| --- | --- | --- | --- | --- |
| Acierto@5 | 0,921 | 0,921 | 0,921 | 0,921 |
| MRR | 0,784 | **0,818** | 0,882 | 0,882 |
| Rechazo correcto | 0,875 | 0,500 | **1,000** | 0,875 |
| Sin dato correcto | 1,000 | 1,000 | **1,000** | **1,000** |
| Falsos rechazos | 0 | 0 | 0 | 0 |
| Actividad y lugar | 5/6 | **6/6** | 5/6 | 5/6 |

BGE-M3 usa los umbrales calibrados (0,40 / 0,70) y las cuatro columnas usan el mismo código. La columna BGE-M3 mejora la evaluación documentada en `sin_dato` (de 0,750 a 1,000) solo por la corrección de la salvaguarda.

| Nº | Hallazgo | Qué se hace |
| --- | --- | --- |
| H13 | Las 50 preguntas se escribieron sobre la descripción CIIU; con fichas para 54 de 500 empresas, acierto@5 y MRR de BGE-M3 no cambian | Agregar preguntas `perfil` que solo se responden con la ficha |
| H14 | "Supermercados en Quito" sigue fallando. La ficha de Favorita (Quito, G4711) es la única que dice "supermercados" y queda primera en BM25, pero su coseno es bajo (0,455): la ficha mezcla lema, descripción, productos y contacto, y el embedding se diluye. En la fusión queda en el puesto 11 | Fragmentar la ficha por campo, para que cada fragmento tenga un solo tema |
| H15 | "¿Qué empresas tienen supermercados?", sin ciudad, ahora devuelve primero la ficha de Favorita | Confirma H2: el texto de la web cubre el vocabulario que la CIIU no tiene |
| H16 | El texto publicitario de las webs acerca preguntas fuera de alcance: con BGE-M3, "dame consejos para bajar de peso" se responde con la ficha de Farcomed; con el léxico se responden cuatro de ocho | Recalibrar los umbrales con el corpus con fichas y evaluar una regla más estricta para los fragmentos `perfil` |
| H17 | El teléfono y la web de Telconet ya se responden desde su ficha (CU-05) | El caso deja de ser solo `sin_dato` |

Evidencias: [`eval50_hash_fichas.json`](../../rag/evidencias/eval50_hash_fichas.json), [`eval50_bge_m3_salvaguarda.json`](../../rag/evidencias/eval50_bge_m3_salvaguarda.json), [`eval50_bge_m3_fichas.json`](../../rag/evidencias/eval50_bge_m3_fichas.json) e [`ingesta_bge_m3_fichas.json`](../../rag/evidencias/ingesta_bge_m3_fichas.json).

```powershell
$env:PYTHONPATH = "rag/src"
$env:RAG_EMBEDDINGS = "BAAI/bge-m3"
$env:RAG_UMBRAL_SIMILITUD = "0.40"; $env:RAG_UMBRAL_FUERTE = "0.70"
python -m rag ingesta --reconstruir     # RAG_FICHAS apunta a etl/seed/profiles.csv por defecto
python -m rag evaluar --salida rag/evidencias/eval50_bge_m3_fichas.json
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

La primera ronda usa OpenAI y Google en la nube, y Ollama en local. Claude Haiku 4.5 queda como referencia sin correr: su costo en el pico (USD 50 al mes) es diez veces el de GPT-6 Luna. Las entradas de Bedrock se corren cuando la cuenta AWS de la EPN esté habilitada. El 24-nov-2026, `--listar` confirmó los ids `gpt-6-luna`, `gemini-3.1-flash-lite` y `gemini-3.5-flash-lite`. Todos se llaman por la interfaz compatible con OpenAI ([ADR 0004](../adr/0004-llm-interfaz-openai.md)); Anthropic, mediante su capa de compatibilidad con OpenAI.

| Paso | Comando |
| --- | --- |
| 1. Instalar Ollama y preparar el modelo | `winget install Ollama.Ollama`, `ollama pull qwen2.5:7b` y `ollama create qwen2.5-cpu -f rag/evaluacion/ollama/Modelfile.qwen2.5-cpu` |
| 2. Cargar una clave por proveedor | Copiar `rag/.env.example` como `rag/.env` y completar `OPENAI_API_KEY` y `GEMINI_API_KEY` |
| 3. Confirmar los ids que ofrece cada proveedor | `python -m rag comparar-llm --listar` |
| 4. Correr la comparación | `python -m rag comparar-llm --salida rag/evidencias/llm` |

```powershell
$env:PYTHONPATH = "rag/src"
$env:RAG_EMBEDDINGS = "BAAI/bge-m3"
$env:RAG_UMBRAL_SIMILITUD = "0.40"; $env:RAG_UMBRAL_FUERTE = "0.70"
python -m rag comparar-llm --listar
python -m rag comparar-llm --salida rag/evidencias/llm
```

El comando omite los modelos sin id o sin clave, y escribe `llm.json` con las métricas y `llm.csv` con todas las respuestas para la revisión manual. `errores_llm` cuenta las llamadas fallidas (clave, id o red); si no es 0, las métricas de ese modelo no son válidas. `rag/.env` está en `.gitignore`, así que las claves nunca entran al repositorio; una variable definida en la sesión de PowerShell tiene prioridad sobre el archivo.

| Modelo | Proveedor | Id | Entrada (USD / 1M tokens) | Salida (USD / 1M tokens) | Costo mensual en el pico |
| --- | --- | --- | --- | --- | --- |
| Qwen2.5 7B | Ollama (local) | `qwen2.5:7b` | 0 | 0 | 0 (solo desarrollo) |
| Claude Haiku 4.5 | Anthropic | `claude-haiku-4-5` | 1,00 | 5,00 | 50,00 |
| GPT-6 Luna | OpenAI | `gpt-6-luna` | 0,10 | 0,50 | 5,00 |
| Gemini 3.1 Flash-Lite | Google | `gemini-3.1-flash-lite` | 0,25 | 1,50 | 13,50 |
| Gemini 3.5 Flash-Lite | Google | `gemini-3.5-flash-lite` | 0,30 | 2,50 | 19,00 |
| Amazon Nova Lite | Bedrock | Por completar | 0,06 | 0,24 | 2,76 |
| Claude Haiku 4.5 | Bedrock | Por completar | 1,00 | 5,00 | 50,00 |

El precio y el id de Claude Haiku 4.5 se confirmaron en la documentación oficial de Anthropic el 24-nov-2026; los de OpenAI y Google, consultados el 03-nov-2026, se confirman con `--listar` y en las páginas oficiales antes de contratar. El pico supone 10.000 consultas al mes, con unos 3.000 tokens de entrada y 400 de salida por consulta.

Ollama corre en el equipo de desarrollo (Ryzen 9 6900HS, 28 GB de RAM y RTX 3050 de 4 GB). Con el driver NVIDIA 546.92, la librería CUDA de Ollama 0.40 falla al cargar el modelo ("device kernel image is invalid"), así que el modelo corre solo en CPU con [`Modelfile.qwen2.5-cpu`](../../rag/evaluacion/ollama/Modelfile.qwen2.5-cpu): tarda de 40 a 60 s por pregunta, y por eso tiene `"timeout": 300` en `modelos_llm.json`. Su latencia no es comparable con la de un servicio en la nube. Sirve para medir citas y rechazos sin costo, no para el despliegue. En dos preguntas de prueba, Qwen2.5 7B respondió sin citas `[n]` válidas y el motor descartó las respuestas.

### Primera corrida (24-nov-2026)

La primera corrida no sirve para comparar modelos: de las 39 preguntas que pasan la recuperación, fallaron 39 llamadas de Ollama, 39 de GPT-6 Luna, 16 de Gemini 3.1 Flash-Lite y 17 de Gemini 3.5 Flash-Lite. El motor convierte cada fallo en respuesta extractiva, así que sin el conteo `errores_llm` habrían pasado por resultados.

| Modelo | Causa | Corrección |
| --- | --- | --- |
| Ollama | El servicio no estaba instalado; ya instalado, la GPU falla con el driver actual | Instalado el 24-nov-2026; modelo en CPU (`qwen2.5-cpu`) con límite de 300 s por llamada |
| GPT-6 Luna | HTTP 400: el modelo solo acepta la temperatura por defecto | `"temperatura": null` en `modelos_llm.json` |
| Gemini | Fallos intermitentes; una llamada aislada responde bien. Es compatible con el límite de solicitudes por minuto | Reintento con espera ante 429 y 5xx, y tipo de error en `errores_tipo` |

| Nº | Hallazgo | Qué se hace |
| --- | --- | --- |
| H18 | Cuando Gemini respondió, citó bien casi siempre: 23 de 23 (3.1) y 21 de 22 (3.5) | Se confirma con la corrida completa |
| H19 | El contexto real es de unos 1.100 tokens de entrada y 100 de salida, no 3.000 y 400 como suponía el escenario de costo | El costo mensual se recalcula con los tokens medidos |
| H20 | El rechazo correcto fue 0,917 en todos los modelos: lo decide la recuperación, no el LLM. Solo F08 llega al LLM | El rechazo no sirve para distinguir modelos; pesan fidelidad, citas y revisión manual |

`citas_validas` se calcula ahora solo sobre las llamadas respondidas, y la latencia, solo sobre las preguntas que llegaron al LLM.

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
