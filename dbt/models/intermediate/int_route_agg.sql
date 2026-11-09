with base as (
    select
        facts.price_id,
        date_trunc('month', dates.price_date)::date as price_month,
        facts.loading_city_gcid,
        facts.unloading_city_gcid,
        groups.body_group,
        facts.weight_category,
        facts.price_rub,
        facts.distance,
        facts.organization_id,
        facts.price_type
    from {{ ref('fact_price') }} as facts
    inner join {{ ref('bridge_price_body_group') }} as groups
        on groups.price_id = facts.price_id
    inner join {{ ref('stg_price_dates') }} as dates
        on dates.price_id = facts.price_id
    where facts.is_fact
        and not facts.complex
        and facts.price_rub > 0
        and facts.distance > 0
        and not facts.outlier_mark
        and not facts.recomputed_outlier
        and dates.price_date <= '{{ var("as_of") }}'::date
),

dedup as (
    select distinct
        price_id,
        price_month,
        loading_city_gcid,
        unloading_city_gcid,
        body_group,
        weight_category,
        price_rub,
        distance,
        organization_id,
        price_type
    from base
)

select
    price_month,
    loading_city_gcid,
    unloading_city_gcid,
    body_group,
    weight_category,
    count(*)::integer as trips_count,
    count(distinct organization_id) filter (
        where price_type in (3, 9)
    )::integer as carriers_count,
    percentile_cont(0.25) within group (order by price_rub) as p25_trip,
    percentile_cont(0.50) within group (order by price_rub) as median_trip,
    percentile_cont(0.75) within group (order by price_rub) as p75_trip,
    avg(price_rub) as avg_trip,
    percentile_cont(0.25) within group (order by price_rub / nullif(distance, 0)) as p25_km,
    percentile_cont(0.50) within group (order by price_rub / nullif(distance, 0)) as median_km,
    percentile_cont(0.75) within group (order by price_rub / nullif(distance, 0)) as p75_km,
    case
        when count(*) < 2 or avg(price_rub) = 0 then null
        else stddev_samp(price_rub) / avg(price_rub)
    end as cv_rate
from dedup
group by 1, 2, 3, 4, 5
