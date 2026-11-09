DELETE FROM raw.price_body_types AS link
WHERE link.price_id IN (
    SELECT id FROM raw.prices WHERE loading_date BETWEEN %(start)s AND %(end)s
    UNION
    SELECT id FROM public.prices WHERE loading_date BETWEEN %(start)s AND %(end)s
);
