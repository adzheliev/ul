"""Category boundaries and the fixed train/test dates."""

from datetime import date

import pytest
from pydantic import ValidationError

from etl.config import DateWindow
from etl.quality.categories import (
    fill_weight_category,
    volume_category,
    weight_category,
)
from etl.quality.places import parse_locality
from etl.quality.reliability import relative_change_pct, reliability_level
from ml.splits import cohort


def test_weight_bands_follow_the_rounded_tenth():
    assert weight_category(30) == "G20T"
    assert weight_category(29.96) == "G20T"
    assert weight_category(10) == "FTL"
    assert weight_category(9.96) == "FTL"
    assert weight_category(5) == "10T"
    assert weight_category(2.5) == "5T"
    assert weight_category(0.5) == "L5T"
    assert weight_category(0.44) == "OTH"


def test_volume_band_is_open_at_zero_and_closed_at_120():
    assert volume_category(0) == "OTH"
    assert volume_category(120) == "FTL"
    assert volume_category(120.01) == "OTH"


def test_filled_category_keeps_a_source_value():
    assert fill_weight_category("FTL", 31) == "FTL"
    assert fill_weight_category(None, 31) == "G20T"


def test_locality_split_uses_the_first_comma():
    assert parse_locality("Казань, Республика Татарстан") == ("Казань", "Республика Татарстан")
    assert parse_locality("Москва") == ("Москва", None)


def test_time_split_boundary_belongs_to_test():
    assert cohort(date(2026, 7, 25)) == "history"
    assert cohort(date(2026, 7, 26)) == "train"
    assert cohort(date(2026, 10, 4)) == "train"
    assert cohort(date(2026, 10, 5)) == "test"
    assert cohort(date(2026, 10, 26)) == "test"
    assert cohort(date(2026, 10, 27)) == "future"


def test_reliability_requires_freshness_for_high():
    assert (
        reliability_level(
            trips_count=30,
            carriers_count=5,
            price_month=date(2026, 10, 1),
            as_of=date(2026, 10, 26),
        )
        == "HIGH"
    )
    assert (
        reliability_level(
            trips_count=40,
            carriers_count=8,
            price_month=date(2026, 8, 1),
            as_of=date(2026, 10, 26),
        )
        == "MEDIUM"
    )
    assert (
        reliability_level(
            trips_count=10,
            carriers_count=1,
            price_month=date(2026, 10, 1),
            as_of=date(2026, 10, 26),
        )
        == "MEDIUM"
    )
    assert (
        reliability_level(
            trips_count=9,
            carriers_count=9,
            price_month=date(2026, 10, 1),
            as_of=date(2026, 10, 26),
        )
        == "LOW_DATA"
    )


def test_relative_change_stays_null_without_a_calendar_neighbour():
    assert relative_change_pct(110, None) is None
    assert relative_change_pct(110, 0) is None
    assert relative_change_pct(110, 100) == pytest.approx(10)


def test_window_rejects_an_inverted_range():
    with pytest.raises(ValidationError):
        DateWindow(start_date=date(2026, 10, 2), end_date=date(2026, 10, 1))
