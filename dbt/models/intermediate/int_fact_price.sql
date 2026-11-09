with rated as (
    select
        prices.price_id,
        prices.loading_date,
        prices.end_loading_date,
        prices.loading_city_gcid,
        prices.unloading_city_gcid,
        prices.distance,
        prices.total_weight,
        prices.total_volume,
        prices.body_type,
        prices.price,
        prices.currency_code,
        prices.complex,
        prices.price_type,
        prices.is_fact,
        prices.outlier_mark,
        prices.organization_id,
        case
            when prices.currency_code = '643' then prices.price
            else prices.price * rates.value
        end as price_rub,
        case
            when prices.currency_code = '643' then 1.0
            else rates.value
        end as fx_rate,
        coalesce(
            prices.weight_category,
            case
                when round(prices.total_weight::numeric, 1) >= 30 then 'G20T'
                when round(prices.total_weight::numeric, 1) >= 10 then 'FTL'
                when round(prices.total_weight::numeric, 1) >= 5 then '10T'
                when round(prices.total_weight::numeric, 1) >= 2.5 then '5T'
                when round(prices.total_weight::numeric, 1) >= 0.5 then 'L5T'
                else 'OTH'
            end
        ) as weight_category,
        coalesce(
            prices.volume_category,
            case
                when prices.total_volume > 0 and prices.total_volume <= 120 then 'FTL'
                else 'OTH'
            end
        ) as volume_category
    from {{ ref('int_accepted_price') }} as prices
    left join {{ ref('stg_exchange_rates') }} as rates
        on rates.num_code = prices.currency_code
        and rates.setting_date = prices.nearest_rate_date
    where prices.currency_code = '643'
        or rates.value is not null
),

chosen_body as (
    select distinct on (bridge.price_id)
        bridge.price_id,
        bridge.body_group
    from {{ ref('bridge_price_body_group') }} as bridge
    inner join rated
        on rated.price_id = bridge.price_id
    order by
        bridge.price_id,
        case
            when rated.body_type is not null and bridge.body_type_id = rated.body_type then 0
            else 1
        end,
        bridge.body_type_id nulls last
)

select
    rated.price_id,
    rated.loading_date,
    rated.end_loading_date,
    rated.loading_city_gcid,
    rated.unloading_city_gcid,
    rated.distance,
    rated.total_weight,
    rated.total_volume,
    rated.price,
    rated.currency_code,
    rated.price_rub,
    rated.fx_rate,
    rated.complex,
    rated.price_type,
    rated.is_fact,
    rated.outlier_mark,
    rated.organization_id,
    rated.weight_category,
    rated.volume_category,
    coalesce(chosen_body.body_group, 'Не указан') as body_group,
    coalesce(marked.recomputed_outlier, false) as recomputed_outlier
from rated
left join chosen_body
    on chosen_body.price_id = rated.price_id
left join {{ ref('int_recomputed_outlier') }} as marked
    on marked.price_id = rated.price_id
