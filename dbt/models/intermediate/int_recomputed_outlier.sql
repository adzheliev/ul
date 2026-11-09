-- MarkOutlierPrices analogue. Not a quarantine reason and not a model feature.
-- Population: accepted facts with a price_group_id, price > 0 and distance > 0.
-- Groups smaller than 4 are unmarked. Fences use percentile_cont inside the group:
-- Tukey 1.5*IQR on raw price, and P5–P95 on raw price/distance. Either fence marks the row.

with eligible as (
    select
        prices.id as price_id,
        prices.price_group_id,
        prices.price,
        prices.distance
    from {{ source('raw', 'prices') }} as prices
    where prices.is_fact
        and prices.price_group_id is not null
        and prices.price > 0
        and prices.distance > 0
        and not exists (
            select 1
            from {{ source('dq', 'quarantine_prices') }} as rejected
            where rejected.source_price_id = prices.id
        )
),

bounds as (
    select
        price_group_id,
        percentile_cont(0.25) within group (order by price) as price_q1,
        percentile_cont(0.75) within group (order by price) as price_q3,
        percentile_cont(0.05) within group (order by price / distance) as km_p5,
        percentile_cont(0.95) within group (order by price / distance) as km_p95
    from eligible
    group by price_group_id
    having count(*) >= 4
)

select
    eligible.price_id,
    (
        eligible.price < bounds.price_q1 - 1.5 * (bounds.price_q3 - bounds.price_q1)
        or eligible.price > bounds.price_q3 + 1.5 * (bounds.price_q3 - bounds.price_q1)
        or eligible.price / eligible.distance < bounds.km_p5
        or eligible.price / eligible.distance > bounds.km_p95
    ) as recomputed_outlier
from eligible
inner join bounds
    on bounds.price_group_id = eligible.price_group_id
