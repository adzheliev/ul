with ranked as (
    select
        city_id,
        gc_id,
        full_name_local,
        latitude,
        longitude,
        row_number() over (partition by gc_id order by city_id) as row_number
    from {{ ref('stg_cities') }}
)

select
    gc_id,
    city_id,
    btrim(split_part(full_name_local, ',', 1)) as city_name,
    nullif(btrim(split_part(full_name_local, ',', 2)), '') as region_name,
    latitude,
    longitude
from ranked
where row_number = 1
