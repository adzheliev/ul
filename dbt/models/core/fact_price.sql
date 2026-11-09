{{ config(
    post_hook=[
        "create index if not exists fact_price_loading_date_idx on {{ this }} (loading_date)",
        "create index if not exists fact_price_route_idx on {{ this }} (loading_city_gcid, unloading_city_gcid)"
    ]
) }}

select
    price_id,
    loading_date,
    end_loading_date,
    loading_city_gcid,
    unloading_city_gcid,
    distance,
    total_weight,
    total_volume,
    price,
    currency_code,
    price_rub,
    fx_rate,
    complex,
    price_type,
    is_fact,
    outlier_mark,
    organization_id,
    weight_category,
    volume_category,
    body_group,
    recomputed_outlier
from {{ ref('int_fact_price') }}
