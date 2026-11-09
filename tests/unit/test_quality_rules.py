"""DQ predicates and the SQL that must keep them."""

from pathlib import Path

from etl.quality.rules import price_reason_codes
from etl.quality.spec import ReasonCode

ROOT = Path(__file__).resolve().parents[2]
QUARANTINE_SQL = (ROOT / "sql" / "dml" / "refresh_quarantine.sql").read_text(encoding="utf-8")
STAGING_SQL = (ROOT / "dbt" / "models" / "staging" / "stg_prices.sql").read_text(encoding="utf-8")


def test_sql_names_every_reason_code():
    for code in ReasonCode:
        assert code.value in QUARANTINE_SQL


def test_same_city_is_not_a_reject_rule():
    assert "loading_city_gcid = p.unloading_city_gcid" not in QUARANTINE_SQL
    assert "loading_city_gcid = unloading_city_gcid" not in QUARANTINE_SQL


def test_staging_does_not_project_group_stats():
    assert "price_group_id" not in STAGING_SQL
    assert "avg_price" not in STAGING_SQL
    assert "min_km_price" not in STAGING_SQL


def test_zero_price_is_not_also_a_ruble_floor():
    reasons = price_reason_codes(
        price=0,
        currency_code="643",
        distance=100,
        total_weight=10,
        total_volume=20,
        loading_city_known=True,
        unloading_city_known=True,
        fx_rate_found=True,
    )
    assert reasons == (ReasonCode.NON_POSITIVE_PRICE,)


def test_ruble_floor_rejects_one_thousand_and_keeps_the_next_kopeck():
    rejected = price_reason_codes(
        price=1000,
        currency_code="643",
        distance=100,
        total_weight=10,
        total_volume=20,
        loading_city_known=True,
        unloading_city_known=True,
        fx_rate_found=True,
    )
    accepted = price_reason_codes(
        price=1000.01,
        currency_code="643",
        distance=100,
        total_weight=10,
        total_volume=20,
        loading_city_known=True,
        unloading_city_known=True,
        fx_rate_found=True,
    )
    assert rejected == (ReasonCode.RUB_PRICE_BELOW_SOURCE_MIN,)
    assert accepted == ()


def test_foreign_price_without_a_rate_is_quarantined():
    reasons = price_reason_codes(
        price=2480,
        currency_code="840",
        distance=2235,
        total_weight=18.5,
        total_volume=40,
        loading_city_known=True,
        unloading_city_known=True,
        fx_rate_found=False,
    )
    assert reasons == (ReasonCode.MISSING_FX_RATE,)


def test_outlier_flag_is_not_a_quarantine_reason():
    reasons = price_reason_codes(
        price=345000,
        currency_code="643",
        distance=897,
        total_weight=20,
        total_volume=80,
        loading_city_known=True,
        unloading_city_known=True,
        fx_rate_found=True,
    )
    assert reasons == ()


def test_same_city_with_known_endpoints_has_no_city_reason():
    reasons = price_reason_codes(
        price=50000,
        currency_code="643",
        distance=12,
        total_weight=5,
        total_volume=10,
        loading_city_known=True,
        unloading_city_known=True,
        fx_rate_found=True,
    )
    assert ReasonCode.UNKNOWN_LOADING_CITY not in reasons
    assert ReasonCode.UNKNOWN_UNLOADING_CITY not in reasons


def test_negative_measures_stack_with_an_unknown_city():
    reasons = price_reason_codes(
        price=50000,
        currency_code="643",
        distance=-1,
        total_weight=-0.1,
        total_volume=-2,
        loading_city_known=False,
        unloading_city_known=True,
        fx_rate_found=True,
    )
    assert reasons == (
        ReasonCode.NON_POSITIVE_DISTANCE,
        ReasonCode.NEGATIVE_WEIGHT,
        ReasonCode.NEGATIVE_VOLUME,
        ReasonCode.UNKNOWN_LOADING_CITY,
    )
