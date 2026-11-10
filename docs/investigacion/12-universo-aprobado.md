# 12. Universo de empresas aprobado

| Campo | Valor |
| --- | --- |
| Estado | **Aprobado** por el director en la reunión del 04-nov-2026 ([RN-02](../reuniones/RN-02-sectores-aprobados-y-justificacion.md)) |
| Fuente | Ranking empresarial SCVS 2025, corte 22-oct-2026 (`etl/datos/crudo/2025/ranking_2025.xlsx`) |
| Reproducción | `python etl/universo/seleccionar_universo.py` |
| Justificación | [13-justificacion-del-universo.md](13-justificacion-del-universo.md) |

Este documento resume qué empresas abarca el Observatorio y con qué profundidad. Reemplaza, como versión aprobada, a las opciones de [02](02-sectores-y-tamanos.md) y al conteo de [B-01](../investigacion-b/01-fuentes-y-universo.md).

## En una frase

El Observatorio cubre **cinco grupos de actividad económica**. Del grupo tecnológico entran todas las empresas; de los otros cuatro, las medianas y las grandes. Eso da **14.042 empresas con cifras** (14.029 tras eliminar duplicados). De ellas, **500 forman el piloto con ficha completa (Company Profile)**.

## Sectores abarcados (CIIU Rev. 4)

| Grupo | Sección CIIU | Qué incluye | Papel en el Observatorio |
| --- | --- | --- | --- |
| **Tecnológicas** | J61, J62, J63, J582 | Telecomunicaciones, desarrollo y consultoría de software, servicios de información, edición de software | Núcleo del estudio: productoras de tecnología |
| **Comercio** | G | Mayoristas, minoristas, supermercados, vehículos | Comparación: principal sector por ventas |
| **Manufactura** | C | Industria, incluida la agroindustria | Comparación: industria y agro |
| **Actividades profesionales** | M | Consultoría, ingeniería, publicidad, investigación | Comparación: servicios basados en conocimiento |
| **Actividades financieras** | K | Medicina prepagada, servicios auxiliares financieros, fiduciarias, casas de valores, holdings | Comparación: servicios financieros bajo control de la SCVS |

### Núcleo tecnológico en detalle

| Código | Actividad | Empresas en el ranking 2025 |
| --- | --- | --- |
| J61 | Telecomunicaciones | 1.986 |
| J62 | Programación, consultoría informática y actividades conexas | 3.213 |
| J63 | Servicios de información | 542 |
| J582 | Edición de programas informáticos | 160 |
| **Total** | | **5.901** |

## Criterio de tamaño

La columna `Tamaño` del ranking 2025 viene vacía en todas las filas. Por eso el tamaño se **deriva de las ventas anuales** según el COPCI y se marca como `tamano_derivado`. No se usa el número de empleados (ver [13](13-justificacion-del-universo.md#calidad-del-dato-de-empleados)).

| Tamaño derivado | Ventas anuales 2025 |
| --- | --- |
| Micro y pequeña | Hasta USD 1.000.000 |
| Mediana | Más de USD 1.000.000 y hasta USD 5.000.000 |
| Grande | Más de USD 5.000.000 |

## Universo con cifras

| Grupo | Total en el ranking | Medianas | Grandes | Criterio | Universo aprobado | Universo depurado |
| --- | --- | --- | --- | --- | --- | --- |
| Tecnológicas | 5.901 | 237 | 63 | Todas | 5.901 | 5.899 |
| G Comercio | 37.231 | 3.453 | 1.766 | Medianas y grandes | 5.219 | 5.210 |
| C Manufactura | 9.971 | 1.040 | 710 | Medianas y grandes | 1.750 | 1.749 |
| M Profesionales | 21.936 | 546 | 108 | Medianas y grandes | 654 | 654 |
| K Financieras | 3.909 | 330 | 188 | Medianas y grandes | 518 | 517 |
| **Total** | **78.948** | | | | **14.042** | **14.029** |

El universo aprobado es el conteo presentado al director. El universo depurado elimina 13 expedientes que el archivo de la SCVS repite en filas idénticas; es el que usan los sistemas.

| Indicador | Valor |
| --- | --- |
| Sociedades en el ranking 2025 | 154.813 filas (154.687 expedientes únicos) |
| Participación del universo en las ventas de todas las sociedades | 62,6 % |
| Participación del piloto en las ventas de todas las sociedades | 25,3 % |

## Piloto con ficha completa (500 empresas)

La ficha Company Profile requiere encontrar y verificar la web oficial de cada empresa, una tarea que la SCVS no resuelve. Por eso se trabaja primero con un piloto de 500 empresas.

| Componente del piloto | Regla | Empresas | Ventas del grupo cubiertas |
| --- | --- | --- | --- |
| Tecnológicas | Todas las medianas y grandes | 300 | 88,6 % |
| G Comercio | Top 50 por ventas 2025 | 50 | 36,6 % |
| C Manufactura | Top 50 por ventas 2025 | 50 | 44,4 % |
| M Profesionales | Top 50 por ventas 2025 | 50 | 42,0 % |
| K Financieras | Top 50 por ventas 2025, sin sociedades de cartera (holdings) | 50 | 29,0 % |
| **Total** | | **500** | |

Además se publica el **top 50 tecnológico**, un subconjunto de las 300, para comparar los cinco grupos con el mismo número de empresas.

### Las cinco primeras de cada lista

| Grupo | Empresas (por ventas 2025) | Ventas de la nº 50 |
| --- | --- | --- |
| Tecnológicas | Conecel, Otecel, Telconet, Setel, Puntonet | USD 6,6 M |
| G Comercio | Corporación Favorita, Corporación El Rosado, Primax Comercial, Dinadec, Tiendas Tuti | USD 187,9 M |
| C Manufactura | Pronaca, Sociedad Nacional de Galápagos, La Fabril, Nestlé Ecuador, AC Bebidas | USD 113,3 M |
| M Profesionales | Fertisa, Minutocorp, McKinsey & Company Ecuador, IMS Internet Media Services, Jucarcorp Group | USD 8,5 M |
| K Financieras | Saludsa, BMI Igualas Médicas, Mediecuador-Humana, Confiamed, Ecuasanitas | USD 6,5 M |

### Distribución geográfica del piloto

| Provincia | Empresas |
| --- | --- |
| Pichincha | 288 |
| Guayas | 147 |
| Azuay | 20 |
| Manabí | 15 |
| Otras | 30 |

## Archivos

| Archivo | Contenido |
| --- | --- |
| [`universo_2025.csv`](../../etl/datos/universo/2025/universo_2025.csv) | 14.029 empresas con CIIU, tamaño derivado, ubicación, cifras 2025 y alertas |
| [`piloto_500.csv`](../../etl/datos/universo/2025/piloto_500.csv) | Las 500 empresas del piloto y el criterio por el que entra cada una |
| [`top50_tec.csv`](../../etl/datos/universo/2025/top50_tec.csv), [`top50_g.csv`](../../etl/datos/universo/2025/top50_g.csv), [`top50_c.csv`](../../etl/datos/universo/2025/top50_c.csv), [`top50_m.csv`](../../etl/datos/universo/2025/top50_m.csv), [`top50_k.csv`](../../etl/datos/universo/2025/top50_k.csv) | Las cinco listas top 50 pedidas por el director |
| [`calidad_2025.json`](../../etl/datos/universo/2025/calidad_2025.json) | Hash del archivo crudo, fecha de corte y conteos de calidad |

## Periodo

| Tramo | Uso |
| --- | --- |
| 2025 | Año base de la selección del universo y del piloto |
| 2012–2025 | Serie comparable (todas las compañías bajo NIIF) ([03](03-periodo-de-analisis.md)) |
| 2006–2011 | Serie histórica, marcada como no comparable |

El universo se fija con el ranking 2025. Si una empresa sale del ranking en años posteriores, conserva su ficha con la fecha de captura.
