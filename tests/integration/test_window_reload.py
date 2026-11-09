"""A second load of the same window must not append rows or sums."""

from datetime import date

import psycopg
import pytest

from etl.config import DateWindow, Settings
from etl.db import connect
from etl.warehouse import load_raw, refresh_quarantine

WINDOW = DateWindow(start_date=date(2026, 9, 1), end_date=date(2026, 9, 7))


@pytest.mark.integration
def test_reloading_a_window_does_not_double_sums():
    settings = Settings()
    try:
        with connect(settings) as conn:
            source = _source_totals(conn)
    except psycopg.OperationalError as exc:
        pytest.skip(f"postgres is not reachable: {exc}")
    if source["count"] == 0:
        pytest.skip("the September window has no source prices")

    load_raw(settings, WINDOW)
    refresh_quarantine(settings, WINDOW)
    with connect(settings) as conn:
        first = _landed_totals(conn)
    load_raw(settings, WINDOW)
    refresh_quarantine(settings, WINDOW)
    with connect(settings) as conn:
        second = _landed_totals(conn)

    assert first == second
    assert first["raw_count"] == source["count"]
    assert first["raw_sum"] == source["price_sum"]


def _source_totals(conn) -> dict:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)::bigint, coalesce(round(sum(price)::numeric, 2), 0)
            FROM public.prices
            WHERE loading_date BETWEEN %s AND %s
            """,
            (WINDOW.start_date, WINDOW.end_date),
        )
        count, price_sum = cursor.fetchone()
    return {"count": int(count), "price_sum": price_sum}


def _landed_totals(conn) -> dict:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)::bigint, coalesce(round(sum(price)::numeric, 2), 0)
            FROM raw.prices
            WHERE loading_date BETWEEN %s AND %s
            """,
            (WINDOW.start_date, WINDOW.end_date),
        )
        raw_count, raw_sum = cursor.fetchone()
        cursor.execute(
            """
            SELECT count(*)::bigint, coalesce(round(sum(price)::numeric, 2), 0)
            FROM dq.quarantine_prices
            WHERE loading_date BETWEEN %s AND %s
            """,
            (WINDOW.start_date, WINDOW.end_date),
        )
        quarantine_count, quarantine_sum = cursor.fetchone()
    return {
        "raw_count": int(raw_count),
        "raw_sum": raw_sum,
        "quarantine_count": int(quarantine_count),
        "quarantine_sum": quarantine_sum,
    }
