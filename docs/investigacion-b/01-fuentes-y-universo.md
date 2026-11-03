# 1. Fuentes SCVS y universo de empresas

La SCVS entrega cifras y clasificación de todas las sociedades. El ranking 2025 trae 154.813 compañías con CIIU de 6 niveles, empleados y ventas; con eso se define el universo del Bloque 2.

## Archivos disponibles (descarga manual, 03-nov-2026)

| Archivo | Filas | Campos clave | Uso |
| --- | --- | --- | --- |
| `ranking_2025.xlsx` (hoja `Ranking2025`, corte 22-oct-2026) | 154.813 | Expediente, nombre, tipo, actividad (CIIU + texto), región, provincia, ciudad, tamaño, sector, empleados, activo, patrimonio, ventas, utilidades, IR, ingreso total | Cifras e indicadores; universo |
| `bi_compania.csv` | 347.421 | Expediente, RUC, nombre, tipo, provincia | Llave RUC ↔ expediente; universo histórico (activas e inactivas) |
| `bi_ciiu.csv` | 3.058 | Código CIIU (1 a 6 niveles) y descripción | Dimensión CIIU |
| `bi_segmento.csv` | 5 | Micro, pequeña, mediana, grande, no definido | Dimensión tamaño |

El 100 % de los expedientes del ranking cruza con `bi_compania`.

## Hallazgos de calidad

| Hallazgo | Efecto | Tratamiento propuesto |
| --- | --- | --- |
| Columna `Tamaño` vacía en las 154.813 filas | No se puede filtrar por segmento oficial | Derivar por ventas (COPCI) y marcar `tamano_derivado`; pedir el segmento a la SCVS |
| Encabezado en 2 filas (título con fecha de corte + nombres) | Lectura directa falla | Leer con `header=1` y guardar la fecha de corte como metadato |
| Columna `Activio` mal escrita | Mapeo de cuentas | Renombrar en Plata |
| 38 % de filas con ventas = 0 | Caen en micro al derivar tamaño | Marcar `sin_ventas` y revisar contra activos |
| 30 filas con año 0 | Registros incompletos | Excluir y registrar en el reporte de calidad |
| CIIU y descripción en una sola columna (`C1010.11 - ...`) | Joins con `bi_ciiu` | Separar código y texto en Plata |

## Universo propuesto (opción B de [`../investigacion/02`](../investigacion/02-sectores-y-tamanos.md))

Tamaño derivado por ventas: mediana USD 1–5 millones; grande, más de USD 5 millones.

| Grupo | Todas | Medianas | Grandes | Entra al universo |
| --- | --- | --- | --- | --- |
| Tecnológicas J61, J62, J63, J582 | 5.901 | 237 | 63 | Todas (5.901) |
| G Comercio | 37.231 | 3.453 | 1.766 | Medianas y grandes (5.219) |
| C Manufactura | 9.971 | 1.040 | 710 | Medianas y grandes (1.750) |
| M Profesionales | 21.936 | 546 | 108 | Medianas y grandes (654) |
| K Financieras y seguros | 3.909 | 330 | 188 | Medianas y grandes (518) |
| **Total** | | | | **14.042** |

Detalle tecnológico: J61 1.986 · J62 3.213 · J63 542 · J582 160.

Archivo resultante: `universo_bloque2.csv` (expediente, nombre, CIIU, grupo, tamaño derivado, provincia, ciudad, empleados, ventas 2025 y columnas vacías para la URL oficial).

## Por qué hace falta acotar

Cada empresa necesita su web oficial, que la SCVS no publica ([04](04-descubrimiento-de-urls.md)). Con 14.042 empresas, esa búsqueda domina el costo del proyecto; por eso se propone un piloto de ~500 ([08](08-plan-y-negociacion.md)).
