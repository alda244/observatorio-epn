"""Apply the Component B schema as its owner."""

from alembic import context
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from etl import config
from etl.bd.schema import DATABASE_SCHEMA, metadata

options = {
    "target_metadata": metadata,
    "version_table_schema": DATABASE_SCHEMA,
}

if context.is_offline_mode():
    context.configure(dialect_name="postgresql", literal_binds=True, **options)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(config.database_url(), poolclass=NullPool)
    with engine.begin() as connection:
        role = connection.scalar(text("SELECT current_user"))
        if role != "rol_datos":
            raise RuntimeError("Las migraciones deben ejecutarse como rol_datos")
        if connection.scalar(text("SELECT to_regclass('oro.alembic_version') IS NOT NULL")):
            connection.execute(text("ALTER TABLE oro.alembic_version SET SCHEMA public"))
        context.configure(connection=connection, **options)
        with context.begin_transaction():
            context.run_migrations()
