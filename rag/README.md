# rag · Componente A

Asistente que responde preguntas sobre las empresas del Observatorio con cita de la fuente. Las cifras se piden a la API de B y el texto sale de los documentos que B expone.

```powershell
$env:PYTHONPATH = "rag/src"
python -m rag ingesta
python -m rag consulta "¿Qué empresas desarrollan software en Cuenca?"
```

Documentación del componente: [docs/componente-a](../docs/componente-a/README.md).
