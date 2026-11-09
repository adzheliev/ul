select
    id as exchange_rate_id,
    num_code,
    value,
    setting_date
from {{ source('raw', 'exchange_rates') }}
