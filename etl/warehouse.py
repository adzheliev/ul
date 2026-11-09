"""Load a date window into raw and refresh the dead-letter slice."""

import logging
import uuid

from psycopg import Connection

from etl.config import DateWindow, Settings
from etl.db import connect
from etl.paths import SQL_DIR
from etl.sql_exec import execute_file

logger = logging.getLogger(__name__)

DWH_DIR = SQL_DIR / "dwh"
DML_DIR = SQL_DIR / "dml"


def apply_ddl(conn: Connection) -> None:
    """Create schemas and operational tables. Safe to repeat."""

    for path in sorted(DWH_DIR.glob("*.sql")):
        execute_file(conn, path)


def load_raw(
    settings: Settings, window: DateWindow, batch_id: uuid.UUID | None = None
) -> uuid.UUID:
    """Replace dimensions and one fact slice in ``raw``.

    Facts, body links, and price dates use the same inclusive ``loading_date``
    predicate for delete and insert. A rerun replaces the slice.
    """

    batch_id = batch_id or uuid.uuid4()
    params = _params(window, batch_id)
    with connect(settings) as conn:
        apply_ddl(conn)
        with conn.transaction():
            for name in ("load_cities.sql", "load_body_types.sql", "load_rates.sql"):
                execute_file(conn, DML_DIR / name)
            execute_file(conn, DML_DIR / "delete_body_links.sql", params)
            execute_file(conn, DML_DIR / "delete_price_dates.sql", params)
            execute_file(conn, DML_DIR / "load_prices.sql", params)
            execute_file(conn, DML_DIR / "insert_body_links.sql", params)
            execute_file(conn, DML_DIR / "insert_price_dates.sql", params)
    logger.info("raw window %s..%s batch=%s", window.start_date, window.end_date, batch_id)
    return batch_id


def refresh_quarantine(
    settings: Settings,
    window: DateWindow,
    batch_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Rewrite dead-letter rows for the window and record batch counts."""

    batch_id = batch_id or uuid.uuid4()
    params = _params(window, batch_id)
    with connect(settings) as conn:
        apply_ddl(conn)
        with conn.transaction():
            execute_file(conn, DML_DIR / "refresh_quarantine.sql", params)
            _write_audit(conn, batch_id, window)
    return batch_id


def _params(window: DateWindow, batch_id: uuid.UUID) -> dict:
    return {
        "start": window.start_date,
        "end": window.end_date,
        "batch_id": str(batch_id),
    }


def _write_audit(conn: Connection, batch_id: uuid.UUID, window: DateWindow) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                count(*) AS rows_read,
                count(*) FILTER (
                    WHERE id IN (SELECT source_price_id FROM dq.quarantine_prices)
                ) AS rows_quarantined
            FROM raw.prices
            WHERE loading_date BETWEEN %s AND %s
            """,
            (window.start_date, window.end_date),
        )
        rows_read, rows_quarantined = cursor.fetchone()
        rows_accepted = rows_read - rows_quarantined
        cursor.execute(
            """
            INSERT INTO dq.batch_audit (
                batch_id, window_start, window_end, started_at,
                rows_read, rows_quarantined, rows_accepted
            )
            VALUES (%s, %s, %s, now(), %s, %s, %s)
            ON CONFLICT (batch_id) DO UPDATE
            SET rows_read = EXCLUDED.rows_read,
                rows_quarantined = EXCLUDED.rows_quarantined,
                rows_accepted = EXCLUDED.rows_accepted
            """,
            (
                batch_id,
                window.start_date,
                window.end_date,
                rows_read,
                rows_quarantined,
                rows_accepted,
            ),
        )
    logger.info(
        "dq window %s..%s read=%s quarantined=%s accepted=%s",
        window.start_date,
        window.end_date,
        rows_read,
        rows_quarantined,
        rows_accepted,
    )
