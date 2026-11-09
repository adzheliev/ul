select
    id as body_type_id,
    name,
    id_from_1c,
    std_id
from {{ source('raw', 'body_types') }}
