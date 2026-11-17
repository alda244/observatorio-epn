# Universo de empresas

El Observatorio cubre cinco grupos de actividad económica: todas las empresas tecnológicas y las medianas y grandes de comercio, manufactura, actividades profesionales y actividades financieras. Son 14.029 empresas con cifras. De ellas, 500 forman el piloto con ficha completa.

La fuente es el ranking empresarial 2025 de la SCVS (corte 22-oct-2026). La selección se reproduce con:

```powershell
python etl/universo/seleccionar_universo.py
```

## Sectores (CIIU Rev. 4)

| Grupo | Código | Incluye |
| --- | --- | --- |
| Tecnológicas (TEC) | J61, J62, J63, J582 | Telecomunicaciones, software, servicios de información, edición de software |
| Comercio | G | Mayoristas, minoristas, supermercados, vehículos |
| Manufactura | C | Industria y agroindustria |
| Actividades profesionales | M | Consultoría, ingeniería, publicidad, investigación |
| Actividades financieras | K | Medicina prepagada, servicios auxiliares, fiduciarias, casas de valores, holdings |

## Tamaño

La columna `Tamaño` del ranking 2025 viene vacía, así que el tamaño se calcula con las ventas anuales (COPCI). La columna se llama `tamano_derivado`.

| Tamaño | Ventas 2025 |
| --- | --- |
| Micro y pequeña | Hasta USD 1 M |
| Mediana | Más de USD 1 M y hasta USD 5 M |
| Grande | Más de USD 5 M |

## Universo

| Grupo | Empresas en el ranking | Regla | Universo |
| --- | --- | --- | --- |
| TEC | 5.901 | Todas | 5.899 |
| G | 37.231 | Medianas y grandes | 5.210 |
| C | 9.971 | Medianas y grandes | 1.749 |
| M | 21.936 | Medianas y grandes | 654 |
| K | 3.909 | Medianas y grandes | 517 |
| **Total** | | | **14.029** |

Se eliminaron 13 expedientes que el archivo de la SCVS repite en filas idénticas. El universo concentra el 62,6 % de las ventas de todas las sociedades del ranking.

## Piloto de 500 empresas

| Grupo | Regla | Empresas | Ventas del grupo cubiertas |
| --- | --- | --- | --- |
| TEC | Todas las medianas y grandes | 300 | 88,6 % |
| G | Top 50 por ventas | 50 | 36,6 % |
| C | Top 50 por ventas | 50 | 44,4 % |
| M | Top 50 por ventas | 50 | 42,0 % |
| K | Top 50 por ventas, sin holdings | 50 | 29,0 % |

El piloto concentra el 25,3 % de las ventas de todas las sociedades. Se publica además el top 50 tecnológico para comparar los cinco grupos con el mismo número de empresas.

| Provincia | Empresas del piloto |
| --- | --- |
| Pichincha | 288 |
| Guayas | 147 |
| Azuay | 20 |
| Manabí | 15 |
| Otras | 30 |

## Calidad del dato

| Problema | Tratamiento |
| --- | --- |
| Columna `Tamaño` vacía | Tamaño calculado por ventas |
| Empleados inconsistentes: 869 de 4.337 grandes declaran menos de 10 (Tiendas Tuti: 8 empleados, USD 1.008 M) | No se usa para clasificar. La columna `alerta_empleados` marca esos casos (31 en el piloto) |
| Holdings sin oferta comercial (CIIU K642 o "HOLDING" en el nombre) | Fuera del top 50 de K; siguen en el universo con cifras |
| 126 filas duplicadas en el archivo crudo | Eliminadas |

## Archivos

Todos en [`etl/datos/universo/2025/`](../etl/datos/universo/2025/).

| Archivo | Contenido |
| --- | --- |
| `universo_2025.csv` | 14.029 empresas con CIIU, tamaño, ubicación, cifras 2025 y alertas |
| `piloto_500.csv` | Las 500 del piloto y la regla por la que entra cada una |
| `top50_tec.csv`, `top50_g.csv`, `top50_c.csv`, `top50_m.csv`, `top50_k.csv` | Las cinco listas top 50 |
| `calidad_2025.json` | Hash del archivo crudo, fecha de corte y conteos de calidad |

El universo se fija con el ranking 2025. Si una empresa sale del ranking en años posteriores, conserva su ficha con la fecha de captura.
