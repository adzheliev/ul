select
    price_month,
    loading_city_gcid,
    unloading_city_gcid,
    body_group,
    weight_category
from {{ ref('mart_route_card') }}
group by 1, 2, 3, 4, 5
having count(*) > 1
