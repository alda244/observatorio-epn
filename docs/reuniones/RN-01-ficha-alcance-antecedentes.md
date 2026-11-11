# RN-01 · Ficha de empresa, alcance y antecedentes

| Campo | Valor |
| --- | --- |
| Fecha | Reuniones de octubre y noviembre de 2026, consolidadas a partir de transcripciones |
| Participantes | Enrique Andrés Larco Ampudia, PhD. (director); Alicia Dayana Pereira Tuqueres (Componente A); Eduardo Miguel Muzo Cansigña (Componente B) |
| Material entregado | `Company Profile DTIC.docx` (03-nov-2026), memorias TIC de FragUI y Data Hub EPN, tesis de maestría de Paúl Reinoso |

## Visión del producto

El producto se concibe como un directorio comercial digital, análogo a las antiguas páginas amarillas: un medio para localizar con rapidez a una empresa que ofrece un producto o servicio, conocer su ubicación y contactarla. Sobre ese catálogo se construye la analítica descriptiva, diagnóstica, predictiva y prescriptiva del comportamiento del comercio ecuatoriano.

| Planteamiento | Consecuencia para el Componente A |
| --- | --- |
| El catálogo debe servir a la facultad y a futuras generaciones (oportunidades de negocio, contactos, pasantías) | El asistente debe atender consultas del tipo "¿qué empresas ofrecen X?", además de consultas sobre una empresa concreta |
| Ejemplo: mayoristas de computación que incorporaron generadores eléctricos y baterías portátiles a su oferta | Las fichas conservan la fecha de captura para comparar la oferta en el tiempo |
| La inteligencia artificial constituye un cambio de época comparable al fuego, la agricultura, la industrialización y la digitalización; el Observatorio estudia ese cambio en las empresas | Marco de la motivación en el capítulo 1 de la memoria |
| La pandemia aceleró la transformación digital: algunas empresas se reinventaron y otras cerraron | Pregunta analítica posible para B; contexto para A |
| Se identificó como práctica deficiente de experiencia de usuario una plataforma de cursos que exige registro antes de mostrar contenido | El widget no exige registro para consultar |

## Decisiones

| Nº | Tema | Decisión | Estado | Documento afectado |
| --- | --- | --- | --- | --- |
| D1 | Esquema de la ficha | De tres esquemas presentados (tradicional por identidad, oferta y operación; Company Profile para plataforma digital; perfil de negocio local con horarios, pagos, fotografías y reseñas), se eligió el **Company Profile** por su descripción de alto impacto y su orientación a plataformas digitales | Decidido | [04](../investigacion/04-ficha-de-empresa.md) |
| D2 | Activos visuales | Se descartan las fotografías de fachada y las reseñas; se conserva el logotipo por su facilidad de obtención | Decidido | [04](../investigacion/04-ficha-de-empresa.md) |
| D3 | Repositorio | Un único repositorio para ambos componentes, con comunicación entre ellos | Decidido | [ADR 0001](../adr/README.md) |
| D4 | Plan TIC | El plan vigente es un borrador; se cierra en el semestre, cuando estén definidas las empresas, las herramientas y la plataforma. Se entregan la memoria del TIC y el plan | Decidido | — |
| D5 | Fuentes de cifras | SCVS y Banco Central del Ecuador, según el antecedente de Reinoso | Decidido | [01](../investigacion/01-fuente-scvs.md), [09](../investigacion/09-antecedentes-reinoso-datahub.md) |
| D6 | Bibliografía | Últimos cinco años, salvo obras seminales | Decidido | [03](../investigacion/03-periodo-de-analisis.md) |

## Puntos abiertos

| Nº | Tema | Planteamiento | Propuesta del equipo |
| --- | --- | --- | --- |
| P1 | Delimitación de empresas | Por tamaño (por ejemplo, dos de los cuatro tamaños) o por sector (por ejemplo, cuatro de siete sectores); interés principal en las tecnológicas, sin descuidar industria y agro, servicios y comercio | Opción B de [02](../investigacion/02-sectores-y-tamanos.md): sector como eje y tamaño como filtro; 14.042 empresas en el universo y ~500 en el piloto |
| P2 | Volumen de fichas | Depende de la capacidad del equipo; la recolección web automatizada amplía lo viable; plazo de nueve meses | Piloto de ~500 empresas ([B-08](../investigacion-b/08-plan-y-negociacion.md)) |
| P3 | Integración con el portal | Se coordinará con el equipo del portal para evitar tecnologías incompatibles | Presentar el stack de [06](../investigacion/06-arquitectura-e-integracion.md) en esa reunión |
| P4 | Documentación publicada en web | El equipo de FragUI publicó su documentación como sitio web, práctica que se considera replicable | Evaluar MkDocs Material sobre `docs/` mediante un ADR |
| P5 | Contacto con Paúl Reinoso | Se dispone de un canal de contacto | Solicitar los notebooks de los anexos A1–A3 y las tablas unificadas 2017–2023 |
| P6 | Reparto del Company Profile entre A y B | No se trató de forma explícita | B recolecta y estructura; A indexa y responde ([10](../investigacion/10-coherencia-con-componente-b.md), I1) |

## Tareas

| Tarea | Responsable | Entregable |
| --- | --- | --- |
| Rediseñar la ficha con el esquema Company Profile | Pereira | [04](../investigacion/04-ficha-de-empresa.md) v2 y 20 fichas piloto |
| Contar empresas por CIIU y tamaño en el ranking 2025 | Muzo | Realizado: [B-01](../investigacion-b/01-fuentes-y-universo.md) |
| Revisar los antecedentes (Reinoso, Data Hub, FragUI) | Pereira | [09](../investigacion/09-antecedentes-reinoso-datahub.md) |
| Solicitar los archivos de Reinoso | Pereira | Insumos en `etl/datos/crudo/` o enlace |
| Verificar la coherencia entre las investigaciones de A y B | Pereira | [10](../investigacion/10-coherencia-con-componente-b.md) |
