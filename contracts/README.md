# contracts

Contrato OpenAPI 3.1 entre la API de B, el asistente de A y el widget ([ADR 0003](../docs/adr/0003-contrato-primero.md)). El archivo `openapi.yaml` está por redactar.

| Ruta | Implementa | Consume |
| --- | --- | --- |
| `GET /empresas` | B | A |
| `GET /empresas/{expediente}` | B | A |
| `GET /empresas/{expediente}/documentos` | B | A |
| `GET /indicadores` | B | A |
| `POST /chat` | A | widget |

| Cambio | Versión |
| --- | --- |
| Campo opcional o ruta nueva | Menor |
| Cambio incompatible | Mayor, con ADR |

Todo cambio entra por PR revisado por el otro estudiante.
