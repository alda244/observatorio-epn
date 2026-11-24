"""Tablas de PostgreSQL del Componente B, publicadas mediante vistas de public."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    false,
)

DATABASE_SCHEMA = "public"

metadata = MetaData(schema=DATABASE_SCHEMA)

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
    Column("grupo", String(4), nullable=False, index=True),
    Column("en_piloto", Boolean, nullable=False, server_default=false()),
    Column("criterio_piloto", String(32)),
    Column("en_top50_tec", Boolean, nullable=False, server_default=false()),
    Column("tipo_compania", Text),
    Column("region", Text),
    Column("provincia", Text, index=True),
    Column("ciudad", Text),
    Column("es_holding", Boolean),
    Column("anio_identificacion", Integer, comment="Año del ranking del que sale esta ficha"),
    comment="Datos estables de cada compañía, del ranking SCVS",
)

cifras_anuales = Table(
    "cifras_anuales",
    metadata,
    Column(
        "expediente",
        Integer,
        ForeignKey(f"{DATABASE_SCHEMA}.empresa.expediente", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column("anio", Integer, primary_key=True),
    Column("empleados", Integer),
    Column("activo", Float),
    Column("patrimonio", Float),
    Column("ventas", Float),
    Column("utilidad_neta", Float),
    Column("ingreso_total", Float),
    Column("tamano_derivado", String(16), index=True),
    Column("tiene_alerta", Boolean, nullable=False),
    Column("motivo_alerta", String(32)),
    Column("en_universo_ese_anio", Boolean, nullable=False),
    CheckConstraint(
        "tiene_alerta = (motivo_alerta IS NOT NULL) AND "
        "(motivo_alerta IS NULL OR motivo_alerta IN "
        "('imposible', 'grande_menos_10', 'fuera_de_rango_division'))",
        name="cifras_alerta_coherente",
    ),
    Column("rank_grupo", Integer),
    Column("nueva_en_ranking", Boolean),
    # «No reportado» no es «cero»: en 2014 la SCVS no publicó estas dos
    # columnas, y sin la marca cualquier promedio de ese año sale mal.
    Column("ingreso_total_no_reportado", Boolean),
    Column("utilidad_no_reportada", Boolean),
    comment="Cifras por empresa y año; el tamaño se deriva de las ventas (COPCI)",
)

ficha = Table(
    "ficha",
    metadata,
    Column(
        "expediente",
        Integer,
        ForeignKey(f"{DATABASE_SCHEMA}.empresa.expediente", ondelete="RESTRICT"),
        primary_key=True,
    ),
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
    Column(
        "expediente",
        Integer,
        ForeignKey(f"{DATABASE_SCHEMA}.empresa.expediente", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    ),
    Column("url", Text, nullable=False),
    Column("tipo_pagina", String(16)),
    Column("formato", String(4), nullable=False),
    Column("tipo_fuente", String(32), nullable=False),
    CheckConstraint("formato IN ('html', 'pdf')", name="documento_formato_valido"),
    CheckConstraint(
        "tipo_fuente IN ('web_oficial', 'informe_anual_oficial', 'catalogo_oficial')",
        name="documento_tipo_fuente_valido",
    ),
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
