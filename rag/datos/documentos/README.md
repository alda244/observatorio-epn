# Documentos para el índice

Cada archivo `.md` de esta carpeta entra al índice en la siguiente ingesta. Debe empezar con un encabezado de metadatos:

```markdown
---
titulo: Nombre del documento
fuente_url: https://url-oficial-de-origen
fuente_tipo: reporte_observatorio | company_profile | web_oficial
fecha: AAAA-MM-DD
origen: literal | derivado
expediente: 384            # opcional, si el documento es de una empresa
---
Texto del documento...
```

Sin `titulo`, `fuente_url`, `fuente_tipo` o `fecha`, la ingesta se detiene: ningún texto entra al índice sin procedencia.
