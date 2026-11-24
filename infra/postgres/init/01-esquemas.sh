#!/bin/bash
# Crea la extensión, los esquemas y los roles de la base del Observatorio.
# Corre una sola vez, cuando se crea el volumen de PostgreSQL.
# Decisión: docs/adr/0002-postgresql-esquemas-roles.md
set -euo pipefail

CLAVE_DATOS="${POSTGRES_CLAVE_DATOS:-rol_datos}"
CLAVE_ASISTENTE="${POSTGRES_CLAVE_ASISTENTE:-rol_asistente}"
CLAVE_API="${POSTGRES_CLAVE_API:-rol_api}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v clave_datos="$CLAVE_DATOS" -v clave_asistente="$CLAVE_ASISTENTE" -v clave_api="$CLAVE_API" <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;

-- Un rol por componente. Ninguno recibe permisos sobre los esquemas del otro:
-- el Componente A obtiene los datos de B por la API.
CREATE ROLE rol_datos      LOGIN PASSWORD :'clave_datos';
CREATE ROLE rol_asistente  LOGIN PASSWORD :'clave_asistente';

-- La primera revisión usa oro. La segunda mueve los objetos a public.
CREATE SCHEMA oro   AUTHORIZATION rol_datos;

GRANT USAGE, CREATE ON SCHEMA public TO rol_datos;
GRANT USAGE ON SCHEMA public TO rol_asistente;
ALTER ROLE rol_datos SET search_path = public;

-- Un rol de solo lectura para la API pública de B, que nunca escribe.
CREATE ROLE rol_api LOGIN PASSWORD :'clave_api';
GRANT USAGE ON SCHEMA oro TO rol_api;
GRANT USAGE ON SCHEMA public TO rol_api;
ALTER ROLE rol_api SET search_path = public;
SQL

echo "Roles de PostgreSQL inicializados."
