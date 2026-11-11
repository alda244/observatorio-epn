# Evidencias del prototipo (EV-A-005)

| Campo | Valor |
| --- | --- |
| Fecha | 2026-11-09 |
| Sprint | 2 (adelantado al cierre del Sprint 1) |
| Corpus | 500 fichas de identificación del piloto ([12](../../docs/investigacion/12-universo-aprobado.md)) |
| Modelo de embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones, CPU). El objetivo del plan es BGE-M3 |
| Generación | Extractiva (sin LLM). La generación con LLM está implementada y probada con un simulador; falta elegir el modelo |

## Archivos

| Archivo | Qué demuestra |
| --- | --- |
| [`ingesta_minilm.json`](ingesta_minilm.json) | Primera ingesta: 500 documentos → 500 fragmentos en 45 s |
| [`ingesta_minilm_repeticion.json`](ingesta_minilm_repeticion.json) | Idempotencia: la segunda corrida no reprocesa nada (0,2 s) |
| [`eval_minilm.json`](eval_minilm.json) | Evaluación de recuperación con 30 preguntas de referencia |
| [`eval_linea_base_hash.json`](eval_linea_base_hash.json) | Misma evaluación con embeddings léxicos (línea base) |
| [`consultas_ejemplo.txt`](consultas_ejemplo.txt) | Salida real de cuatro consultas, con citas, cifras, advertencias y rechazo |

## Resultados

| Métrica | Línea base léxica | MiniLM multilingüe |
| --- | --- | --- |
| Acierto@5 (24 preguntas con respuesta) | 0,875 | **0,917** |
| MRR | 0,706 | **0,816** |
| Rechazo correcto (6 preguntas fuera de alcance) | 0,833 | **1,000** |
| Falsos rechazos | 0 | 0 |

| Tipo de pregunta | Aciertos (MiniLM) |
| --- | --- |
| Por nombre de empresa | 5/5 |
| Con cifras | 2/2 |
| Por actividad | 12/13 |
| Por actividad y lugar | 3/4 |
| Fuera de alcance | 6/6 |

## Hallazgos

| Nº | Hallazgo | Consecuencia |
| --- | --- | --- |
| H1 | La similitud coseno sola no separa preguntas fuera de alcance (encebollado: 0,52; consulta válida sobre Tuti: 0,42) | Se adoptó una regla de respaldo: coseno ≥ 0,65, o coseno ≥ 0,30 con coincidencia léxica. Se recalibra con BGE-M3 |
| H2 | "Supermercados en Quito" falla: la descripción CIIU oficial de Corporación Favorita dice "venta al por menor... en tiendas", sin la palabra *supermercado* | Evidencia de que la ficha de identificación no basta: el texto del Company Profile (Bloque 2, de B) cierra la brecha de vocabulario |
| H3 | "Empresas que editan y publican software" no recupera J582: la CIIU llama a esa actividad "edición de programas informáticos" | Mismo origen que H2; también se mitiga con BGE-M3 y con el texto de las webs oficiales |
| H4 | Las búsquedas por nombre necesitan un índice propio de la razón social | Se agregó BM25 sobre los nombres a la fusión RRF |
| H5 | El dato de empleados es inconsistente (Tuti: 8 empleados, USD 1.008 M) | El motor adjunta la advertencia cuando se piden empleados de una empresa con `alerta_empleados` |

## Cómo reproducir

```powershell
$env:PYTHONPATH = "rag/src"
python -m rag ingesta --reconstruir
python -m rag evaluar --salida rag/evidencias/eval_minilm.json
```
