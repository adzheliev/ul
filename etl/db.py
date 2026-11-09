"""Postgres connections for the ETL role."""

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg import Connection

from etl.config import Settings

logger = logging.getLogger(__name__)


@contextmanager
def connect(settings: Settings) -> Iterator[Connection]:
    """Open a connection that commits on success and rolls back on error.

    Compose marks Postgres healthy before the init process restarts the
    server, so the first attempts may be refused.
    """

    last_error: Exception | None = None
    connection: Connection | None = None
    for attempt in range(1, 31):
        try:
            connection = psycopg.connect(
                settings.postgres_dsn,
                application_name="smartlogistics-etl",
            )
            break
        except psycopg.OperationalError as exc:
            last_error = exc
            logger.warning("postgres is not ready, attempt %s/30", attempt)
            time.sleep(2)
    if connection is None:
        raise last_error or psycopg.OperationalError("postgres connection failed")
    with connection:
        yield connection
