{% macro body_group(body_type_id) -%}
case
    when {{ body_type_id }} is null then 'Не указан'
    when {{ body_type_id }} in (56, 57, 58, 59, 60, 61) then 'Тент'
    when {{ body_type_id }} in (4, 46, 47, 48) then 'Рефрижератор'
    when {{ body_type_id }} = 2 then 'Изотерм'
    when {{ body_type_id }} in (1, 15) then 'Борт'
    else 'Прочие'
end
{%- endmacro %}
