DELETE FROM raw.body_types;

INSERT INTO raw.body_types (id, name, id_from_1c, std_id)
SELECT id, name, "id_from_1C", std_id
FROM public.body_types;
