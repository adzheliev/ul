select facts.price_id
from {{ ref('fact_price') }} as facts
inner join {{ source('dq', 'quarantine_prices') }} as rejected
    on rejected.source_price_id = facts.price_id
