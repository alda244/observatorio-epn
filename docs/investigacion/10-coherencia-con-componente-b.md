# 10. Coherencia entre las investigaciones de A y B

Corte: 03-nov-2026. Se contrasta la investigación del Componente A (`docs/investigacion/`, rama `main`) con la del Componente B (`docs/investigacion-b/` y ADR 0006–0007, rama `docs/investigacion-componente-b`, commit `3a0f8e9`). Ambas coinciden en fuentes, ética de recolección, frontera por API y stack; difieren en el dueño del texto de las fichas, la clasificación por tamaño y la infraestructura por defecto.

## Coincidencias

| Tema | A | B | Estado |
| --- | --- | --- | --- |
| Fuente de cifras | Descargas oficiales SCVS; sin scraping del portal SCVS ([05](05-adquisicion-de-datos.md)) | Ranking 2025 y tablas `bi_*` por descarga manual ([B-01](../investigacion-b/01-fuentes-y-universo.md)) | Coherente |
| Delimitación | Opción B: tecnológicas + G, C, K, M ([02](02-sectores-y-tamanos.md)) | Mismo universo, cuantificado en 14.042 empresas ([B-01](../investigacion-b/01-fuentes-y-universo.md)) | Coherente; B aporta las cifras |
| Esquema de ficha | Company Profile ([04](04-ficha-de-empresa.md), [RN-01](../reuniones/RN-01-ficha-alcance-antecedentes.md)) | Company Profile, Bloque 2 ([B-02](../investigacion-b/02-company-profile-bloque2.md)) | Coherente |
| Recolección web | robots.txt, bot identificado, límite de peticiones, solo texto institucional ([05](05-adquisicion-de-datos.md)) | Scrapling con `robots_txt_obey=True`, 1 petición por dominio cada 3 s ([B-06](../investigacion-b/06-scraping-etico.md)) | Coherente; B lo implementa y prueba |
| Citación | URL, fecha de captura y hash por campo | `fuente_url`, `fecha_captura`, `sha256`, `fuente_tipo` | Coherente |
| Frontera A/B | A consume la API de B; no lee el esquema de B | Igual | Coherente |
| Stack | Python 3.12, uv, FastAPI, PostgreSQL, pytest, ruff | Igual | Coherente |
| Antecedentes | Reinoso y Data Hub ([09](09-antecedentes-reinoso-datahub.md)) | Reinoso, Defaz, Escobar, Rojas | Coherente |

## Incoherencias y resolución propuesta

| Nº | Tema | Postura de A | Postura de B | Resolución propuesta | Acción |
| --- | --- | --- | --- | --- | --- |
| I1 | Dueño del texto de las fichas | A arma la ficha textual completa (decisión 5 de [08](08-agenda-de-negociacion.md); [04](04-ficha-de-empresa.md) v2) | B produce el Bloque 2; los bloques 1 y 3 quedan fuera de su alcance ([ADR 0006](../adr/0006-bloque2-company-profile-en-b.md)) | Aceptar ADR 0006 con la enmienda de la tabla siguiente: un solo recolector (el de B) para todas las páginas de cada empresa | Revisión de A en el PR de B; confirmación del director |
| I2 | Clasificación por tamaño | Usar el segmento oficial de la SCVS y no recalcular ([02](02-sectores-y-tamanos.md)) | La columna `Tamaño` del ranking 2025 viene vacía; se deriva por ventas (COPCI) y se marca `tamano_derivado` | Adoptar la postura de B, basada en la descarga real | [02](02-sectores-y-tamanos.md) actualizado |
| I3 | Infraestructura por defecto | AWS gestionado ([07](07-infraestructura-aws.md), versión del 20-oct) | Local y EPN por defecto; AWS como alternativa ([B-07](../investigacion-b/07-alternativa-aws.md)) | Desarrollo local para ambos; producción en la cuenta AWS de la EPN con la misma composición de contenedores | [07](07-infraestructura-aws.md) definitivo y [ADR 0008](../adr/0008-infraestructura-de-despliegue.md) |
| I4 | Capas Medallion frente al ADR 0002 | Un esquema y un rol por componente (`datos`, `asistente`) | Esquemas `bronce`, `plata`, `oro` | Esquemas `bronce`, `plata` y `oro` con propietario `rol_datos`; `rol_asistente` sin permisos sobre ellos. Reemplaza el nombre único `datos` del ADR 0002 mediante un ADR nuevo | Seguimiento ya anotado en ADR 0007 |
| I5 | Cargos directivos | Se guardan solo cargos ([04](04-ficha-de-empresa.md) v1) | Se excluyen en Plata ([B-06](../investigacion-b/06-scraping-etico.md)) | Excluirlos: no aportan a los casos de uso y reducen el riesgo frente a la LOPDP | [04](04-ficha-de-empresa.md) actualizado |
| I6 | Etiqueta del sector K | "K/M Servicios" ([02](02-sectores-y-tamanos.md)) | K = financieras y seguros; M = profesionales | Usar la nomenclatura CIIU Rev. 4 de B | [02](02-sectores-y-tamanos.md) actualizado |
| I7 | Tamaño del corpus | 600–1.500 empresas con ficha ([07](07-infraestructura-aws.md), 20-oct) | Piloto de ~500 empresas | Dimensionar sobre el piloto de 500, con margen hasta 1.500 | [07](07-infraestructura-aws.md) definitivo |
| I8 | LLM para textos `derivado` | LLM por interfaz compatible con OpenAI (ADR 0004) | "Bedrock, con la misma interfaz que use A" | Un único proveedor y una única cuenta para ambos componentes | [ADR 0008](../adr/0008-infraestructura-de-despliegue.md) |
| I9 | Periodo de cifras | Serie comparable 2012–2025 ([03](03-periodo-de-analisis.md)) | Solo el ranking 2025 descargado | Sin conflicto, pero B debe fijar qué años carga en el Sprint 2; Reinoso demuestra la ruta 2017–2023 | Punto para el plan de B |

### Enmienda propuesta al ADR 0006

| Elemento | Propuesta |
| --- | --- |
| Recolector | El spider de B captura, una sola vez por empresa, portada, "nosotros", "servicios/productos" y PDF oficiales |
| Campos estructurados | B produce los campos del Company Profile que salen de forma directa del HTML, el JSON-LD `Organization` o la SCVS: Bloque 1 (nombre, web, contacto corporativo, ubicación), Bloque 2 completo y logotipo del Bloque 3 |
| Documentos para el índice | B expone el texto limpio (capa Plata) de cada página capturada, con URL, fecha y hash, en una ruta nueva `GET /empresas/{expediente}/documentos` |
| Rol de A | A indexa esos documentos y los del propio Observatorio, deriva palabras clave y responde sobre misión, visión, historia y certificaciones con citación, sin un segundo recolector |
| Encaje con el plan F_AA_234A de A | El plan de A define el corpus como reportes, indicadores y recursos del Observatorio; la recolección de webs de empresas no figura en sus tareas, por lo que la enmienda no recorta objetivos aprobados |

## Inconsistencias del repositorio (ambas ramas)

| Elemento referenciado | Dónde se cita | Estado |
| --- | --- | --- |
| ADR 0001–0005 | `docs/adr/README.md`, ADR 0006 y 0007 | No existen en ninguna rama |
| `docs/arquitectura/pendientes.md` | `docs/arquitectura/README.md` | No existe |
| `docs/sprints/`, `docs/evidencias/`, `docs/evaluacion/` | `docs/README.md` | No existen |
| `scripts/dev.ps1`, `scripts/test.ps1`, `docker-compose.yml`, `.env.example`, `CODEOWNERS` | READMEs de módulos | No existen |
| `contracts/openapi.yaml` | `contracts/README.md`, ADR 0006 | No existe |
| `docs/investigacion/README.md` y `docs/README.md` | Modificados en las dos ramas | Conflicto previsible al fusionar; se resuelve conservando ambas filas |
