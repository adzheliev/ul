with cells as (
    select * from {{ ref('int_route_agg') }}
)

select
    cells.price_month,
    cells.loading_city_gcid,
    coalesce(origin.city_name, '') as loading_city_name,
    coalesce(origin.region_name, '') as loading_region,
    cells.unloading_city_gcid,
    coalesce(destination.city_name, '') as unloading_city_name,
    coalesce(destination.region_name, '') as unloading_region,
    cells.body_group,
    cells.weight_category,
    cells.trips_count,
    cells.carriers_count,
    cells.p25_trip,
    cells.median_trip,
    cells.p75_trip,
    cells.avg_trip,
    cells.p25_km,
    cells.median_km,
    cells.p75_km,
    cells.cv_rate,
    case
        when previous.median_trip is null or previous.median_trip = 0 then null
        else (cells.median_trip - previous.median_trip) / previous.median_trip * 100
    end as mom_pct,
    case
        when year_ago.median_trip is null or year_ago.median_trip = 0 then null
        else (cells.median_trip - year_ago.median_trip) / year_ago.median_trip * 100
    end as yoy_pct,
    case
        when cells.trips_count >= {{ var('high_min_trips') }}
            and cells.carriers_count >= {{ var('high_min_carriers') }}
            and (
                '{{ var("as_of") }}'::date - cells.price_month::date
            ) <= {{ var('high_max_age_days') }}
            then 'HIGH'
        when cells.trips_count >= {{ var('medium_min_trips') }} then 'MEDIUM'
        else 'LOW_DATA'
    end as reliability_level,
    '{{ var("as_of") }}'::date as as_of
from cells
left join cells as previous
    on previous.price_month = (cells.price_month::date - interval '1 month')::date
    and previous.loading_city_gcid = cells.loading_city_gcid
    and previous.unloading_city_gcid = cells.unloading_city_gcid
    and previous.body_group = cells.body_group
    and previous.weight_category = cells.weight_category
left join cells as year_ago
    on year_ago.price_month = (cells.price_month::date - interval '1 year')::date
    and year_ago.loading_city_gcid = cells.loading_city_gcid
    and year_ago.unloading_city_gcid = cells.unloading_city_gcid
    and year_ago.body_group = cells.body_group
    and year_ago.weight_category = cells.weight_category
left join {{ ref('dim_city') }} as origin
    on origin.gc_id = cells.loading_city_gcid
left join {{ ref('dim_city') }} as destination
    on destination.gc_id = cells.unloading_city_gcid
