"""Feature contract: cyclical dates and a strict matrix."""

import math

import pandas as pd
import pytest
from pandera.errors import SchemaErrors

from ml.contracts import FeatureSchema, assert_feature_columns
from ml.features import FEATURE_COLUMNS, LEAKAGE_COLUMNS, build_features, cyclical
from ml.metrics import regression_metrics


def test_december_is_closer_to_january_than_to_june():
    december = cyclical(12, 12)
    january = cyclical(1, 12)
    june = cyclical(6, 12)
    assert math.dist(december, january) < math.dist(december, june)


def test_feature_columns_match_the_pandera_contract():
    assert_feature_columns()
    assert LEAKAGE_COLUMNS.isdisjoint(FEATURE_COLUMNS)


def test_builder_drops_the_target():
    features = build_features(_observation(price_rub=80_000))
    assert "price_rub" not in features.columns
    assert list(features.columns) == list(FEATURE_COLUMNS)
    FeatureSchema.validate(features)


def test_strict_schema_rejects_a_leaked_target():
    features = build_features(_observation(price_rub=80_000))
    leaked = features.copy()
    leaked["price_rub"] = 80_000
    with pytest.raises(SchemaErrors):
        FeatureSchema.validate(leaked)


def test_metrics_match_a_known_pair():
    metrics = regression_metrics([100.0, 200.0], [110.0, 150.0])
    assert metrics["mae"] == pytest.approx(30)
    assert metrics["mape_pct"] == pytest.approx((10 / 100 + 50 / 200) / 2 * 100)


def _observation(price_rub: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "loading_date": "2026-10-06",
                "distance": 800,
                "total_weight": 20,
                "total_volume": 82,
                "origin_lat": 55.75,
                "origin_lon": 37.62,
                "destination_lat": 55.79,
                "destination_lon": 49.11,
                "origin_city": "Москва",
                "origin_region": "г. Москва",
                "destination_city": "Казань",
                "destination_region": "Республика Татарстан",
                "body_group": "Тент",
                "weight_category": "FTL",
                "volume_category": "FTL",
                "price_rub": price_rub,
                "outlier_mark": False,
            }
        ]
    )
