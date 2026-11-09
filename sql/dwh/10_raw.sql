-- Landing tables. Column lists are the source contract we model.
-- price_group_id is landed for fidelity and is not projected by staging:
-- group stats already include the row being predicted.

CREATE TABLE IF NOT EXISTS raw.prices (
    id                  bigint PRIMARY KEY,
    created_at          timestamp(0),
    updated_at          timestamp(0),
    organization_id     integer,
    loading_date        date             NOT NULL,
    loading_city_gcid   integer          NOT NULL,
    unloading_city_gcid integer          NOT NULL,
    distance            double precision NOT NULL,
    total_weight        double precision NOT NULL,
    total_volume        double precision NOT NULL,
    body_type           integer,
    price               double precision NOT NULL,
    currency_code       varchar(3)       NOT NULL,
    complex             boolean          NOT NULL,
    price_type          smallint         NOT NULL,
    is_fact             boolean          NOT NULL,
    nearest_rate_date   date,
    end_loading_date    date,
    outlier_mark        boolean          NOT NULL,
    weight_category     varchar(4),
    volume_category     varchar(4),
    price_group_id      bigint,
    batch_id            uuid             NOT NULL,
    loaded_at           timestamptz      NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS raw_prices_loading_date_idx ON raw.prices (loading_date);

CREATE TABLE IF NOT EXISTS raw.cities (
    id              bigint PRIMARY KEY,
    full_name_local varchar(255) NOT NULL,
    full_name_gc    varchar(255) NOT NULL,
    gc_id           integer      NOT NULL,
    name            varchar(255) NOT NULL,
    longitude       double precision,
    latitude        double precision,
    created_at      timestamp(0),
    updated_at      timestamp(0)
);

CREATE INDEX IF NOT EXISTS raw_cities_gc_id_idx ON raw.cities (gc_id, id);

CREATE TABLE IF NOT EXISTS raw.body_types (
    id           bigint PRIMARY KEY,
    name         varchar(255) NOT NULL,
    id_from_1c   integer      NOT NULL,
    std_id       integer
);

CREATE TABLE IF NOT EXISTS raw.exchange_rates (
    id           bigint PRIMARY KEY,
    num_code     varchar(255)     NOT NULL,
    value        double precision NOT NULL,
    setting_date date             NOT NULL
);

CREATE INDEX IF NOT EXISTS raw_exchange_rates_lookup_idx
    ON raw.exchange_rates (num_code, setting_date);

CREATE TABLE IF NOT EXISTS raw.price_body_types (
    id           bigint PRIMARY KEY,
    price_id     bigint  NOT NULL,
    body_type_id integer NOT NULL,
    UNIQUE (price_id, body_type_id)
);

CREATE TABLE IF NOT EXISTS raw.price_dates (
    id         bigint PRIMARY KEY,
    price_id   bigint NOT NULL,
    price_date date   NOT NULL,
    UNIQUE (price_id, price_date)
);

CREATE INDEX IF NOT EXISTS raw_price_dates_price_id_idx ON raw.price_dates (price_id);
