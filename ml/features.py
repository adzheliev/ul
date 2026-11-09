"""Feature contract for the tariff regressor.

``price_rub`` is the target and is never a column of the model frame.
Group stats, VAT, unit rates, and ``outlier_mark`` are rejected by name and
by the strict Pandera schema.
"""

import math
from datetime import date

import pandas as pd

from etl.quality.places import parse_locality

LEAKAGE_COLUMNS = frozenset(
    {
        "price",
        "price_rub",
        "price_with_vat",
        "price_km",
        "price_per_km",
        "price_per_weight",
        "avg_price",
        "min_km_price",
        "max_km_price",
        "price_group_id",
        "price_group_stats",
        "outlier_mark",
        "recomputed_outlier",
        "carrier_cost",
        "customer_cost",
        "transportation_cost",
        "profit",
        "fx_rate",
    }
)

CATEGORY_COLUMNS = (
    "origin_city",
    "origin_region",
    "destination_city",
    "destination_region",
    "body_group",
    "weight_category",
    "volume_category",
)

NUMERIC_COLUMNS = (
    "distance",
    "total_weight",
    "total_volume",
    "origin_lat",
    "origin_lon",
    "destination_lat",
    "destination_lon",
    "year",
    "month",
    "day_of_week",
    "day_of_year",
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
    "doy_sin",
    "doy_cos",
)

FEATURE_COLUMNS = NUMERIC_COLUMNS + CATEGORY_COLUMNS

MONTH_PERIOD = 12.0
DOW_PERIOD = 7.0
DOY_PERIOD = 365.25
MISSING_CATEGORY = "Не указан"


def cyclical(value: float, period: float) -> tuple[float, float]:
    """Encode a cyclic value on the unit circle.

    Month 12 and month 1 are one step apart, as are Sunday and Monday.
    """

    angle = 2.0 * math.pi * value / period
    return math.sin(angle), math.cos(angle)


def calendar_features(loading_date: date) -> dict[str, float]:
    """Year, calendar parts, and sin/cos terms for one loading date.

    ``day_of_week`` is ISO (Monday = 1, Sunday = 7) so the week wraps.
    """

    month = float(loading_date.month)
    day_of_week = float(loading_date.isoweekday())
    day_of_year = float(loading_date.timetuple().tm_yday)
    month_sin, month_cos = cyclical(month, MONTH_PERIOD)
    dow_sin, dow_cos = cyclical(day_of_week, DOW_PERIOD)
    doy_sin, doy_cos = cyclical(day_of_year, DOY_PERIOD)
    return {
        "year": float(loading_date.year),
        "month": month,
        "day_of_week": day_of_week,
        "day_of_year": day_of_year,
        "month_sin": month_sin,
        "month_cos": month_cos,
        "dow_sin": dow_sin,
        "dow_cos": dow_cos,
        "doy_sin": doy_sin,
        "doy_cos": doy_cos,
    }


def regions_from_labels(origin_label: str, destination_label: str) -> dict[str, str | None]:
    """Parse origin and destination labels independently.

    A concatenated route string is intentionally not returned: its cardinality
    is too high for rare lanes.
    """

    origin_city, origin_region = parse_locality(origin_label)
    destination_city, destination_region = parse_locality(destination_label)
    return {
        "origin_city": origin_city,
        "origin_region": origin_region,
        "destination_city": destination_city,
        "destination_region": destination_region,
    }


def _category(value: object) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return MISSING_CATEGORY
    text = str(value).strip()
    return text or MISSING_CATEGORY


def build_features(observations: pd.DataFrame) -> pd.DataFrame:
    """Project an observation frame onto the model columns.

    The input may contain the target and audit flags. None of those columns
    are copied. Calling this with a frame that only has leakage columns and
    no distance raises ``KeyError`` rather than training on an empty trick.

    Args:
        observations: Rows from ``mart.ml_observation`` plus any extra fields.

    Returns:
        A frame whose columns are exactly ``FEATURE_COLUMNS``.
    """

    leaked = LEAKAGE_COLUMNS.intersection(FEATURE_COLUMNS)
    if leaked:
        raise RuntimeError(f"feature contract includes leakage columns: {sorted(leaked)}")

    frame = observations.copy()
    dates = pd.to_datetime(frame["loading_date"]).dt.date
    calendar = pd.DataFrame([calendar_features(value) for value in dates], index=frame.index)
    features = pd.DataFrame(index=frame.index)
    for column in (
        "distance",
        "total_weight",
        "total_volume",
        "origin_lat",
        "origin_lon",
        "destination_lat",
        "destination_lon",
    ):
        features[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in CATEGORY_COLUMNS:
        features[column] = frame[column].map(_category)
    for column in calendar.columns:
        features[column] = calendar[column]
    return features.loc[:, list(FEATURE_COLUMNS)]
