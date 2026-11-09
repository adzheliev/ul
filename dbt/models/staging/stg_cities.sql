select
    id as city_id,
    gc_id,
    full_name_local,
    name,
    latitude,
    longitude
from {{ source('raw', 'cities') }}
