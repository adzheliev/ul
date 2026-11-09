DELETE FROM raw.exchange_rates;

INSERT INTO raw.exchange_rates (id, num_code, value, setting_date)
SELECT id, num_code, value, setting_date
FROM public.exchange_rates;
