CREATE DATABASE IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS mart.mart_route_card
(
    price_month Date,
    loading_city_gcid Int32,
    loading_city_name String,
    loading_region String,
    unloading_city_gcid Int32,
    unloading_city_name String,
    unloading_region String,
    body_group LowCardinality(String),
    weight_category LowCardinality(String),
    trips_count UInt32,
    carriers_count UInt32,
    p25_trip Float64,
    median_trip Float64,
    p75_trip Float64,
    avg_trip Float64,
    p25_km Float64,
    median_km Float64,
    p75_km Float64,
    cv_rate Nullable(Float64),
    mom_pct Nullable(Float64),
    yoy_pct Nullable(Float64),
    reliability_level LowCardinality(String),
    as_of Date
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(price_month)
ORDER BY (price_month, loading_city_gcid, unloading_city_gcid, body_group, weight_category);

CREATE TABLE IF NOT EXISTS mart.ml_price_predictions
(
    price_id Int64,
    loading_date Date,
    loading_city_gcid Int32,
    unloading_city_gcid Int32,
    body_group LowCardinality(String),
    actual_price_rub Nullable(Float64),
    predicted_price_rub Float64,
    abs_error_rub Nullable(Float64),
    ape_pct Nullable(Float64),
    model_name LowCardinality(String),
    scored_at DateTime64(6, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(loading_date)
ORDER BY (model_name, loading_date, price_id);
