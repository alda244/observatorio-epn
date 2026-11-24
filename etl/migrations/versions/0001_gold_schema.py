"""Create the published gold schema objects."""

from alembic import op

revision = "0001_gold_schema"
down_revision = None
branch_labels = None
depends_on = None

_UPGRADE_SQL = (
    """CREATE TABLE oro.empresa (
    expediente SERIAL NOT NULL,
    ruc VARCHAR(13),
    nombre TEXT NOT NULL,
    ciiu VARCHAR(12) NOT NULL,
    ciiu_descripcion TEXT,
    seccion_ciiu VARCHAR(1),
    division_ciiu VARCHAR(4),
    grupo VARCHAR(4) NOT NULL,
    en_piloto BOOLEAN DEFAULT false NOT NULL,
    criterio_piloto VARCHAR(32),
    en_top50_tec BOOLEAN DEFAULT false NOT NULL,
    tipo_compania TEXT,
    region TEXT,
    provincia TEXT,
    ciudad TEXT,
    es_holding BOOLEAN,
    anio_identificacion INTEGER,
    PRIMARY KEY (expediente)
)""",
    "CREATE INDEX ix_oro_empresa_ciiu ON oro.empresa (ciiu)",
    "CREATE INDEX ix_oro_empresa_division_ciiu ON oro.empresa (division_ciiu)",
    "CREATE INDEX ix_oro_empresa_grupo ON oro.empresa (grupo)",
    "CREATE INDEX ix_oro_empresa_provincia ON oro.empresa (provincia)",
    "CREATE INDEX ix_oro_empresa_ruc ON oro.empresa (ruc)",
    "CREATE INDEX ix_oro_empresa_seccion_ciiu ON oro.empresa (seccion_ciiu)",
    """CREATE TABLE oro.cifras_anuales (
    expediente INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    empleados INTEGER,
    activo FLOAT,
    patrimonio FLOAT,
    ventas FLOAT,
    utilidad_neta FLOAT,
    ingreso_total FLOAT,
    tamano_derivado VARCHAR(16),
    tiene_alerta BOOLEAN NOT NULL,
    motivo_alerta VARCHAR(32),
    en_universo_ese_anio BOOLEAN NOT NULL,
    rank_grupo INTEGER,
    nueva_en_ranking BOOLEAN,
    ingreso_total_no_reportado BOOLEAN,
    utilidad_no_reportada BOOLEAN,
    PRIMARY KEY (expediente, anio),
    CONSTRAINT cifras_alerta_coherente CHECK (
        tiene_alerta = (motivo_alerta IS NOT NULL)
        AND (motivo_alerta IS NULL OR motivo_alerta IN
             ('imposible', 'grande_menos_10', 'fuera_de_rango_division'))),
    FOREIGN KEY(expediente) REFERENCES oro.empresa (expediente) ON DELETE RESTRICT
)""",
    "CREATE INDEX ix_oro_cifras_anuales_tamano_derivado ON oro.cifras_anuales (tamano_derivado)",
    """CREATE TABLE oro.ficha (
    expediente INTEGER NOT NULL,
    fecha_captura DATE NOT NULL,
    url_oficial TEXT,
    tagline VARCHAR(150),
    tagline_origen VARCHAR(8),
    tagline_fuente TEXT,
    descripcion TEXT,
    descripcion_fuente TEXT,
    productos_servicios TEXT,
    productos_fuente TEXT,
    correo_corporativo TEXT,
    telefono TEXT,
    redes TEXT,
    logo_url TEXT,
    direccion TEXT,
    fuente_tipo VARCHAR(32),
    estado VARCHAR(10),
    PRIMARY KEY (expediente, fecha_captura),
    FOREIGN KEY(expediente) REFERENCES oro.empresa (expediente) ON DELETE RESTRICT
)""",
    "CREATE INDEX ix_oro_ficha_estado ON oro.ficha (estado)",
    """CREATE TABLE oro.documento (
    id BIGSERIAL NOT NULL,
    expediente INTEGER NOT NULL,
    url TEXT NOT NULL,
    tipo_pagina VARCHAR(16),
    formato VARCHAR(4) NOT NULL,
    tipo_fuente VARCHAR(32) NOT NULL,
    fecha_captura DATE NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    titulo TEXT,
    texto TEXT,
    PRIMARY KEY (id),
    CONSTRAINT documento_formato_valido CHECK (formato IN ('html', 'pdf')),
    CONSTRAINT documento_tipo_fuente_valido CHECK (tipo_fuente IN
        ('web_oficial', 'informe_anual_oficial', 'catalogo_oficial')),
    CONSTRAINT documento_unico UNIQUE (expediente, sha256),
    FOREIGN KEY(expediente) REFERENCES oro.empresa (expediente) ON DELETE RESTRICT
)""",
    "CREATE INDEX ix_oro_documento_expediente ON oro.documento (expediente)",
    """CREATE TABLE oro.indicador_sector (
    anio INTEGER NOT NULL,
    seccion_ciiu VARCHAR(1) NOT NULL,
    indicador VARCHAR(48) NOT NULL,
    descripcion_seccion TEXT,
    valor FLOAT,
    PRIMARY KEY (anio, seccion_ciiu, indicador)
)""",
    """CREATE VIEW oro.ficha_vigente AS
SELECT DISTINCT ON (expediente)
       expediente, fecha_captura, url_oficial, tagline,
       tagline_origen, tagline_fuente, descripcion, descripcion_fuente,
       productos_servicios, productos_fuente, correo_corporativo, telefono,
       redes, logo_url, direccion, fuente_tipo,
       estado
  FROM oro.ficha
 ORDER BY expediente, fecha_captura DESC""",
    """CREATE VIEW oro.v_empresa AS
SELECT e.expediente, e.ruc, e.nombre, e.ciiu,
       e.ciiu_descripcion, e.seccion_ciiu, e.division_ciiu, e.grupo,
       e.en_piloto, e.criterio_piloto, e.en_top50_tec, e.tipo_compania,
       e.region, e.provincia, e.ciudad, e.es_holding,
       e.anio_identificacion,
       CASE f.estado
           WHEN 'completo' THEN 'completa'
           WHEN 'parcial' THEN 'parcial'
           ELSE 'sin_ficha'
       END AS estado_ficha
  FROM oro.empresa e
  LEFT JOIN oro.ficha_vigente f USING (expediente)""",
    """CREATE VIEW oro.v_cifras_anuales AS
SELECT expediente, anio, empleados, activo,
       patrimonio, ventas, utilidad_neta, ingreso_total,
       tamano_derivado, tiene_alerta, motivo_alerta, en_universo_ese_anio,
       rank_grupo, nueva_en_ranking, ingreso_total_no_reportado, utilidad_no_reportada
  FROM oro.cifras_anuales""",
    """CREATE VIEW oro.v_documento AS
SELECT id, expediente, url, tipo_pagina,
       formato, tipo_fuente, fecha_captura, sha256,
       titulo, texto
  FROM oro.documento""",
    """CREATE VIEW oro.v_indicador_sector AS
SELECT anio, seccion_ciiu, indicador, descripcion_seccion,
       valor
  FROM oro.indicador_sector""",
    "GRANT SELECT ON oro.ficha_vigente TO rol_api",
    "GRANT SELECT ON oro.v_empresa TO rol_api",
    "GRANT SELECT ON oro.v_cifras_anuales TO rol_api",
    "GRANT SELECT ON oro.v_documento TO rol_api",
    "GRANT SELECT ON oro.v_indicador_sector TO rol_api",
)


def upgrade() -> None:
    for statement in _UPGRADE_SQL:
        op.execute(statement)


def downgrade() -> None:
    op.execute("DROP VIEW oro.v_indicador_sector")
    op.execute("DROP VIEW oro.v_documento")
    op.execute("DROP VIEW oro.v_cifras_anuales")
    op.execute("DROP VIEW oro.v_empresa")
    op.execute("DROP VIEW oro.ficha_vigente")
    op.drop_table("indicador_sector", schema="oro")
    op.drop_table("documento", schema="oro")
    op.drop_table("ficha", schema="oro")
    op.drop_table("cifras_anuales", schema="oro")
    op.drop_table("empresa", schema="oro")
