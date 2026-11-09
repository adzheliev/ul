DELETE FROM raw.cities;

INSERT INTO raw.cities (
    id, full_name_local, full_name_gc, gc_id, name, longitude, latitude, created_at, updated_at
)
SELECT
    id, full_name_local, full_name_gc, gc_id, name, longitude, latitude, created_at, updated_at
FROM public.cities;
