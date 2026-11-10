# RN-02 · Sectores aprobados y justificación del universo

| Campo | Valor |
| --- | --- |
| Fecha | 04-nov-2026 |
| Participantes | Enrique Andrés Larco Ampudia, PhD. (director); Alicia Dayana Pereira Tuqueres (Componente A); Eduardo Miguel Muzo Cansigña (Componente B) |
| Fuente | Transcripción automática de la reunión; las intervenciones se parafrasean |
| Material revisado | Tablero del ranking empresarial de la SCVS, clasificación por secciones CIIU, repositorio `observatorio-epn` |

## Temas tratados

| Tema | Planteamiento del director |
| --- | --- |
| Datos de la SCVS | Se revisó el tablero del ranking 2025. El director señaló que algunos datos parecen erróneos: Tiendas Tuti aparece con 8 empleados y ventas de más de USD 1.000 millones, cuando solo un local tiene alrededor de cuatro empleados. Sugirió consultar a la SCVS cómo se calcula ese campo |
| Sectores grandes | Observó que entre las empresas de mayores ventas predominan sectores distintos del tecnológico |
| Núcleo tecnológico | Revisó la sección J y reconoció en ella a las operadoras de telecomunicaciones del ranking (Conecel, Telconet, Puntonet) |
| Sectores seleccionados | El equipo presentó las secciones elegidas: J (tecnología), G (comercio), C (manufactura), M (actividades profesionales) y K (actividades financieras) |
| Justificación | Anticipó la pregunta del tribunal: por qué se eligen cinco secciones y no todas, de la A a la U. Pidió una justificación escrita basada en el foco tecnológico del equipo (pasantías y trabajos), en la incidencia del uso de tecnología en esos sectores y en los recursos y el tiempo disponibles para dos estudiantes |
| Trabajo futuro | Recomendó dejar en la memoria una sección de trabajo futuro con las secciones no cubiertas |
| Documentación | Valoró que la documentación del repositorio esté organizada por temas, porque se puede trasladar a la memoria en LaTeX |

## Decisiones

| Nº | Tema | Decisión | Estado | Documento |
| --- | --- | --- | --- | --- |
| D1 | Sectores | Se aprueban las secciones J (núcleo tecnológico J61, J62, J63, J582), G, C, M y K | Decidido | [12](../investigacion/12-universo-aprobado.md) |
| D2 | Universo | Tecnológicas de todos los tamaños + medianas y grandes de G, C, M y K (14.042 empresas) | Decidido | [12](../investigacion/12-universo-aprobado.md) |
| D3 | Listas | Para la siguiente reunión se presentan las listas de empresas: top 50 de cada grupo y las 300 tecnológicas medianas y grandes | Decidido | [`etl/datos/universo/2025/`](../../etl/datos/universo/2025/) |
| D4 | Justificación | Se redacta la justificación de la selección con su trabajo futuro | Decidido | [13](../investigacion/13-justificacion-del-universo.md) |

## Puntos abiertos

| Nº | Tema | Propuesta del equipo |
| --- | --- | --- |
| P1 | Holdings en el grupo K | Excluirlos del top 50 de K (no tienen oferta comercial) y mantenerlos en el universo con cifras ([13](../investigacion/13-justificacion-del-universo.md)) |
| P2 | Bancos y aseguradoras | No están en el ranking de la SCVS; el grupo K se describe con lo que contiene y la banca queda como trabajo futuro |
| P3 | Dato de empleados | Consultar a la SCVS cómo se define; mientras tanto, el tamaño se deriva por ventas y se marca `alerta_empleados` |
| P4 | Fuente oficial sobre adopción de TIC por sector | Citar las tablas del módulo TIC de la ENESEM (INEC) en la justificación |

## Tareas

| Tarea | Responsable | Entregable |
| --- | --- | --- |
| Generar las listas top 50 por grupo y el piloto de 500 | Pereira | Realizado: `etl/universo/seleccionar_universo.py` y `etl/datos/universo/2025/` |
| Redactar la justificación del universo | Pereira | Realizado: [13](../investigacion/13-justificacion-del-universo.md), pendiente de revisión |
| Prototipo del pipeline de ingesta del asistente | Pereira | `rag/` (Sprint 2 adelantado) |
| Revisar las listas y la regla de holdings | Muzo | Comentarios en el PR |
| Encontrar las webs oficiales del piloto | Muzo | Columnas `url_*` de `piloto_500.csv` |
