# Investigación de alcance: Portal de Datos Abiertos y Analítica de Indicadores (Componente B)

Corte: 03-nov-2026 · Responsable: Eduardo Miguel Muzo Cansigña · Director: Enrique Andrés Larco Ampudia, PhD.

Este conjunto define cómo obtener, procesar y publicar los datos del Componente B: cifras de la SCVS y el Bloque 2 del formato *Company Profile* (tagline, descripción, productos y servicios). Complementa la investigación del Componente A en [`../investigacion/`](../investigacion/README.md).

## Documentos

| Nº | Archivo | Pregunta que responde |
| --- | --- | --- |
| 1 | [01-fuentes-y-universo.md](01-fuentes-y-universo.md) | ¿Qué trae la SCVS y cuántas empresas entran? |
| 2 | [02-company-profile-bloque2.md](02-company-profile-bloque2.md) | ¿Qué campos del Company Profile se llenan y con qué reglas? |
| 3 | [03-fuentes-bloque2.md](03-fuentes-bloque2.md) | ¿De dónde sale el texto de cada empresa? |
| 4 | [04-descubrimiento-de-urls.md](04-descubrimiento-de-urls.md) | ¿Cómo se encuentra la web oficial de cada empresa? |
| 5 | [05-arquitectura-y-pipeline.md](05-arquitectura-y-pipeline.md) | ¿Cómo se organiza el ETL y qué herramientas usa? |
| 6 | [06-scraping-etico.md](06-scraping-etico.md) | ¿Cómo se recolecta la web sin incumplir normas? |
| 7 | [07-alternativa-aws.md](07-alternativa-aws.md) | ¿Cómo sería el mismo pipeline sobre AWS? |
| 8 | [08-plan-y-negociacion.md](08-plan-y-negociacion.md) | ¿Qué decidir en la reunión de seguimiento y qué sigue? |

## Propuestas a negociar

| Tema | Propuesta | Detalle |
| --- | --- | --- |
| Universo | Tecnológicas J61–J63 y J582 + G, C, K, M medianas y grandes (14.042 empresas) | [01](01-fuentes-y-universo.md) |
| Alcance del Bloque 2 | Piloto de ~500: 300 tecnológicas medianas y grandes + top 50 por ventas de G, C, K, M | [01](01-fuentes-y-universo.md), [08](08-plan-y-negociacion.md) |
| Campos | Tagline, descripción y productos/servicios, cada uno con URL, fecha y origen `literal`/`derivado` | [02](02-company-profile-bloque2.md) |
| Fuentes de texto | Web oficial y PDF oficiales primero; prensa y terceros solo como respaldo marcado | [03](03-fuentes-bloque2.md) |
| Arquitectura | Medallion (bronce/plata/oro) en PostgreSQL + pipeline Python por comandos + CI en GitHub Actions; sin Airflow | [05](05-arquitectura-y-pipeline.md) |
| Recolección web | Scrapling configurado: robots.txt, bot identificado, 1 petición por dominio cada 3 s | [06](06-scraping-etico.md) |
| Nube | Local y EPN por defecto; AWS como alternativa | [07](07-alternativa-aws.md) |
| Frontera A/B | El Bloque 2 lo produce B y lo sirve por `/empresas/{expediente}`; A lo consume | [08](08-plan-y-negociacion.md) |

## Insumos de origen

| Insumo | Tipo |
| --- | --- |
| Formulario F_AA_233A del proyecto "Servicios Inteligentes y Datos Abiertos para el Observatorio" | Documento oficial EPN |
| Plan F_AA_234A de Eduardo Miguel Muzo Cansigña | Documento oficial EPN |
| Formato "Company Profile" (DTIC) | Formato de referencia del proyecto |
| Ranking SCVS 2025 (Excel, corte 22-oct-2026) y tablas `bi_compania`, `bi_ciiu`, `bi_segmento` | Descarga oficial SCVS |
| TIC de Escobar, Defaz y Rojas (EPN, jul-2026) y tesis de maestría de Reinoso (EPN, jul-2025) | Documentos académicos EPN |
| Piloto de 10 empresas (`piloto_bloque2.csv`) y spider probado (`spider_bloque2.py`) | Evidencia propia, 03-nov-2026 |
