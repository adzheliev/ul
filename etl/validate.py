"""Publish gates: relational check, Pandera, and Great Expectations."""

import logging

import pandas as pd

from etl.config import Settings
from etl.db import connect
from etl.errors import DataQualityError
from etl.quality.expectations import validate_core_frame
from etl.quality.pandera_models import CorePriceSchema

logger = logging.getLogger(__name__)

CORE_SQL = """
SELECT
    price_id,
    price_rub,
    distance,
    total_weight,
    total_volume,
    currency_code,
    weight_category,
    volume_category,
    body_group,
    outlier_mark,
    recomputed_outlier
FROM core.fact_price
"""

EXPECTED_ROWS_SQL = """
SELECT
    (SELECT count(*) FROM raw.prices)
    - (SELECT count(DISTINCT source_price_id) FROM dq.quarantine_prices)
"""


def validate_core(settings: Settings) -> None:
    """Fail the batch when a quarantined price leaked into core or a suite fails."""

    with connect(settings) as conn:
        leaked = _quarantine_leak_count(conn)
        if leaked:
            raise DataQualityError(f"{leaked} quarantined prices are present in core.fact_price")
        frame = pd.read_sql_query(CORE_SQL, conn)
        CorePriceSchema.validate(frame)
        outcome = validate_core_frame(frame, expected_rows=_expected_core_rows(conn))
        _store_outcome(conn, outcome)
    if not outcome.success:
        raise DataQualityError(
            f"Great Expectations suite {outcome.suite_name} failed "
            f"({outcome.unexpected} of {outcome.evaluated})"
        )
    logger.info(
        "gx suite %s success evaluated=%s",
        outcome.suite_name,
        outcome.evaluated,
    )


def _expected_core_rows(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute(EXPECTED_ROWS_SQL)
        return int(cursor.fetchone()[0])


def _quarantine_leak_count(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*)
            FROM core.fact_price AS facts
            INNER JOIN dq.quarantine_prices AS rejected
                ON rejected.source_price_id = facts.price_id
            """
        )
        return int(cursor.fetchone()[0])


def _store_outcome(conn, outcome) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO dq.expectation_result (batch_id, suite_name, success, evaluated, unexpected)
            SELECT batch_id, %s, %s, %s, %s
            FROM dq.batch_audit
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (outcome.suite_name, outcome.success, outcome.evaluated, outcome.unexpected),
        )
        cursor.execute(
            """
            UPDATE dq.batch_audit
            SET gx_success = %s,
                finished_at = now()
            WHERE batch_id = (
                SELECT batch_id FROM dq.batch_audit ORDER BY started_at DESC LIMIT 1
            )
            """,
            (outcome.success,),
        )
