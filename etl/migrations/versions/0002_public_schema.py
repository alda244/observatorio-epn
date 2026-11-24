"""Move the published tables and views to public without reloading data."""

from alembic import op

revision = "0002_public_schema"
down_revision = "0001_gold_schema"
branch_labels = None
depends_on = None

TABLES = ("empresa", "cifras_anuales", "ficha", "documento", "indicador_sector")
VIEWS = ("ficha_vigente", "v_empresa", "v_cifras_anuales", "v_documento", "v_indicador_sector")


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE oro.{table} SET SCHEMA public")
    for view in VIEWS:
        op.execute(f"ALTER VIEW oro.{view} SET SCHEMA public")
    op.execute("DROP SCHEMA oro RESTRICT")


def downgrade() -> None:
    # The database administrator must recreate oro with rol_datos as owner first.
    op.execute("GRANT USAGE ON SCHEMA oro TO rol_api")
    for view in VIEWS:
        op.execute(f"ALTER VIEW public.{view} SET SCHEMA oro")
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} SET SCHEMA oro")
