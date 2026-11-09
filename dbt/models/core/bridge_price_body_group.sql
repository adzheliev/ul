with linked as (
    select
        prices.price_id,
        links.body_type_id
    from {{ ref('int_accepted_price') }} as prices
    inner join {{ ref('stg_price_body_types') }} as links
        on links.price_id = prices.price_id
),

fallback as (
    select
        prices.price_id,
        prices.body_type as body_type_id
    from {{ ref('int_accepted_price') }} as prices
    where prices.body_type is not null
        and not exists (
            select 1
            from {{ ref('stg_price_body_types') }} as links
            where links.price_id = prices.price_id
        )
),

unspecified as (
    select
        prices.price_id,
        null::integer as body_type_id
    from {{ ref('int_accepted_price') }} as prices
    where prices.body_type is null
        and not exists (
            select 1
            from {{ ref('stg_price_body_types') }} as links
            where links.price_id = prices.price_id
        )
),

unioned as (
    select * from linked
    union all
    select * from fallback
    union all
    select * from unspecified
),

mapped as (
    select
        price_id,
        body_type_id,
        {{ body_group('body_type_id') }} as body_group
    from unioned
)

select distinct on (price_id, body_group)
    price_id,
    body_group,
    body_type_id
from mapped
order by price_id, body_group, body_type_id nulls last
