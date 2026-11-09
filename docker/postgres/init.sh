#!/bin/bash
# First-boot roles and warehouse schemas. Source tables already exist.
set -euo pipefail

for file in /bootstrap/dwh/*.sql; do
  psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" -f "${file}"
done

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'etl') THEN
    CREATE ROLE etl LOGIN PASSWORD '${ETL_PASSWORD}';
  END IF;
END
\$\$;
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO etl;
GRANT CREATE ON DATABASE ${POSTGRES_DB} TO etl;
GRANT USAGE ON SCHEMA public TO etl;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO etl;
GRANT ALL ON SCHEMA raw, dq, staging, intermediate, core, mart TO etl;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA raw, dq, mart TO etl;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA dq, mart TO etl;

DO \$\$
DECLARE
    item record;
BEGIN
    FOR item IN
        SELECT nsp.nspname AS schema_name, cls.relname AS object_name, cls.relkind
        FROM pg_class AS cls
        JOIN pg_namespace AS nsp ON nsp.oid = cls.relnamespace
        WHERE nsp.nspname IN ('raw', 'dq', 'staging', 'intermediate', 'core', 'mart')
          AND cls.relkind IN ('r', 'p', 'v', 'm')
    LOOP
        IF item.relkind = 'v' THEN
            EXECUTE format('ALTER VIEW %I.%I OWNER TO etl', item.schema_name, item.object_name);
        ELSE
            EXECUTE format('ALTER TABLE %I.%I OWNER TO etl', item.schema_name, item.object_name);
        END IF;
    END LOOP;
END
\$\$;
SQL

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'airflow') THEN
    CREATE ROLE airflow LOGIN PASSWORD '${AIRFLOW_DB_PASSWORD}';
  END IF;
END
\$\$;
SQL

if ! psql -tAc "SELECT 1 FROM pg_database WHERE datname = 'airflow'" | grep -q 1; then
  psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" \
    -c "CREATE DATABASE airflow OWNER airflow"
fi

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'superset') THEN
    CREATE ROLE superset LOGIN PASSWORD '${SUPERSET_DB_PASSWORD}';
  END IF;
END
\$\$;
SQL

if ! psql -tAc "SELECT 1 FROM pg_database WHERE datname = 'superset'" | grep -q 1; then
  psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" \
    -c "CREATE DATABASE superset OWNER superset"
fi
