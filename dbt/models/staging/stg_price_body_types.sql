select
    id as price_body_type_id,
    price_id,
    body_type_id
from {{ source('raw', 'price_body_types') }}
