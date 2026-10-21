# portal-datos · Componente B

Dueño: Eduardo Muzo. Interfaz de publicación y consulta de conjuntos de datos abiertos.

**Estado: pendiente de decisión.** El plan F_AA_234A de B evalúa en el Sprint 1 tres alternativas: CKAN, desarrollo propio o enfoque híbrido. La elección se registra como ADR en `docs/adr/` y solo entonces esta carpeta recibe código, configuración y su job de CI.

| Pregunta abierta | Por qué importa |
| --- | --- |
| ¿CKAN, propio o híbrido? | CKAN agrega servicios (Solr, Redis) a `docker-compose.yml` |
| ¿Interfaz propia o páginas dentro del portal del Observatorio? | Define si se usa FragUI |
| ¿Cómo se publican los metadatos DCAT? | Depende de la alternativa elegida |
