-- Dead-letter for prices that failed a DQ rule.
-- One row per (source price, reason). A price with any row here is excluded
-- from core. Outliers are not written here.
--
-- The assignment name is dq_quarantine_prices. The physical table is
-- dq.quarantine_prices; the view below is the spec alias.

CREATE TABLE IF NOT EXISTS dq.quarantine_prices (
    quarantine_id       bigserial PRIMARY KEY,
    batch_id            uuid             NOT NULL,
    source_price_id     bigint           NOT NULL,
    reason_code         text             NOT NULL,
    loading_date        date             NOT NULL,
    currency_code       text             NOT NULL,
    price               double precision NOT NULL,
    distance            double precision NOT NULL,
    total_weight        double precision NOT NULL,
    total_volume        double precision NOT NULL,
    loading_city_gcid   integer          NOT NULL,
    unloading_city_gcid integer          NOT NULL,
    nearest_rate_date   date,
    detected_at         timestamptz      NOT NULL DEFAULT now(),
    CONSTRAINT quarantine_prices_reason_uniq UNIQUE (source_price_id, reason_code)
);

CREATE INDEX IF NOT EXISTS quarantine_prices_loading_date_idx
    ON dq.quarantine_prices (loading_date);

COMMENT ON TABLE dq.quarantine_prices IS
    'Dead-letter for rejected prices (assignment table dq_quarantine_prices). Not a DWH layer.';

CREATE OR REPLACE VIEW dq.dq_quarantine_prices AS
SELECT * FROM dq.quarantine_prices;

CREATE TABLE IF NOT EXISTS dq.batch_audit (
    batch_id         uuid PRIMARY KEY,
    window_start     date        NOT NULL,
    window_end       date        NOT NULL,
    started_at       timestamptz NOT NULL,
    finished_at      timestamptz,
    rows_read        integer,
    rows_quarantined integer,
    rows_accepted    integer,
    gx_success       boolean,
    detail           text
);

CREATE TABLE IF NOT EXISTS dq.expectation_result (
    id           bigserial PRIMARY KEY,
    batch_id     uuid        NOT NULL,
    suite_name   text        NOT NULL,
    success      boolean     NOT NULL,
    evaluated    integer,
    unexpected   integer,
    ran_at       timestamptz NOT NULL DEFAULT now()
);
