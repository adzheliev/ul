-- Replace price rows for an inclusive loading-date window.

DELETE FROM raw.prices
WHERE loading_date BETWEEN %(start)s AND %(end)s;

INSERT INTO raw.prices (
    id,
    created_at,
    updated_at,
    organization_id,
    loading_date,
    loading_city_gcid,
    unloading_city_gcid,
    distance,
    total_weight,
    total_volume,
    body_type,
    price,
    currency_code,
    complex,
    price_type,
    is_fact,
    nearest_rate_date,
    end_loading_date,
    outlier_mark,
    weight_category,
    volume_category,
    price_group_id,
    batch_id,
    loaded_at
)
SELECT
    id,
    created_at,
    updated_at,
    organization_id,
    loading_date,
    loading_city_gcid,
    unloading_city_gcid,
    distance,
    total_weight,
    total_volume,
    body_type,
    price,
    currency_code,
    complex,
    price_type,
    is_fact,
    nearest_rate_date,
    end_loading_date,
    outlier_mark,
    weight_category,
    volume_category,
    price_group_id,
    %(batch_id)s::uuid,
    now()
FROM public.prices
WHERE loading_date BETWEEN %(start)s AND %(end)s;
