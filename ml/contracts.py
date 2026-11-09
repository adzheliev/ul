"""Strict schema of the model matrix."""

import pandera.pandas as pa

from etl.quality.spec import BODY_GROUPS, VOLUME_LABELS, WEIGHT_LABELS
from ml.features import FEATURE_COLUMNS


class FeatureSchema(pa.DataFrameModel):
    """Model matrix. An extra column such as ``price_rub`` fails validation."""

    distance: float = pa.Field(gt=0)
    total_weight: float = pa.Field(ge=0)
    total_volume: float = pa.Field(ge=0)
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    year: float
    month: float
    day_of_week: float
    day_of_year: float
    month_sin: float
    month_cos: float
    dow_sin: float
    dow_cos: float
    doy_sin: float
    doy_cos: float
    origin_city: str
    origin_region: str
    destination_city: str
    destination_region: str
    body_group: str = pa.Field(isin=list(BODY_GROUPS))
    weight_category: str = pa.Field(isin=list(WEIGHT_LABELS))
    volume_category: str = pa.Field(isin=list(VOLUME_LABELS))

    class Config:
        strict = True
        coerce = True


def assert_feature_columns() -> None:
    """Fail fast when the schema and ``FEATURE_COLUMNS`` drift apart."""

    declared = set(FeatureSchema.to_schema().columns)
    expected = set(FEATURE_COLUMNS)
    if declared != expected:
        missing = sorted(expected - declared)
        extra = sorted(declared - expected)
        raise RuntimeError(f"feature schema drift missing={missing} extra={extra}")
