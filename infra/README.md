# infra

Configuración de la base de datos y del despliegue. El detalle está en [docs/infraestructura.md](../docs/infraestructura.md).

| Esquema | Rol | Dueño | Acceso del otro componente |
| --- | --- | --- | --- |
| Esquemas de B | `rol_datos` | B | Ninguno |
| `asistente` | `rol_asistente` | A | Ninguno |

La extensión `vector` se instala en `public`.

## Qué hay aquí

| Archivo | Para qué |
| --- | --- |
| `postgres/init/01-esquemas.sh` | Crea la extensión `vector`, los roles y los esquemas la primera vez que arranca la base |
| `../docker-compose.yml` | Levanta PostgreSQL 16 con pgvector en local |

La imagen oficial de PostgreSQL ejecuta una sola vez, al crear el volumen, lo
que encuentre en `/docker-entrypoint-initdb.d`. Ahí se monta esta carpeta.

**Por qué es un `.sh` y no un `.sql`:** las claves de los roles se leen del
`.env` (`POSTGRES_CLAVE_DATOS`, `POSTGRES_CLAVE_ASISTENTE`). Un archivo `.sql`
no puede leer variables de entorno, así que habría que escribir las claves en
el repositorio. El script envuelve `psql` y las inyecta desde el entorno.

```bash
cp .env.example .env     # y cambie las claves
docker compose up -d db
docker compose exec db psql -U postgres -d observatorio -c "\dn"
```

Si hay que volver a crear los esquemas desde cero, el script corre otra vez
solo si se borra el volumen: `docker compose down -v`.
