"""Reliability band for one market cell.

The mart SQL encodes the same thresholds via dbt vars. Age is the number of
days from the cell month (first day) to ``as_of``.
"""

from datetime import date

from etl.quality.spec import (
    HIGH_MAX_AGE_DAYS,
    HIGH_MIN_CARRIERS,
    HIGH_MIN_TRIPS,
    MEDIUM_MIN_TRIPS,
)


def reliability_level(
    *,
    trips_count: int,
    carriers_count: int,
    price_month: date,
    as_of: date,
) -> str:
    """Return ``HIGH``, ``MEDIUM``, or ``LOW_DATA`` for one corridor cell."""

    fresh = (as_of - price_month).days <= HIGH_MAX_AGE_DAYS
    if trips_count >= HIGH_MIN_TRIPS and carriers_count >= HIGH_MIN_CARRIERS and fresh:
        return "HIGH"
    if trips_count >= MEDIUM_MIN_TRIPS:
        return "MEDIUM"
    return "LOW_DATA"


def relative_change_pct(current: float | None, previous: float | None) -> float | None:
    """Percent change against a calendar neighbour.

    A missing neighbour or a zero baseline stays null. The mart must not
    substitute the latest available month.
    """

    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / previous * 100.0
