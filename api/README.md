# api · Componente B

Dueño: Eduardo Muzo. API pública FastAPI, de solo lectura sobre el esquema `datos`. Implementa las rutas `datos-abiertos` de [`contracts/openapi.yaml`](../contracts/openapi.yaml).

| Carpeta | Propósito |
| --- | --- |
| `src/api/main.py` | Aplicación FastAPI |
| `src/api/` | Rutas, consultas y esquemas (se agregan por sprint) |
| `tests/` | Pruebas con pytest + TestClient |

| Ruta | Estado |
| --- | --- |
| `GET /salud` | Hola mundo |
| `GET /empresas`, `GET /empresas/{expediente}`, `GET /indicadores` | Definidas en el contrato; sin implementar |

Propuesta en revisión: `GET /empresas/{expediente}` sirve también el Bloque 2 del Company Profile ([ADR 0006](../docs/adr/0006-bloque2-company-profile-en-b.md)).

## Stack

Python 3.12 · FastAPI · uvicorn · uv · pytest · ruff. El acceso a la base (SQLAlchemy Core + psycopg) se agrega con la primera ruta de datos. La API no escribe: las tablas las crea el ETL.

## Uso (PowerShell, desde la raíz)

```powershell
.\scripts\dev.ps1 -Modulo api     # http://localhost:8001/docs
.\scripts\test.ps1 -Modulo api
```
