-- Warehouse schemas.
--
-- raw:   landing of one source window. Facts are replaced per window.
-- dq:    dead-letter and batch audit. Not a hop between raw and core.
-- core:  conformed tables, created by dbt.
-- mart:  serving tables. The route card is built by dbt in Postgres and
--        copied into ClickHouse. Predictions are written by the scorer.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS dq;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;
