INSERT INTO raw.price_body_types (id, price_id, body_type_id)
SELECT link.id, link.price_id, link.body_type_id
FROM public.price_body_types AS link
INNER JOIN public.prices AS price
    ON price.id = link.price_id
WHERE price.loading_date BETWEEN %(start)s AND %(end)s;
