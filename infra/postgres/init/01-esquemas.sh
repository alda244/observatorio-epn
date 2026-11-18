#!/bin/bash
# Crea la extensión, los esquemas y los roles de la base del Observatorio.
# Corre una sola vez, cuando se crea el volumen de PostgreSQL.
# Decisión: docs/adr/0002-postgresql-esquemas-roles.md
set -euo pipefail

CLAVE_DATOS="${POSTGRES_CLAVE_DATOS:-rol_datos}"
CLAVE_ASISTENTE="${POSTGRES_CLAVE_ASISTENTE:-rol_asistente}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE EXTENSION IF NOT EXISTS vector;

-- Un rol por componente. Ninguno recibe permisos sobre los esquemas del otro:
-- el Componente A obtiene los datos de B por la API.
CREATE ROLE rol_datos      LOGIN PASSWORD '${CLAVE_DATOS}';
CREATE ROLE rol_asistente  LOGIN PASSWORD '${CLAVE_ASISTENTE}';

-- Componente B: capas de la metodología Medallion.
CREATE SCHEMA plata AUTHORIZATION rol_datos;
CREATE SCHEMA oro   AUTHORIZATION rol_datos;

-- Componente A: índice vectorial y trazabilidad.
CREATE SCHEMA asistente AUTHORIZATION rol_asistente;

-- La extensión vive en public y los dos roles la usan.
GRANT USAGE ON SCHEMA public TO rol_datos, rol_asistente;
ALTER ROLE rol_datos     SET search_path = oro, plata, public;
ALTER ROLE rol_asistente SET search_path = asistente, public;

-- Un rol de solo lectura para la API pública de B, que nunca escribe.
CREATE ROLE rol_api LOGIN PASSWORD '${CLAVE_DATOS}';
GRANT USAGE ON SCHEMA oro TO rol_api;
ALTER DEFAULT PRIVILEGES FOR ROLE rol_datos IN SCHEMA oro GRANT SELECT ON TABLES TO rol_api;
ALTER ROLE rol_api SET search_path = oro, public;
SQL

echo "Esquemas plata, oro y asistente creados con sus roles."
