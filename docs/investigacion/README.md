# Investigación de alcance: Asistente RAG del Observatorio (Componente A)

Corte: 20-oct-2026 · Responsable: Alicia Pereira · Director: Enrique Andrés Larco Ampudia, PhD.

Este conjunto resume la investigación preliminar con la que se negocian con el director los términos del asistente RAG: fuentes, sectores, periodo, ficha de empresa, adquisición de datos, integración e infraestructura.

## Documentos

| Nº | Archivo | Pregunta que responde |
| --- | --- | --- |
| 1 | [01-fuente-scvs.md](01-fuente-scvs.md) | ¿Qué ofrece la Superintendencia de Compañías como fuente? |
| 2 | [02-sectores-y-tamanos.md](02-sectores-y-tamanos.md) | ¿Qué sectores y tamaños de empresa abarcar? |
| 3 | [03-periodo-de-analisis.md](03-periodo-de-analisis.md) | ¿Es viable analizar desde 2006? |
| 4 | [04-ficha-de-empresa.md](04-ficha-de-empresa.md) | ¿Qué datos se extraen de los canales oficiales de cada empresa? |
| 5 | [05-adquisicion-de-datos.md](05-adquisicion-de-datos.md) | ¿Cómo obtener los datos de forma legal y ética? |
| 6 | [06-arquitectura-e-integracion.md](06-arquitectura-e-integracion.md) | ¿Cómo se integra con el Componente B y el portal en curso? |
| 7 | [07-infraestructura-aws.md](07-infraestructura-aws.md) | ¿Qué infraestructura solicitar? |
| 8 | [08-agenda-de-negociacion.md](08-agenda-de-negociacion.md) | ¿Qué decidir en la reunión y qué sigue? |

## Propuestas a negociar

| Tema | Propuesta | Detalle |
| --- | --- | --- |
| Sectores | Tecnológicas (CIIU J61–J63, J582) a fondo + comercio, manufactura y servicios como capa comparativa | [02](02-sectores-y-tamanos.md) |
| Tamaños | Cifras para todos los tamaños; ficha textual solo para medianas, grandes y tecnológicas con web | [02](02-sectores-y-tamanos.md) |
| Periodo | Serie comparable 2012–2025; 2006–2011 como serie histórica marcada | [03](03-periodo-de-analisis.md) |
| Fuentes de cifras | Descargas oficiales de la SCVS y convenio institucional; sin scraping del portal SCVS | [05](05-adquisicion-de-datos.md) |
| Frontera A/B | B carga y expone cifras por API; A indexa texto oficial y consume la API de B | [06](06-arquitectura-e-integracion.md) |
| Despliegue | Widget embebible en el portal, construido con el stack de FragUI, sobre AWS de la EPN | [06](06-arquitectura-e-integracion.md), [07](07-infraestructura-aws.md) |

## Insumos de origen

| Insumo | Tipo |
| --- | --- |
| Formulario F_AA_233A del proyecto "Servicios Inteligentes y Datos Abiertos para el Observatorio" | Documento oficial EPN |
| Transcripciones de reuniones con el director (oct-2026) | Notas internas |
| TIC de E. Armas, "Componentes para entrada de datos y formularios… (FragUI)", EPN, jul-2026, y su plan F_AA_234A | Documento académico EPN |
