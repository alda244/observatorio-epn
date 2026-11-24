# Comparación de modelos de embeddings

Se comparan tres formas de convertir texto en vectores con las mismas 50 preguntas de referencia ([`preguntas_referencia.json`](../../rag/evaluacion/preguntas_referencia.json)) y el mismo corpus: las 500 fichas de identificación del piloto. El protocolo está en [protocolo-evaluacion.md](protocolo-evaluacion.md).

| Campo | Valor |
| --- | --- |
| Fecha | 2026-11-18 |
| Sprint | 2 |
| Corpus | 500 fichas, un fragmento por empresa |
| Recuperación | Híbrida: coseno + BM25 con fusión RRF, top 5 |
| Generación | Extractiva (sin LLM) |
| Equipo | CPU, sin GPU |

## Modelos

| Modelo | Tipo | Dimensiones | Longitud máxima de entrada | Evidencia |
| --- | --- | --- | --- | --- |
| `hash-512` | Léxico, línea base | 512 | Sin límite | [`eval50_hash.json`](../../rag/evidencias/eval50_hash.json) |
| `paraphrase-multilingual-MiniLM-L12-v2` | Semántico, pequeño | 384 | 128 tokens | [`eval50_minilm.json`](../../rag/evidencias/eval50_minilm.json) |
| `BAAI/bge-m3` | Semántico, grande | 1024 | 8.192 tokens | [`eval50_bge_m3.json`](../../rag/evidencias/eval50_bge_m3.json), [`eval50_bge_m3_calibrado.json`](../../rag/evidencias/eval50_bge_m3_calibrado.json) |

## Umbrales de la salvaguarda

El asistente responde solo si el mejor coseno supera el umbral fuerte, o si supera el umbral de similitud y además hay coincidencia léxica ([asistente.md](asistente.md)). Cada modelo puntúa en su propia escala, por eso los umbrales se calibran por modelo.

| Modelo | Umbral de similitud | Umbral fuerte | Origen |
| --- | --- | --- | --- |
| `hash-512` | 0,05 | 0,95 | Línea base |
| MiniLM | 0,30 | 0,65 | Calibrado con las 30 preguntas del prototipo |
| BGE-M3 sin calibrar | 0,30 | 0,65 | Los de MiniLM |
| BGE-M3 calibrado | 0,40 | 0,70 | Ajustado con las 50 preguntas |

## Resultados

| Métrica | Meta | Léxico | MiniLM | BGE-M3 sin calibrar | BGE-M3 calibrado |
| --- | --- | --- | --- | --- | --- |
| Acierto@5 (38 con respuesta) | ≥ 0,90 | 0,921 | **0,947** | 0,921 | 0,921 |
| MRR | ≥ 0,80 | 0,784 | 0,844 | **0,882** | **0,882** |
| Rechazo correcto (8 fuera de alcance) | 1,00 | 0,875 | **1,000** | 0,875 | **1,000** |
| Sin dato correcto (4) | 1,00 | **1,000** | 0,750 | 0,750 | 0,750 |
| Falsos rechazos | 0 | 0 | 0 | 0 | 0 |

| Tipo de pregunta | Léxico | MiniLM | BGE-M3 calibrado |
| --- | --- | --- | --- |
| Por nombre | 9/9 | 9/9 | 9/9 |
| Con cifras | 4/4 | 4/4 | 4/4 |
| Por actividad | 17/19 | 18/19 | 17/19 |
| Por actividad y lugar | 5/6 | 5/6 | 5/6 |
| Fuera de alcance | 7/8 | 8/8 | 8/8 |
| Sin dato | 4/4 | 3/4 | 3/4 |

### Costo de indexar

| Modelo | Tiempo de ingesta de 500 fichas en CPU | Tamaño de los vectores |
| --- | --- | --- |
| MiniLM | 32–44 s | 0,8 MB |
| BGE-M3 | 269–530 s | 2,0 MB |

Tiempos tomados del registro de corridas de la ingesta (`rag/datos/indice/corridas.jsonl`, local y fuera del repositorio), en cuatro corridas del 18-nov-2026. BGE-M3 es entre 6 y 12 veces más lento al indexar. La ingesta es incremental, así que ese costo se paga una vez por documento y no por consulta.

## Fallos por pregunta

| Pregunta | Tipo | Léxico | MiniLM | BGE-M3 calibrado |
| --- | --- | --- | --- | --- |
| P10 · Empresas que editan y publican software | Actividad | Falla | Falla | Falla |
| P19 · Empresas de ingeniería y consultoría técnica | Actividad | Falla | Rango 3 | Falla |
| P24 · Supermercados en Quito | Actividad y lugar | Falla | Falla | Falla |
| F04 · ¿Cómo está el clima mañana? | Fuera de alcance | Responde | Rechaza | Rechaza |
| S04 · ¿Qué certificaciones tiene Holcim? | Sin dato | Rechaza | Responde | Responde |

## Hallazgos

| Nº | Hallazgo | Qué se hace |
| --- | --- | --- |
| H7 | P10 y P24 fallan con los tres modelos: la brecha es de vocabulario de la CIIU, no del modelo (H2, H3) | Medido con las 57 fichas de B: P24 sigue fallando porque Favorita está en Sangolquí ([evaluacion.md](evaluacion.md#con-el-company-profile)) |
| H8 | Los modelos semánticos superan a la línea base en orden (MRR +0,06 y +0,10) y en rechazo | El RAG semántico aporta frente a la búsqueda por palabras |
| H9 | Con umbrales recalibrados, BGE-M3 pasa de 7/8 a 8/8 rechazos sin perder aciertos | Los umbrales se calibran cada vez que cambia el modelo |
| H10 | S04 (certificaciones de Holcim) se responde con ambos modelos semánticos y no con el léxico | Resuelto: si la pregunta nombra a una empresa, el campo se busca solo en sus fragmentos ([evaluacion.md](evaluacion.md#con-el-company-profile)) |
| H11 | La diferencia de acierto@5 entre MiniLM y BGE-M3 es una sola pregunta (P19) de 38 | Con este corpus los dos modelos son equivalentes en acierto |
| H12 | MiniLM corta la entrada en 128 tokens; los fragmentos son de 350 palabras | Con las fichas actuales, cortas, no afecta. Con el texto de las webs, MiniLM perdería contenido |

## Decisión provisional

Se adopta **BGE-M3 con umbrales 0,40 / 0,70** para el Sprint 3:

| Criterio | Razón |
| --- | --- |
| Orden de resultados | Mejor MRR (0,882): la empresa correcta aparece más arriba |
| Salvaguardas | Rechazo 8/8, igual que MiniLM, sin falsos rechazos |
| Textos largos | Acepta 8.192 tokens; el Company Profile tendrá páginas completas |
| Costo | Corre en CPU; el tiempo extra de ingesta se paga una sola vez |

MiniLM queda como alternativa si el servidor sin GPU no sostiene la latencia de BGE-M3 en las pruebas de carga. La decisión se confirma con un ADR cuando se repita esta comparación con el texto del Company Profile.

## Limitaciones

| Limitación | Cómo se atiende |
| --- | --- |
| Los umbrales de BGE-M3 se ajustaron con las mismas 50 preguntas con las que se evalúa, lo que puede sobreestimar el resultado | Separar un conjunto de preguntas de validación que no se use para calibrar |
| Los umbrales de MiniLM vienen de las 30 preguntas del prototipo y no se recalibraron con las 50 | Calibrar ambos modelos con el mismo procedimiento en la siguiente corrida |
| 38 preguntas con respuesta: una pregunta mueve el acierto@5 en 0,026 | Ampliar las preguntas cuando haya texto del Company Profile |
| Solo mide la recuperación; no evalúa la respuesta generada | RAGAS en el Sprint 3, con el LLM elegido |

## Cómo reproducir

```powershell
$env:PYTHONPATH = "rag/src"
$env:RAG_EMBEDDINGS = "BAAI/bge-m3"
python -m rag ingesta --reconstruir
python -m rag evaluar --salida rag/evidencias/eval50_bge_m3.json
$env:RAG_UMBRAL_SIMILITUD = "0.40"
$env:RAG_UMBRAL_FUERTE = "0.70"
python -m rag evaluar --salida rag/evidencias/eval50_bge_m3_calibrado.json
```

Para MiniLM se usa `RAG_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"` con los umbrales por defecto.
