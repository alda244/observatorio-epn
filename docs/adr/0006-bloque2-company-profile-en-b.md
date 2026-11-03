# 0006. Bloque 2 del Company Profile producido por B

| Campo | Valor |
| --- | --- |
| Estado | Propuesto |
| Fecha | 2026-11-03 |
| Componente | Compartido |
| Decisores | Eduardo Miguel Muzo Cansigña (propone), Alicia Pereira (revisa), director |
| Issue / PR | Pendiente |

## Contexto

El formato *Company Profile* del director define el Bloque 2 (tagline, descripción, productos y servicios). La investigación de A asigna a A los campos textuales de la ficha, entre ellos productos y servicios ([`../investigacion/04`](../investigacion/04-ficha-de-empresa.md)). La investigación de B propone que B produzca el Bloque 2 como dato abierto, con fuente, fecha y origen `literal`/`derivado` por fila ([`../investigacion-b/02`](../investigacion-b/02-company-profile-bloque2.md), [`../investigacion-b/08`](../investigacion-b/08-plan-y-negociacion.md)). El plan F_AA_234A de B incluye el portal y la API pública por empresa.

## Opciones consideradas

| Opción | A favor | En contra |
| --- | --- | --- |
| A produce el Bloque 2 (como en [`../investigacion/04`](../investigacion/04-ficha-de-empresa.md)) | Un solo recolector de texto; sin cambio de contrato | El Bloque 2 no se publica como dato abierto en el portal de B |
| **B produce el Bloque 2 y lo sirve por `/empresas/{expediente}`** | Dato abierto, citable y visible en el portal; A lo consume por la API como las cifras | Cambio de contrato; B asume la recolección web y el descubrimiento de URLs |
| Reparto por campo | Cada uno llena lo que mejor conoce | Dos recolectores sobre las mismas webs; duplica la carga sobre los sitios |

## Decisión

Propuesta: B produce el Bloque 2 en `oro.ficha_contenido` y lo expone en `/empresas/{expediente}`. A lo consume por la API y conserva el resto de la ficha textual (identidad, operación).

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | El Bloque 2 queda publicado con licencia, metadatos y procedencia en el portal de datos |
| Positiva | El asistente cita el Bloque 2 con `fuente_url`, `fecha_captura` y `tagline_origen` |
| Negativa | B asume el descubrimiento de URLs, el cuello de botella del Bloque 2 ([`../investigacion-b/04`](../investigacion-b/04-descubrimiento-de-urls.md)) |
| Seguimiento | Campos opcionales del Bloque 2 en `contracts/openapi.yaml` (versión menor) |
| Seguimiento | Definir con A si `rag.ingesta` reutiliza las URL verificadas por B para no rastrear dos veces el mismo sitio |
| Seguimiento | Actualizar [`../investigacion/04`](../investigacion/04-ficha-de-empresa.md) y el diagrama de [`../arquitectura/`](../arquitectura/README.md) si se acepta |
