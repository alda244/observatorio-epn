# Base de datos del Componente B

Modelo de datos que produce el ETL y que lee la API pública. Sigue el
[ADR 0002](../docs/adr/0002-postgresql-esquemas-roles.md): un solo PostgreSQL 16,
esquemas propios de B con `rol_datos` y ningún permiso para el Componente A,
que obtiene los datos por la API.

## Esquemas y capas

Las capas siguen la metodología Medallion. El dato crudo no entra a la base:
se conserva como archivo inmutable con su hash en `datos/crudo/MANIFEST.csv`,
que es lo que permite reproducir todo desde el origen.

| Capa | Dónde vive | Contenido | Quién la lee |
| --- | --- | --- | --- |
| Crudo (bronce) | Archivos en `etl/datos/crudo/` | Descargas SCVS y HTML capturado, sin modificar | Solo el ETL |
| Plata | Archivos Parquet y esquema `plata` | Datos limpios, normalizados y validados | Solo el ETL |
| Oro | Esquema `oro` | Lo que se publica | La API y el portal |

| Rol | Dueño de | Permisos |
| --- | --- | --- |
| `rol_datos` | `plata`, `oro` | Lectura y escritura. Lo usa el ETL |
| `rol_api` | — | Solo `SELECT` sobre `oro`. Lo usa la API, que nunca escribe |
| `rol_asistente` | `asistente` | Sin acceso a `plata` ni a `oro` |

Los tres se crean en [`infra/postgres/init/01-esquemas.sh`](../infra/postgres/init/01-esquemas.sh),
que corre una sola vez al crear el volumen de PostgreSQL.

## Modelo de datos

```mermaid
erDiagram
    EMPRESA ||--o{ CIFRAS_ANUALES : "declara cada año"
    EMPRESA ||--o{ UNIVERSO : "entra al estudio en"
    EMPRESA ||--o{ FICHA : "tiene capturas de"
    EMPRESA ||--o{ DOCUMENTO : "publica"
    INDICADOR_SECTOR }o--|| EMPRESA : "compara por sección CIIU"

    EMPRESA {
        int expediente PK "Identificador SCVS"
        string ruc "13 dígitos, del directorio"
        text nombre "Razón social"
        string ciiu "CIIU Rev. 4, 6 niveles"
        string seccion_ciiu "Letra A–U"
        string division_ciiu "Tres caracteres"
        string grupo "TEC, G, C, M, K"
        text provincia
        bool es_holding
    }
    CIFRAS_ANUALES {
        int expediente PK_FK
        int anio PK
        float ventas
        float activo
        float patrimonio
        float utilidad_neta
        int empleados "Dato con alerta"
        string tamano_derivado "Calculado por ventas"
        string alerta_empleados "Causa de la inconsistencia"
    }
    UNIVERSO {
        int anio PK
        int expediente PK_FK
        string grupo
        bool en_piloto
        string criterio_piloto
    }
    FICHA {
        int expediente PK_FK
        date fecha_captura PK
        string tagline "Máx. 150 caracteres"
        text descripcion
        text productos_servicios
        text correo_corporativo
        text redes
        text logo_url
        string estado "completo, parcial, pendiente"
    }
    DOCUMENTO {
        bigint id PK
        int expediente FK
        text url
        string tipo_pagina "portada, nosotros, servicios"
        date fecha_captura
        string sha256
        text texto
    }
    INDICADOR_SECTOR {
        int anio PK
        string seccion_ciiu PK
        string indicador PK
        float valor
    }
```

## Las tablas, una por una

### `oro.empresa`

Lo que no cambia de año en año: quién es la empresa y a qué se dedica. Una
fila por expediente. Si una empresa aparece en varios años, su fila se
actualiza con la información más reciente.

### `oro.cifras_anuales`

Una fila por empresa y año, que es la decisión que permite las series de
tiempo y las proyecciones del Sprint 5. La clave es `(expediente, anio)`.

El campo `empleados` se publica junto a `alerta_empleados`, que dice por qué
el número no es confiable cuando no lo es:

| Valor | Significado |
| --- | --- |
| *(vacío)* | El dato es coherente con su sector |
| `grande_menos_10` | Empresa grande por ventas que declara menos de 10 empleados |
| `fuera_de_rango_division` | Vende más de 20 veces por empleado que la mediana de su división CIIU |
| `imposible` | Más de 100.000 empleados |

El tamaño **no** se toma de la SCVS, porque esa columna viene vacía: se
calcula con las ventas según el COPCI y se publica como `tamano_derivado`.

### `oro.universo`

Qué empresas abarca el Observatorio en cada año y cuáles tienen ficha. Se
separa de `empresa` porque el universo se recalcula por año: en 2025 son
14.027 empresas y 500 del piloto; en 2024, 12.931 y 478.

### `oro.ficha`

El Company Profile, con la clave `(expediente, fecha_captura)`: una captura
nueva no pisa la anterior, así se puede comparar cómo cambia la oferta de una
empresa en el tiempo. Cada campo guarda la URL de donde salió.

### `oro.documento`

El texto limpio de cada página capturada. Es lo que consume el Componente A
por `GET /empresas/{expediente}/documentos` para indexar y citar. La
restricción `(expediente, sha256)` evita guardar dos veces la misma página.

### `oro.indicador_sector`

Indicadores financieros por sección CIIU y año que publica la SCVS (liquidez,
endeudamiento, rentabilidad y otros). Sirve para comparar una empresa contra
su sector. Hoy cubre 2018–2023.

## Correspondencia con el contrato

| Ruta | Tablas |
| --- | --- |
| `GET /empresas` | `empresa` + `cifras_anuales` + `universo` |
| `GET /empresas/{expediente}` | `empresa` + `cifras_anuales` + `ficha` |
| `GET /empresas/{expediente}/documentos` | `documento` |
| `GET /indicadores` | `indicador_sector` + agregados de `cifras_anuales` |

## Correspondencia con la ficha de empresa

Campos de [`docs/ficha-empresa.md`](../docs/ficha-empresa.md) que produce B:

| Bloque | Campo | Columna |
| --- | --- | --- |
| 1 | Razón social | `empresa.nombre` |
| 1 | Contacto corporativo | `ficha.correo_corporativo`, `ficha.telefono`, `ficha.url_oficial` |
| 1 | Redes | `ficha.redes` |
| 1 | Ubicación | `empresa.provincia`, `empresa.ciudad`, `ficha.direccion` |
| 1 | Sector CIIU y tamaño | `empresa.ciiu`, `cifras_anuales.tamano_derivado` |
| 2 | Descripción corta | `ficha.tagline` |
| 2 | Descripción detallada | `ficha.descripcion` |
| 2 | Productos y servicios | `ficha.productos_servicios` |
| 3 | Logotipo | `ficha.logo_url` |
| Cifras | Ventas, utilidad, empleados | `cifras_anuales` |

Lo que produce A (misión, visión, historia, palabras clave, certificaciones)
sale de `oro.documento`, no de una columna de B.

## Reglas

| Regla | Cómo se cumple |
| --- | --- |
| La API nunca escribe | `rol_api` solo tiene `SELECT` sobre `oro` |
| Repetir un paso no duplica filas | Toda carga usa `INSERT ... ON CONFLICT DO UPDATE` sobre la clave primaria |
| Todo dato se puede rastrear hasta su fuente | `MANIFEST.csv` para la SCVS; `fuente_url`, `fecha_captura` y `sha256` para la web |
| Un dato dudoso se publica marcado, no se corrige ni se oculta | `alerta_empleados`, `tamano_derivado`, `tagline_origen` |
| Sin datos personales | Solo correos corporativos; se descartan cargos directivos (LOPDP) |

## Pendientes

| Pendiente | Por qué importa |
| --- | --- |
| Nombre comercial aparte de la razón social | La ficha lo pide y hoy solo se guarda la razón social |
| Fecha de constitución para calcular los años en el mercado | La ficha lo pide; no está en el ranking, hay que ver si el directorio lo trae |
| Migraciones con Alembic | Hoy las tablas se crean con `create_all`; conviene versionar los cambios |
| Cuentas de los estados financieros en la base | Ya están en plata (`financieros.parquet`), falta decidir qué se publica |
| Metadatos DCAT del catálogo | Sprint 7 |
