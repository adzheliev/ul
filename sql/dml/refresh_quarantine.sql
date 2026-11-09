-- Replace the dead-letter slice for one inclusive loading-date window.
-- Predicates match etl.quality.rules.price_reason_codes.

DELETE FROM dq.quarantine_prices
WHERE loading_date BETWEEN %(start)s AND %(end)s;

INSERT INTO dq.quarantine_prices (
    batch_id,
    source_price_id,
    reason_code,
    loading_date,
    currency_code,
    price,
    distance,
    total_weight,
    total_volume,
    loading_city_gcid,
    unloading_city_gcid,
    nearest_rate_date
)
SELECT
    %(batch_id)s::uuid,
    p.id,
    r.reason_code,
    p.loading_date,
    p.currency_code,
    p.price,
    p.distance,
    p.total_weight,
    p.total_volume,
    p.loading_city_gcid,
    p.unloading_city_gcid,
    p.nearest_rate_date
FROM raw.prices AS p
CROSS JOIN LATERAL (
    VALUES
        ('NON_POSITIVE_PRICE', p.price <= 0),
        (
            'RUB_PRICE_BELOW_SOURCE_MIN',
            p.currency_code = '643' AND p.price > 0 AND p.price <= 1000
        ),
        ('NON_POSITIVE_DISTANCE', p.distance <= 0),
        ('NEGATIVE_WEIGHT', p.total_weight < 0),
        ('NEGATIVE_VOLUME', p.total_volume < 0),
        (
            'UNKNOWN_LOADING_CITY',
            NOT EXISTS (
                SELECT 1 FROM raw.cities AS c WHERE c.gc_id = p.loading_city_gcid
            )
        ),
        (
            'UNKNOWN_UNLOADING_CITY',
            NOT EXISTS (
                SELECT 1 FROM raw.cities AS c WHERE c.gc_id = p.unloading_city_gcid
            )
        ),
        (
            'MISSING_FX_RATE',
            p.currency_code <> '643'
            AND NOT EXISTS (
                SELECT 1
                FROM raw.exchange_rates AS er
                WHERE er.num_code = p.currency_code
                  AND er.setting_date = p.nearest_rate_date
            )
        )
) AS r(reason_code, failed)
WHERE p.loading_date BETWEEN %(start)s AND %(end)s
  AND r.failed;
