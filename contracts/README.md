# contracts

Dueño: compartido (A y B). Contrato OpenAPI 3.1 entre la API de B, el asistente de A y el widget (ADR 0003).

| Ruta | Implementa | Consume |
| --- | --- | --- |
| `GET /empresas` | B (`api/`) | A (`rag/`) |
| `GET /empresas/{expediente}` | B (`api/`) | A (`rag/`) |
| `GET /indicadores` | B (`api/`) | A (`rag/`) |
| `POST /chat` | A (`rag/`) | `widget/` |

## Reglas de cambio

| Regla | Detalle |
| --- | --- |
| Todo cambio entra por PR revisado por el otro estudiante | `CODEOWNERS` |
| Cambio incompatible (a partir de 1.0.0) | Issue con plantilla `cambio-contrato`, ADR y versión mayor en `info.version` |
| Cambio compatible (campo opcional, ruta nueva) | Versión menor |
| Validación | Spectral en la CI (`scripts\test.ps1 -Modulo contracts`) |

## Uso local

```powershell
# Validar el contrato
.\scripts\test.ps1 -Modulo contracts

# Mock de la API de B en http://localhost:4010 (A desarrolla sin depender de B)
.\scripts\dev.ps1 -Modulo mock-b
```
