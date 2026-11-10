# Registro de evidencias

Cada evidencia tiene un código, la fecha, el sprint, qué demuestra y dónde está. Los códigos `EV-A-NNN` son del Componente A y `EV-B-NNN`, del Componente B.

| Código | Fecha | Sprint | Evidencia | Qué demuestra | Ubicación |
| --- | --- | --- | --- | --- | --- |
| EV-A-001 | 2026-11-09 | 1 | Descarga del ranking SCVS 2025 y del catálogo CIIU con hash SHA-256 | Procedencia y reproducibilidad de los datos | [`MANIFEST.csv`](../../etl/datos/crudo/MANIFEST.csv) |
| EV-A-002 | 2026-11-09 | 1 | Script de selección del universo y reporte de calidad | El universo (14.029) y el piloto (500) se generan de forma reproducible | [`seleccionar_universo.py`](../../etl/universo/seleccionar_universo.py), [`calidad_2025.json`](../../etl/datos/universo/2025/calidad_2025.json) |
| EV-A-003 | 2026-11-09 | 1 | Listas top 50 por grupo y piloto de 500 | Cumplimiento de la tarea D3 de RN-02 | [`etl/datos/universo/2025/`](../../etl/datos/universo/2025/) |
| EV-A-004 | 2026-11-09 | 1 | Justificación del universo | Respuesta escrita a la pregunta del tribunal (RN-02, D4) | [13](../investigacion/13-justificacion-del-universo.md) |
| EV-A-005 | 2026-11-09 | 2 | Prototipo del pipeline de ingesta y consulta, con pruebas | Ingesta, fragmentación, indexación y respuesta con cita funcionando de extremo a extremo | [`rag/`](../../rag/README.md), [`rag/evidencias/`](../../rag/evidencias/) |
