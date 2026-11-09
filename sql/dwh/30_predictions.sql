-- Scorer outputs. dbt does not own these tables, so a mart rebuild cannot wipe them.

CREATE TABLE IF NOT EXISTS mart.ml_price_predictions (
    price_id              bigint           NOT NULL,
    loading_date          date             NOT NULL,
    loading_city_gcid     integer          NOT NULL,
    unloading_city_gcid   integer          NOT NULL,
    body_group            text             NOT NULL,
    actual_price_rub      double precision,
    predicted_price_rub   double precision NOT NULL,
    abs_error_rub         double precision,
    ape_pct               double precision,
    model_name            text             NOT NULL,
    scored_at             timestamptz      NOT NULL,
    PRIMARY KEY (price_id, model_name)
);

CREATE INDEX IF NOT EXISTS ml_price_predictions_loading_date_idx
    ON mart.ml_price_predictions (loading_date);

CREATE TABLE IF NOT EXISTS mart.ml_run (
    run_id      uuid PRIMARY KEY,
    model_name  text             NOT NULL,
    trained_at  timestamptz      NOT NULL,
    r2          double precision,
    mape_pct    double precision,
    rmse        double precision,
    mae         double precision,
    train_rows  integer          NOT NULL,
    test_rows   integer          NOT NULL,
    random_seed integer          NOT NULL
);
