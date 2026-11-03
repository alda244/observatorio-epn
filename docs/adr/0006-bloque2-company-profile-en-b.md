# 0006. Bloque 2 del Company Profile producido por B

| Campo | Valor |
| --- | --- |
| Estado | Propuesto |
| Fecha | 2026-11-03 |
| Componente | Compartido |
| Decisores | Eduardo Miguel Muzo Cansigña (propone), Alicia Pereira (revisa), director |
| Issue / PR | Pendiente |

## Contexto

Las dos investigaciones de alcance proponen recolectar el mismo texto: la de A asigna a A la ficha textual, incluida la "oferta de valor" (productos y servicios, propuesta diferencial) ([`../investigacion/04`](../investigacion/04-ficha-de-empresa.md), decisión 5 de [`../investigacion/08`](../investigacion/08-agenda-de-negociacion.md)); la de B propone que B produzca el Bloque 2 del formato *Company Profile* (tagline, descripción, productos y servicios) ([`../investigacion-b/02`](../investigacion-b/02-company-profile-bloque2.md)). Ambas no pueden quedar: dos recolectores sobre las mismas webs duplican trabajo y carga sobre los sitios. Hay que elegir un solo dueño.

| Equivalencia | Ficha de A | Company Profile (director) |
| --- | --- | --- |
| Lo que se disputa | Oferta de valor | Bloque 2: tagline, descripción, productos/servicios |
| Lo que no se disputa | Identidad y propósito; datos de operación | Bloques 1 y 3 (fuera del alcance de B) |

## Criterios de decisión

| Criterio | A produce el Bloque 2 | B produce el Bloque 2 |
| --- | --- | --- |
| Acceso a los datos que identifican a la empresa | El RUC, la razón social y el expediente están en el esquema `datos`, que A no puede leer ([ADR 0002](0002-postgresql-esquemas-roles.md)) | B los tiene: `bi_compania` cruza RUC ↔ expediente en el 100 % del ranking ([`../investigacion-b/01`](../investigacion-b/01-fuentes-y-universo.md)) |
| Verificación de la URL oficial (el cuello de botella) | Necesitaría el RUC y la razón social por API para validar cada sitio | Se valida localmente con `rapidfuzz` ≥ 0,85 contra RUC y razón social ([`../investigacion-b/04`](../investigacion-b/04-descubrimiento-de-urls.md)) |
| Selección del universo y del piloto | Depende de que B entregue antes el universo filtrado | B ya calculó el universo (14.042) y define el piloto (~500) |
| Evidencia existente | Sin piloto ni recolector | Piloto de 10 empresas y spider ético probado ([`../investigacion-b/03`](../investigacion-b/03-fuentes-bloque2.md), [`../investigacion-b/06`](../investigacion-b/06-scraping-etico.md)) |
| Publicación como dato abierto (F_AA_233A, plan F_AA_234A) | El texto queda dentro del índice vectorial del asistente | El Bloque 2 se publica en el portal con licencia, DCAT y procedencia por fila |
| Coherencia con la regla de A "toda cifra se toma de la API de B" | Dos fuentes de verdad sobre la misma empresa | Mismo patrón: la ficha estructurada también sale de la API de B |
| Foco de cada tesis | A reparte su tiempo entre recolección y motor RAG | A concentra su aporte en recuperación, salvaguardas, trazabilidad, evaluación RAGAS y widget |

## Decisión

Propuesta: B produce el Bloque 2 en `ficha_contenido` y lo expone en `/empresas/{expediente}`, con `fuente_url`, `fuente_tipo`, `fecha_captura`, `sha256` y `tagline_origen` por fila. A lo consume por la API, igual que las cifras, y conserva los campos textuales de identidad y operación de su ficha.

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | Un solo recolector por sitio, con la configuración ética de [`../investigacion-b/06`](../investigacion-b/06-scraping-etico.md) |
| Positiva | El asistente cita el Bloque 2 con URL, fecha y origen `literal`/`derivado` |
| Negativa | B asume el descubrimiento y la verificación de URLs, estimado en 17–25 h para el piloto ([`../investigacion-b/04`](../investigacion-b/04-descubrimiento-de-urls.md)) |
| Seguimiento | Campos opcionales del Bloque 2 en `contracts/openapi.yaml` (versión menor) |
| Seguimiento | Exponer en la API las URL oficiales verificadas para que `rag.ingesta` las reutilice en identidad y operación sin repetir la búsqueda |
| Seguimiento | Si se acepta, actualizar [`../investigacion/04`](../investigacion/04-ficha-de-empresa.md), [`../investigacion/08`](../investigacion/08-agenda-de-negociacion.md) y el diagrama de [`../arquitectura/`](../arquitectura/README.md) |
