# infra

Dueño: compartido. Configuración de infraestructura local, independiente del destino final (EPN o AWS).

| Archivo | Propósito |
| --- | --- |
| `postgres/init/01-esquemas.sh` | Extensión `vector`, esquemas `datos` (B) y `asistente` (A), un rol por esquema |
| `../docker-compose.yml` | PostgreSQL 16 + pgvector y mock opcional de la API de B |

## Esquemas y roles

| Esquema | Rol | Dueño | Permisos del otro componente |
| --- | --- | --- | --- |
| `datos` | `rol_datos` | B | Ninguno |
| `asistente` | `rol_asistente` | A | Ninguno |

El script de inicio corre solo cuando se crea el volumen. Para reiniciar la base local desde cero (borra los datos locales):

```powershell
docker compose down -v
docker compose up -d db
```

La extensión `vector` se instala en `public`; el rol de A la usa mediante su `search_path`.
