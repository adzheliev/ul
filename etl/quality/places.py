"""Parse ``cities.full_name_local`` values shaped as ``City, Region``."""


def parse_locality(full_name_local: str) -> tuple[str, str | None]:
    """Split a locality label on the first comma.

    The canonical city row is chosen in SQL (``min(id)`` per ``gc_id``) before
    this split runs. A label without a comma yields a city and no region.

    Returns:
        City name and region name. The region is ``None`` when it is absent.
    """

    city, separator, region = full_name_local.partition(",")
    cleaned_region = region.strip() if separator else ""
    return city.strip(), cleaned_region or None
