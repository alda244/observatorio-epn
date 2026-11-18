# Cómo se almacenan los datos en la base

Generado el 2026-11-18 con `etl documentar`, a partir de los archivos reales de
`datos/oro/`. Las cifras de este documento no son ejemplos: son lo que hay.

El diseño —por qué las tablas son estas y cómo se relacionan— está en
[base-de-datos.md](base-de-datos.md). Aquí se ve el contenido.

## Lo que se cargaría hoy

| Tabla | Filas | Archivo de origen | En disco |
| --- | --- | --- | --- |
| `oro.empresa` | 14.027 | `empresa.parquet` | 0.6 MB |
| `oro.cifras_anuales` | 118.792 | `cifras_anuales.parquet` | 5.0 MB |
| `oro.universo` | 118.792 | `universo_por_anio.parquet` | 0.3 MB |
| `oro.ficha` | 5 | `ficha.csv` | 0.0 MB |
| `oro.documento` | se arma al cargar | `crudo/web/AAAA/manifest.jsonl` + HTML | |
| `oro.indicador_sector` | se arma al cargar | `crudo/AAAA/indicadores_sector.csv` | |

Las dos últimas no pasan por el consolidado: el texto de las páginas y los
indicadores sectoriales se leen en el momento de la carga.

## `oro.empresa`

Lo que no cambia de cada compañía.

- Filas: **14.027**
- Clave primaria: `expediente`
- La publica: `GET /empresas/{expediente}`

| Columna | Tipo en PostgreSQL | Clave | Sin dato | Ejemplo real |
| --- | --- | --- | --- | --- |
| `expediente` | INTEGER | PK | 0 % | 2 |
| `ruc` | VARCHAR(13) |  | 0 % | 1790004724001 |
| `nombre` | TEXT |  | 0 % | ACERIA DEL ECUADOR CA ADELCA. |
| `ciiu` | VARCHAR(12) |  | 0 % | C2410.25 |
| `ciiu_descripcion` | TEXT |  | 0 % | FABRICACIÓN DE ÁNGULOS, PERFILES Y SECCIONES ABIERTAS DE ACE… |
| `seccion_ciiu` | VARCHAR(1) |  | 0 % | C |
| `division_ciiu` | VARCHAR(4) |  | 0 % | C24 |
| `grupo` | VARCHAR(4) |  | 0 % | C |
| `tipo_compania` | TEXT |  | 0 % | ANÓNIMA |
| `region` | TEXT |  | 0 % | SIERRA |
| `provincia` | TEXT |  | 0 % | PICHINCHA |
| `ciudad` | TEXT |  | 0 % | QUITO |
| `es_holding` | BOOLEAN |  | 0 % | False |
| `anio_identificacion` | INTEGER |  | 0 % | 2025 |

Dos filas reales:

- expediente = 2 · ruc = 1790004724001 · nombre = ACERIA DEL ECUADOR CA ADELCA. · ciiu = C2410.25 · ciiu_descripcion = FABRICACIÓN DE ÁNGULOS, PERFILES Y SECCIONES ABIERTAS DE ACE… · seccion_ciiu = C · division_ciiu = C24 · grupo = C · tipo_compania = ANÓNIMA · region = SIERRA · provincia = PICHINCHA · ciudad = QUITO · es_holding = False · anio_identificacion = 2025
- expediente = 3 · ruc = 1790008959001 · nombre = ACERO COMERCIAL ECUATORIANO S.A. · ciiu = G4610.03 · ciiu_descripcion = INTERMEDIARIOS DEL COMERCIO DE LA MADERA Y MATERIALES DE CON… · seccion_ciiu = G · division_ciiu = G46 · grupo = G · tipo_compania = ANÓNIMA · region = SIERRA · provincia = PICHINCHA · ciudad = QUITO · es_holding = False · anio_identificacion = 2025

## `oro.cifras_anuales`

Una fila por empresa y ejercicio fiscal. Es la que permite series y proyecciones.

- Filas: **118.792**
- Clave primaria: `expediente`, `anio`
- La publica: `GET /empresas` y el bloque de cifras del detalle

| Columna | Tipo en PostgreSQL | Clave | Sin dato | Ejemplo real |
| --- | --- | --- | --- | --- |
| `expediente` | INTEGER | PK | 0 % | 2 |
| `anio` | INTEGER | PK | 0 % | 2012 |
| `empleados` | INTEGER |  | 0 % | 1295 |
| `activo` | FLOAT |  | 0 % | 267455691.94 |
| `patrimonio` | FLOAT |  | 0 % | 108633791.89 |
| `ventas` | FLOAT |  | 0 % | 329472125.05 |
| `utilidad_neta` | FLOAT |  | 0 % | 13948538.12 |
| `ingreso_total` | FLOAT |  | 0 % | 331167834.26 |
| `tamano_derivado` | VARCHAR(16) |  | 0 % | grande |
| `alerta_empleados` | VARCHAR(32) |  | 0 % |  |
| `rank_grupo` | INTEGER |  | 18 % | 8 |
| `nueva_en_ranking` | BOOLEAN |  | 0 % | False |
| `ingreso_total_no_reportado` | BOOLEAN |  | 0 % | False |
| `utilidad_no_reportada` | BOOLEAN |  | 0 % | False |

Dos filas reales:

- expediente = 2 · anio = 2012 · empleados = 1295 · activo = 267455691.94 · patrimonio = 108633791.89 · ventas = 329472125.05 · utilidad_neta = 13948538.12 · ingreso_total = 331167834.26 · tamano_derivado = grande · alerta_empleados =  · rank_grupo = 8 · nueva_en_ranking = False · ingreso_total_no_reportado = False · utilidad_no_reportada = False
- expediente = 2 · anio = 2013 · empleados = 1355 · activo = 277594310.82 · patrimonio = 125158563.56 · ventas = 329146498.33 · utilidad_neta = 20043382.7 · ingreso_total = 330496635.64 · tamano_derivado = grande · alerta_empleados =  · rank_grupo = 8 · nueva_en_ranking = False · ingreso_total_no_reportado = False · utilidad_no_reportada = False

## `oro.universo`

En qué años aparece cada empresa y cuáles tienen ficha.

- Filas: **118.792**
- Clave primaria: `anio`, `expediente`
- La publica: El filtro `anio` de `GET /empresas`

| Columna | Tipo en PostgreSQL | Clave | Sin dato | Ejemplo real |
| --- | --- | --- | --- | --- |
| `anio` | INTEGER | PK | 0 % | 2012 |
| `expediente` | INTEGER | PK | 0 % | 2 |
| `grupo` | VARCHAR(4) |  | 0 % | C |
| `en_piloto` | BOOLEAN |  | 0 % | True |
| `criterio_piloto` | VARCHAR(32) |  | 95 % | top50_c |
| `en_universo_ese_anio` | BOOLEAN |  | 0 % | True |
| `en_top50_tec` | BOOLEAN |  | 0 % | False |

Dos filas reales:

- anio = 2012 · expediente = 2 · grupo = C · en_piloto = True · criterio_piloto = top50_c · en_universo_ese_anio = True · en_top50_tec = False
- anio = 2012 · expediente = 3 · grupo = G · en_piloto = False · en_universo_ese_anio = True · en_top50_tec = False

## `oro.ficha`

El Company Profile, con la fuente de cada campo.

- Filas: **5**
- Clave primaria: `expediente`, `fecha_captura`
- La publica: `GET /empresas/{expediente}` (Bloque 2)

| Columna | Tipo en PostgreSQL | Clave | Sin dato | Ejemplo real |
| --- | --- | --- | --- | --- |
| `expediente` | INTEGER | PK | 0 % | 384 |
| `fecha_captura` | DATE | PK | 0 % | 2026-11-11 |
| `url_oficial` | TEXT |  | 0 % | https://www.corporacionfavorita.com/ |
| `tagline` | VARCHAR(150) |  | 0 % | Corporación Favorita, empresa ecuatoriana multinacional. Mej… |
| `tagline_origen` | VARCHAR(8) |  | 0 % | literal |
| `tagline_fuente` | TEXT |  | 0 % | https://www.corporacionfavorita.com/ |
| `descripcion` | TEXT |  | 20 % | Trabajamos para mejorar la calidad de vida de todos, ofrecie… |
| `descripcion_fuente` | TEXT |  | 20 % | https://www.corporacionfavorita.com/quienes-somos |
| `productos_servicios` | TEXT |  | 20 % | Supermercados y retail; Centros comerciales; Industria; Marc… |
| `productos_fuente` | TEXT |  | 20 % | https://www.corporacionfavorita.com/marcas#servicios |
| `correo_corporativo` | TEXT |  | 80 % | info@telconet.com.co; info@telconet.com.pa; info@telconet.ec… |
| `telefono` | TEXT |  | 80 % | +5073803626; +573115393687; +59323922000; +59343922000; 1800… |
| `redes` | TEXT |  | 60 % | https://www.facebook.com/CorporacionFavorita; https://www.in… |
| `logo_url` | TEXT |  | 60 % | https://www.corporacionfavorita.com/logo-cf.png |
| `direccion` | TEXT |  | 100 % | — |
| `fuente_tipo` | VARCHAR(32) |  | 0 % | web_oficial |
| `estado` | VARCHAR(10) |  | 0 % | completo |

Columnas del archivo que la tabla no guarda: `nombre`, `paginas_capturadas`, `anio_captura`.

Dos filas reales:

- expediente = 384 · fecha_captura = 2026-11-11 · url_oficial = https://www.corporacionfavorita.com/ · tagline = Corporación Favorita, empresa ecuatoriana multinacional. Mej… · tagline_origen = literal · tagline_fuente = https://www.corporacionfavorita.com/ · descripcion = Trabajamos para mejorar la calidad de vida de todos, ofrecie… · descripcion_fuente = https://www.corporacionfavorita.com/quienes-somos · productos_servicios = Supermercados y retail; Centros comerciales; Industria; Marc… · productos_fuente = https://www.corporacionfavorita.com/marcas#servicios · redes = https://www.facebook.com/CorporacionFavorita; https://www.in… · logo_url = https://www.corporacionfavorita.com/logo-cf.png · fuente_tipo = web_oficial · estado = completo
- expediente = 7154 · fecha_captura = 2026-11-11 · url_oficial = https://pronaca.com/ · tagline = Somos una empresa multinacional familiar que actúa con respe… · tagline_origen = literal · tagline_fuente = https://pronaca.com/ · descripcion = Somos una empresa multinacional familiar que actúa con respe… · descripcion_fuente = https://pronaca.com/somos-pronaca/acerca-de-nosotros/ · fuente_tipo = web_oficial · estado = parcial

## Qué respondería la API hoy

Las consultas son las del contrato y los resultados están calculados sobre
estos mismos archivos.

### `GET /empresas?anio=2025&grupo=TEC`

```sql
SELECT e.expediente, e.nombre, c.ventas, c.empleados
  FROM oro.empresa e
  JOIN oro.cifras_anuales c USING (expediente)
  JOIN oro.universo u USING (expediente)
 WHERE c.anio = 2025 AND u.anio = c.anio AND e.grupo = 'TEC'
 ORDER BY c.ventas DESC;
```

Devolvería **5.898 empresas**. Las tres primeras por ventas:

| expediente | nombre | ventas | empleados |
| --- | --- | --- | --- |
| 47845 | CONSORCIO ECUATORIANO DE TELECOMUNICACIONES S.A. CONECEL | 1.030.666.289 | 3.302 |
| 47972 | OTECEL S.A. | 511.863.497 | 688 |
| 72951 | TELCONET S.A. | 317.568.866 | 5.382 |

### `GET /empresas/384`

```sql
SELECT anio, ventas, utilidad_neta, empleados
  FROM oro.cifras_anuales WHERE expediente = 384 ORDER BY anio;
```

La serie de **CORPORACION FAVORITA C.A.**, 14 años:

| anio | ventas | utilidad_neta | empleados |
| --- | --- | --- | --- |
| 2012 | 1.606.407.226 | 113.366.735 | 7.396 |
| 2013 | 1.755.908.806 | 132.656.095 | 8.732 |
| 2014 | 1.925.644.051 | 143.117.229 | 9.197 |
| 2015 | 1.989.012.100 | 146.587.818 | 9.030 |
| 2016 | 1.887.147.694 | 135.025.111 | 8.501 |
| 2017 | 1.948.912.009 | 148.382.202 | 8.521 |
| 2018 | 2.089.984.173 | 154.011.840 | 10.478 |
| 2019 | 2.103.828.360 | 155.764.233 | 10.479 |
| 2020 | 2.170.602.775 | 147.499.234 | 10.768 |
| 2021 | 2.178.780.982 | 143.823.630 | 10.818 |
| 2022 | 2.355.580.171 | 152.679.114 | 10.966 |
| 2023 | 2.483.015.099 | 165.234.816 | 12.343 |
| 2024 | 2.546.101.460 | 157.778.086 | 11.547 |
| 2025 | 2.690.137.858 | 163.876.843 | 12.033 |

### Cuántas empresas tiene cada año

```sql
SELECT anio, count(*) FROM oro.universo GROUP BY anio ORDER BY anio;
```

| anio | empresas |
| --- | --- |
| 2012 | 4.623 |
| 2013 | 4.934 |
| 2014 | 5.330 |
| 2015 | 5.813 |
| 2016 | 6.194 |
| 2017 | 6.660 |
| 2018 | 7.156 |
| 2019 | 8.451 |
| 2020 | 9.156 |
| 2021 | 10.145 |
| 2022 | 11.187 |
| 2023 | 12.149 |
| 2024 | 12.967 |
| 2025 | 14.027 |

## Cómo se carga

`etl bd` no calcula nada: inserta estos archivos. Tres reglas:

| Regla | Por qué |
| --- | --- |
| `INSERT ... ON CONFLICT DO UPDATE` por clave primaria | Repetir la carga no duplica filas ni pierde correcciones |
| Por lotes de unos 60.000 parámetros | PostgreSQL admite 65.535 por consulta |
| Primero `empresa`, después el resto | Las demás tablas la referencian |

Antes de cargar, `etl verificar` comprueba las mismas condiciones que
impondrán las claves de PostgreSQL: claves únicas y cero filas huérfanas.
Si algo no cuadra, falla ahí y no en la base.
