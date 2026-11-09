select price_id, body_group
from {{ ref('bridge_price_body_group') }}
group by 1, 2
having count(*) > 1
