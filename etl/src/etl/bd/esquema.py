"""Esquema de la base de datos del Componente B.

Un solo PostgreSQL con esquemas propios de B
([ADR 0002](../../../../docs/adr/0002-postgresql-esquemas-roles.md)):
`plata` guarda lo limpio y `oro` lo que publica la API. El rol del Componente A
no tiene permisos sobre ninguno de los dos: A consume la API.

Las tablas de `oro` corresponden a las rutas del contrato:

| Tabla | Ruta |
| --- | --- |
| `empresa`, `cifras_anuales` | `GET /empresas`, `GET /empresas/{expediente}` |
| `ficha` | `GET /empresas/{expediente}` (Company Profile) |
| `documento` | `GET /empresas/{expediente}/documentos` |
| `indicador_sector` | `GET /indicadores` |
"""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

ESQUEMA_PLATA = "plata"
ESQUEMA_ORO = "oro"

metadata = MetaData(schema=ESQUEMA_ORO)

empresa = Table(
    "empresa",
    metadata,
    Column("expediente", Integer, primary_key=True),
    Column("ruc", String(13), index=True),
    Column("nombre", Text, nullable=False),
    Column("ciiu", String(12), nullable=False, index=True),
    Column("ciiu_descripcion", Text),
    Column("seccion_ciiu", String(1), index=True),
    Column("division_ciiu", String(4), index=True),
    Column("grupo", String(4), index=True),
    Column("tipo_compania", Text),
    Column("region", Text),
    Column("provincia", Text, index=True),
    Column("ciudad", Text),
    Column("es_holding", Boolean),
    comment="Datos estables de cada compañía, del ranking SCVS",
)

cifras_anuales = Table(
    "cifras_anuales",
    metadata,
    Column("expediente", Integer, primary_key=True),
    Column("anio", Integer, primary_key=True),
    Column("empleados", Integer),
    Column("activo", Float),
    Column("patrimonio", Float),
    Column("ventas", Float),
    Column("utilidad_neta", Float),
    Column("ingreso_total", Float),
    Column("tamano_derivado", String(16), index=True),
    Column("alerta_empleados", String(32)),
    Column("rank_grupo", Integer),
    Column("nueva_en_ranking", Boolean),
    comment="Cifras por empresa y año; el tamaño se deriva de las ventas (COPCI)",
)

universo = Table(
    "universo",
    metadata,
    Column("anio", Integer, primary_key=True),
    Column("expediente", Integer, primary_key=True),
    Column("grupo", String(4), nullable=False),
    Column("en_piloto", Boolean, nullable=False, default=False),
    Column("criterio_piloto", String(32)),
    Column("en_top50_tec", Boolean),
    comment="Empresas que abarca el Observatorio en cada año y cuáles tienen ficha",
)

ficha = Table(
    "ficha",
    metadata,
    Column("expediente", Integer, primary_key=True),
    Column("fecha_captura", Date, primary_key=True),
    Column("url_oficial", Text),
    Column("tagline", String(150)),
    Column("tagline_origen", String(8)),
    Column("tagline_fuente", Text),
    Column("descripcion", Text),
    Column("descripcion_fuente", Text),
    Column("productos_servicios", Text),
    Column("productos_fuente", Text),
    Column("correo_corporativo", Text),
    Column("telefono", Text),
    Column("redes", Text),
    Column("logo_url", Text),
    Column("direccion", Text),
    Column("fuente_tipo", String(32)),
    Column("estado", String(10), index=True),
    comment="Company Profile por empresa y fecha de captura",
)

documento = Table(
    "documento",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("expediente", Integer, nullable=False, index=True),
    Column("url", Text, nullable=False),
    Column("tipo_pagina", String(16)),
    Column("fecha_captura", Date, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("titulo", Text),
    Column("texto", Text),
    UniqueConstraint("expediente", "sha256", name="documento_unico"),
    comment="Texto limpio de cada página capturada, para que A lo indexe y lo cite",
)

indicador_sector = Table(
    "indicador_sector",
    metadata,
    Column("anio", Integer, primary_key=True),
    Column("seccion_ciiu", String(1), primary_key=True),
    Column("indicador", String(48), primary_key=True),
    Column("descripcion_seccion", Text),
    Column("valor", Float),
    comment="Indicadores financieros por sector y año publicados por la SCVS",
)

TABLAS = [empresa, cifras_anuales, universo, ficha, documento, indicador_sector]
