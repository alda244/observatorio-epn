# 0006. B recolecta las webs y produce el Company Profile

| Campo | Valor |
| --- | --- |
| Estado | Aceptado |
| Fecha | 2026-11-03 |
| Componente | Compartido |

## Contexto

A y B necesitan texto de las webs oficiales de las mismas empresas. Dos recolectores sobre los mismos sitios duplican trabajo y carga. B ya tiene el RUC y la razón social para verificar cada web y ya define el universo.

## Decisión

B es el único recolector. Captura, una vez por empresa, la portada, "nosotros", "productos y servicios" y los PDF oficiales, y expone:

| Ruta | Contenido |
| --- | --- |
| `GET /empresas/{expediente}` | Campos estructurados del Company Profile y cifras |
| `GET /empresas/{expediente}/documentos` | Texto limpio de cada página, con URL, fecha y hash |

A indexa esos documentos, deriva las palabras clave y responde sobre misión, visión, historia y certificaciones con cita. El detalle de los campos está en [ficha-empresa.md](../ficha-empresa.md).

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | Un solo recolector por sitio |
| Positiva | El Company Profile se publica también como dato abierto |
| Negativa | B asume la búsqueda y verificación de las webs (17–25 h para el piloto) |
| Negativa | A depende de B para tener texto más allá de la descripción CIIU |
