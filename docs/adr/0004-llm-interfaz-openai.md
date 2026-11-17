# 0004. LLM por una interfaz compatible con OpenAI

| Campo | Valor |
| --- | --- |
| Estado | Aceptado; el modelo se elige con la comparación de LLM |
| Fecha | 2026-11-17 |
| Componente | A |

## Contexto

El modelo de lenguaje todavía no está elegido y puede cambiar durante el proyecto por costo o calidad. La mayoría de proveedores, incluido Bedrock y Ollama, ofrecen un endpoint compatible con la API de OpenAI.

## Decisión

El asistente usa el cliente `openai` con `base_url`, `api_key` y `model` definidos por variables de entorno. Una respuesta sin citas válidas se descarta antes de llegar al usuario.

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | Cambiar de proveedor es cambiar una variable |
| Positiva | La misma interfaz sirve para Ollama en desarrollo |
| Negativa | Funciones propias de cada proveedor quedan fuera |
