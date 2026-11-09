"""The core suite accepts a clean frame and rejects a non-positive price."""

import pandas as pd

from etl.quality.expectations import validate_core_frame


def _frame(price_rub: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "price_id": 1,
                "price_rub": price_rub,
                "distance": 100.0,
                "total_weight": 10.0,
                "total_volume": 20.0,
                "currency_code": "643",
                "weight_category": "FTL",
                "volume_category": "FTL",
                "body_group": "Тент",
                "outlier_mark": False,
                "recomputed_outlier": False,
            }
        ]
    )


def test_core_suite_accepts_a_clean_price():
    outcome = validate_core_frame(_frame(50_000))
    assert outcome.success
    assert outcome.unexpected == 0


def test_core_suite_rejects_a_non_positive_price():
    outcome = validate_core_frame(_frame(0))
    assert not outcome.success
    assert outcome.unexpected >= 1


def test_core_suite_rejects_a_duplicate_price_id():
    frame = pd.concat([_frame(50_000), _frame(60_000)], ignore_index=True)
    outcome = validate_core_frame(frame)
    assert not outcome.success


def test_core_suite_rejects_a_missing_body_group():
    frame = _frame(50_000)
    frame.loc[0, "body_group"] = None
    outcome = validate_core_frame(frame)
    assert not outcome.success


def test_core_suite_rejects_an_unflagged_peak():
    frame = _frame(50_000)
    frame.loc[0, "distance"] = 10.0
    outcome = validate_core_frame(frame)
    assert not outcome.success


def test_core_suite_allows_a_peak_that_is_already_flagged():
    frame = _frame(50_000)
    frame.loc[0, "distance"] = 10.0
    frame.loc[0, "recomputed_outlier"] = True
    outcome = validate_core_frame(frame)
    assert outcome.success


def test_core_suite_rejects_a_short_batch():
    outcome = validate_core_frame(_frame(50_000), expected_rows=2)
    assert not outcome.success
