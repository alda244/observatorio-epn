# Casos de uso

El asistente sirve a quien busca empresas o datos sobre ellas, sin registro. Cada caso tiene preguntas de referencia en [`preguntas_referencia.json`](../../rag/evaluacion/preguntas_referencia.json), agrupadas por tipo.

| Actor | Qué busca |
| --- | --- |
| Estudiante o egresado | Empresas para pasantías o empleo, por sector y ciudad |
| Emprendedor o empresa | Proveedores, clientes o competidores que ofrecen algo concreto |
| Investigador del Observatorio | Datos de una empresa o de un sector, con su fuente |
| Público general | Información básica de una empresa conocida |

## Casos

| Nº | Caso | Ejemplo | Qué responde el asistente | Tipo de pregunta |
| --- | --- | --- | --- | --- |
| CU-01 | Conocer una empresa | "¿A qué se dedica Sofka?" | Actividad, ubicación y sector, con cita | `nombre` |
| CU-02 | Encontrar empresas por actividad | "¿Quién procesa pagos electrónicos?" | Lista de empresas con su actividad y cita | `actividad` |
| CU-03 | Encontrar empresas por actividad y lugar | "Empresas de tecnología en Manta" | Lista filtrada por ciudad o provincia | `actividad_lugar` |
| CU-04 | Consultar cifras | "¿Cuánto vendió Pronaca en 2025?" | Cifra de la API de B con fecha de corte; advertencia si el dato de empleados es dudoso | `cifra` |
| CU-05 | Conocer el perfil de una empresa | "¿Cuál es la misión de Pronaca?" | Misión, productos, contacto o certificaciones desde los documentos de B. Si no están: "no hay dato publicado" | `sin_dato` hasta que B exponga los documentos |
| CU-06 | Comparar sectores | "¿Cuánto vende en promedio una tecnológica mediana?" | Indicador de `GET /indicadores` con su fuente | Pendiente: depende de la API de B |
| CU-07 | Preguntar algo fuera del Observatorio | "¿Cuál es la capital de Francia?" | "No hay dato publicado" | `fuera_de_alcance` |

## Reglas comunes

| Regla | Caso que protege |
| --- | --- |
| Cada afirmación cita la fuente con URL y fecha | Todos |
| Las cifras se piden a la API de B | CU-04, CU-06 |
| Si la pregunta pide un campo que ninguna fuente contiene, no se responde | CU-05 |
| Sin respaldo suficiente, no se responde | CU-07 |
| No se muestran datos personales; solo contacto corporativo | CU-05 |
