# Descargas SCVS versionadas

Las descargas se hacen a mano desde los recursos oficiales (`docs/investigacion/05-adquisicion-de-datos.md`). No se hace scraping del portal SCVS.

| Paso | Acción |
| --- | --- |
| 1 | Guardar el archivo sin modificar en `crudo/<año>/` |
| 2 | Calcular el hash: `Get-FileHash .\crudo\2025\archivo.xlsx -Algorithm SHA256` |
| 3 | Agregar una fila a `MANIFEST.csv` con URL de origen, fecha de descarga, fecha de corte y hash |
| 4 | Registrar la descarga como evidencia en `docs/evidencias/registro.md` |

Un archivo crudo nunca se edita: una versión nueva de la SCVS es un archivo nuevo con su propia fila.
