select
    id as price_date_id,
    price_id,
    price_date
from {{ source('raw', 'price_dates') }}
