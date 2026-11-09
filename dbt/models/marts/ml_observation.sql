{{ config(materialized='view') }}

select
    facts.price_id,
    facts.loading_date,
    facts.loading_city_gcid,
    facts.unloading_city_gcid,
    origin.city_name as origin_city,
    coalesce(origin.region_name, 'Не указан') as origin_region,
    origin.latitude as origin_lat,
    origin.longitude as origin_lon,
    destination.city_name as destination_city,
    coalesce(destination.region_name, 'Не указан') as destination_region,
    destination.latitude as destination_lat,
    destination.longitude as destination_lon,
    facts.distance,
    facts.total_weight,
    facts.total_volume,
    facts.body_group,
    facts.weight_category,
    facts.volume_category,
    facts.is_fact,
    facts.complex,
    facts.outlier_mark,
    facts.recomputed_outlier,
    facts.price_rub
from {{ ref('fact_price') }} as facts
inner join {{ ref('dim_city') }} as origin
    on origin.gc_id = facts.loading_city_gcid
inner join {{ ref('dim_city') }} as destination
    on destination.gc_id = facts.unloading_city_gcid
