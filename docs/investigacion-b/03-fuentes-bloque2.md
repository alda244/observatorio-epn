# 3. Fuentes del Bloque 2

Ninguna fuente oficial masiva publica tagline, descripción ni productos. El texto sale de cada empresa. En el piloto, los PDF oficiales (informes anuales, memorias, catálogos) rindieron mejor que la web.

## Jerarquía de fuentes

| Prioridad | Fuente | Qué aporta | `fuente_tipo` |
| --- | --- | --- | --- |
| 1 | Web oficial: `title`, `meta description`, `og:description`, JSON-LD `Organization`, páginas "nosotros" y "servicios" | Tagline casi directa; lista de servicios | `web_oficial` |
| 2 | Informe anual, memoria de sostenibilidad o catálogo en PDF publicados por la empresa | Misión, descripción y líneas de negocio completas | `informe_anual_oficial`, `memoria_sostenibilidad_oficial`, `catalogo_oficial` |
| 3 | Informes de gestión del Portal de Documentos SCVS | Texto oficial cuando no hay web | `informe_gestion_scvs` |
| 4 | Organismos que describen a la empresa (BID Invest, reguladores) | Respaldo verificable | `tercero_institucional` |
| 5 | Prensa | Solo si no hay 1–4; marcar | `prensa` |

## Descartadas

| Fuente | Motivo |
| --- | --- |
| LinkedIn | Sus términos prohíben la extracción automatizada |
| Agregadores comerciales (EMIS, MarketLine, ZoomInfo) | De pago o con licencia restrictiva |
| Portal de aplicaciones SCVS por scraping | Rechaza el acceso automatizado ([`../investigacion/05`](../investigacion/05-adquisicion-de-datos.md)) |

## Evidencia del piloto (03-nov-2026)

| Empresa | Grupo | Fuente que funcionó | Estado |
| --- | --- | --- | --- |
| Corporación Favorita | G | [Informe CF 2024](https://www.corporacionfavorita.com/wp-content/uploads/2025/04/Informe-CF-2024.pdf) | Completo |
| PRONACA | C | [Folleto institucional](https://pronaca.com/wp-content/uploads/2026/04/folleto-ES.pdf) | Completo |
| SaludSA | K | [Memoria de Sostenibilidad 2023](https://www.saludsa.com/wp-content/uploads/2024/05/SALUDSA-Memoria-de-Sostenibilidad-2023.pdf) | Completo |
| CONECEL (Claro) | TEC | URL oficial vía [PeeringDB](https://b.peeringdb.net/net/6492); falta el texto | Parcial |
| Telconet | TEC | [Revisión ambiental y social de BID Invest](https://www.idbinvest.org/sites/default/files/environmental-and-social-review-46547-es.pdf) | Parcial |
| Security Data | TEC | [Prensa (KCH)](https://kchcomunicacion.com/?p=354991) | Parcial |
| La Fabril | C | [Prensa (KCH)](https://kchcomunicacion.com/?p=530378) | Parcial |
| Tatasolution Center, Fertisa, Misivacorp | TEC, M | Sin resultados útiles en búsqueda | Pendiente |

Lectura: 3 de 10 completas, todas con PDF oficial. Las grandes de G, C y K publican memorias; las tecnológicas medianas casi no, así que dependen de su web.

## Implicación para el ETL

El spider debe registrar los PDF enlazados desde la web (memoria, informe, sostenibilidad, catálogo), y Plata debe extraer su texto. Herramientas en [05](05-arquitectura-y-pipeline.md).
