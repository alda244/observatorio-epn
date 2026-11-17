# infra

Configuración de la base de datos y del despliegue. El detalle está en [docs/infraestructura.md](../docs/infraestructura.md).

| Esquema | Rol | Dueño | Acceso del otro componente |
| --- | --- | --- | --- |
| Esquemas de B | `rol_datos` | B | Ninguno |
| `asistente` | `rol_asistente` | A | Ninguno |

La extensión `vector` se instala en `public`. El script de creación de esquemas y roles y el `docker-compose.yml` están por agregar.
