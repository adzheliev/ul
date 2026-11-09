INSERT INTO raw.price_dates (id, price_id, price_date)
SELECT link.id, link.price_id, link.price_date
FROM public.price_dates AS link
INNER JOIN public.prices AS price
    ON price.id = link.price_id
WHERE price.loading_date BETWEEN %(start)s AND %(end)s;
