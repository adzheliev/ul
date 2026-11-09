select prices.*
from {{ ref('stg_prices') }} as prices
where not exists (
    select 1
    from {{ source('dq', 'quarantine_prices') }} as rejected
    where rejected.source_price_id = prices.price_id
)
