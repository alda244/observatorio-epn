# Casos de uso

El asistente sirve a quien busca empresas o datos sobre ellas, sin registro. Cada caso tiene preguntas de referencia en [`preguntas_referencia.json`](../../rag/evaluacion/preguntas_referencia.json), agrupadas por tipo.

| Actor | Qué busca |
| --- | --- |
| Estudiante o egresado | Empresas para pasantías o empleo, por sector y ciudad |
| Emprendedor o empresa | Proveedores, clientes o competidores que ofrecen algo concreto |
| Investigador del Observatorio | Datos de una empresa o de un sector, con su fuente |
| Público general | Información básica de una empresa conocida |
| Gobierno y entidades públicas | Tamaño y evolución de un sector o territorio, para el análisis y la toma de decisiones |

El actor Gobierno agrupa a ministerios, gobiernos locales, agencias de fomento y gremios que diseñan o evalúan políticas productivas. A diferencia de los demás actores, no busca una empresa concreta sino el agregado: cuántas empresas hay, cuánto venden y cómo cambió en el tiempo. Las cifras 2012–2025 que publica la API de B permiten responder esas preguntas con la misma regla de cita que el resto.

## Casos

| Nº | Caso | Ejemplo | Qué responde el asistente | Tipo de pregunta |
| --- | --- | --- | --- | --- |
| CU-01 | Conocer una empresa | "¿A qué se dedica Sofka?" | Actividad, ubicación y sector, con cita | `nombre` |
| CU-02 | Encontrar empresas por actividad | "¿Quién procesa pagos electrónicos?" | Lista de empresas con su actividad y cita | `actividad` |
| CU-03 | Encontrar empresas por actividad y lugar | "Empresas de tecnología en Manta" | Lista filtrada por ciudad o provincia | `actividad_lugar` |
| CU-04 | Consultar cifras | "¿Cuánto vendió Pronaca en 2025?" | Cifra de la API de B con fecha de corte; advertencia si el dato de empleados es dudoso | `cifra` |
| CU-05 | Conocer el perfil de una empresa | "¿Cuál es la misión de Pronaca?" | Lema, descripción, productos o contacto corporativo desde la ficha de B. Si no están: "no hay dato publicado" | `sin_dato`; pendiente: `perfil` |
| CU-06 | Comparar sectores | "¿Cuánto vende en promedio una tecnológica mediana?" | Indicador de `GET /indicadores` con su fuente | Pendiente: depende de la API de B |
| CU-07 | Preguntar algo fuera del Observatorio | "¿Cuál es la capital de Francia?" | "No hay dato publicado" | `fuera_de_alcance` |
| CU-08 | Dimensionar un sector o territorio | "¿Cuántas tecnológicas grandes hay en Pichincha?" | Conteo de `GET /v1/empresas` con los filtros de la pregunta, el universo y la fecha de corte | Pendiente: `agregado` |
| CU-09 | Seguir la evolución de una empresa | "¿Cómo cambiaron las ventas de Telconet entre 2015 y 2025?" | Serie de `cifras` de `GET /v1/empresas/{expediente}`, con la fuente de cada ejercicio | Pendiente: `serie` |

| Actor | Casos principales |
| --- | --- |
| Estudiante o egresado | CU-02, CU-03 |
| Emprendedor o empresa | CU-02, CU-05 |
| Investigador del Observatorio | CU-04, CU-06, CU-09 |
| Público general | CU-01, CU-05 |
| Gobierno y entidades públicas | CU-06, CU-08, CU-09 |

## Reglas comunes

| Regla | Caso que protege |
| --- | --- |
| Cada afirmación cita la fuente con URL y fecha | Todos |
| Las cifras se piden a la API de B | CU-04, CU-06, CU-08, CU-09 |
| Un conteo o un promedio indica el universo (14.029 empresas del ranking 2025) y no se presenta como dato de todo el país | CU-06, CU-08 |
| Una serie muestra los ejercicios disponibles y avisa si falta alguno | CU-09 |
| Si la pregunta pide un campo que ninguna fuente contiene, no se responde | CU-05 |
| Sin respaldo suficiente, no se responde | CU-07 |
| No se muestran datos personales; solo contacto corporativo | CU-05 |
