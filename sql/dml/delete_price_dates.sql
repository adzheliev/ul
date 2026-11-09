DELETE FROM raw.price_dates AS link
WHERE link.price_id IN (
    SELECT id FROM raw.prices WHERE loading_date BETWEEN %(start)s AND %(end)s
    UNION
    SELECT id FROM public.prices WHERE loading_date BETWEEN %(start)s AND %(end)s
);
