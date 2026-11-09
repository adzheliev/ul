"""Pandera contracts for warehouse outputs.

The model matrix lives in ``ml.contracts`` so the warehouse package does not
import the training code.
"""

import pandera.pandas as pa

from etl.quality.spec import BODY_GROUPS, RELIABILITY_LEVELS, VOLUME_LABELS, WEIGHT_LABELS


class CorePriceSchema(pa.DataFrameModel):
    """Rows allowed to leave core towards the mart and the trainer."""

    price_id: int
    price_rub: float = pa.Field(gt=0)
    distance: float = pa.Field(gt=0)
    total_weight: float = pa.Field(ge=0)
    total_volume: float = pa.Field(ge=0)
    currency_code: str = pa.Field(isin=["643", "840", "978"])
    weight_category: str = pa.Field(isin=list(WEIGHT_LABELS))
    volume_category: str = pa.Field(isin=list(VOLUME_LABELS))
    body_group: str = pa.Field(isin=list(BODY_GROUPS))
    outlier_mark: bool

    class Config:
        strict = False
        coerce = True


class RouteCardSchema(pa.DataFrameModel):
    """Serving grain of the market corridor."""

    loading_city_gcid: int
    unloading_city_gcid: int
    body_group: str = pa.Field(isin=list(BODY_GROUPS))
    weight_category: str = pa.Field(isin=list(WEIGHT_LABELS))
    trips_count: int = pa.Field(ge=1)
    carriers_count: int = pa.Field(ge=0)
    reliability_level: str = pa.Field(isin=list(RELIABILITY_LEVELS))

    class Config:
        strict = False
        coerce = True
