# 7. Infraestructura y dimensionamiento

Se recomienda la opción gestionada en la cuenta AWS de la EPN: un PostgreSQL con pgvector compartido con B (esquemas separados), LLM por API y sin GPU propia. El corpus estimado es pequeño.

## Opciones

| Opción | Componentes | A favor | En contra |
| --- | --- | --- | --- |
| **1. Gestionada (recomendada)** | Amazon Bedrock (LLM + embeddings), RDS PostgreSQL + pgvector, contenedores (ECS/Fargate o EC2), S3 | Sin GPU; escala con el uso; datos dentro de AWS | Costo por uso; verificar modelos disponibles en la región |
| 2. Autoalojada | EC2 con GPU + modelo abierto (vLLM u Ollama) + pgvector | Control total; costo fijo | GPU encendida todo el tiempo; más mantenimiento |
| 3. Híbrida | Embeddings multilingües en CPU + LLM por API | Indexar no consume tokens | Dos piezas que mantener |

Contexto institucional: la EPN ya adquirió infraestructura AWS y el director pidió dimensionar los requerimientos para solicitarlos (notas de reunión).

## Estimación del corpus (estimación propia, a validar con el conteo real)

| Variable | Valor supuesto |
| --- | --- |
| Empresas con ficha textual | 600–1.500 |
| Páginas por empresa | 5 |
| Fragmentos por página | 3 |
| Vectores totales | 10.000–25.000 |
| Dimensión del embedding | 1.024 |
| Tamaño aproximado de vectores | ~100 MB |
| Base de datos suficiente | 2 vCPU, 4–8 GB RAM |
| Cuello de botella a medir en carga | Latencia del LLM, no la base |

## Solicitud a la EPN

| Recurso | Cantidad | Compartido con B |
| --- | --- | --- |
| RDS PostgreSQL con extensión pgvector | 1 instancia pequeña | Sí (esquemas separados) |
| Servicio de contenedores para APIs | 1 | Sí |
| Bucket S3 para corpus y descargas | 1 | Sí |
| Acceso a Amazon Bedrock | 1 cuenta/rol | No |
| Subdominio para portal y API | 1 | Sí |

## Entorno local (Windows PowerShell)

```powershell
$env:PG_PASS = Read-Host -Prompt "Clave Postgres"
docker run -d --name obs-pg -e POSTGRES_PASSWORD=$env:PG_PASS -p 5432:5432 pgvector/pgvector:pg16
docker exec -it obs-pg psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
```
