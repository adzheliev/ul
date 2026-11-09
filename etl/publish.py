"""Copy Postgres marts into ClickHouse serving tables."""

import logging

import clickhouse_connect
import pandas as pd

from etl.config import Settings
from etl.db import connect
from etl.paths import SQL_DIR
from etl.quality.pandera_models import RouteCardSchema

logger = logging.getLogger(__name__)

ROUTE_SQL = "SELECT * FROM mart.mart_route_card"
PREDICTION_SQL = "SELECT * FROM mart.ml_price_predictions"


def publish_route_card(settings: Settings) -> int:
    """Replace the ClickHouse corridor with the Postgres mart."""

    with connect(settings) as conn:
        frame = pd.read_sql_query(ROUTE_SQL, conn)
    if frame.empty:
        logger.info("route card is empty; clickhouse table truncated")
    else:
        RouteCardSchema.validate(frame)
    _replace_table(settings, "mart_route_card", _prepare_route(frame))
    logger.info("published route card rows=%s", len(frame))
    return len(frame)


def publish_predictions(settings: Settings) -> int:
    """Replace ClickHouse predictions with the Postgres scoring table."""

    with connect(settings) as conn:
        frame = pd.read_sql_query(PREDICTION_SQL, conn)
    _replace_table(settings, "ml_price_predictions", _prepare_predictions(frame))
    logger.info("published predictions rows=%s", len(frame))
    return len(frame)


def _client(settings: Settings):
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_db,
    )


def _replace_table(settings: Settings, table: str, frame: pd.DataFrame) -> None:
    client = _client(settings)
    ddl = (SQL_DIR / "clickhouse" / "10_mart.sql").read_text(encoding="utf-8")
    for statement in (part.strip() for part in ddl.split(";") if part.strip()):
        client.command(statement)
    client.command(f"TRUNCATE TABLE mart.{table}")
    if frame.empty:
        return
    client.insert_df(table, frame, database="mart")


def _prepare_route(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    prepared = frame.copy()
    prepared["price_month"] = pd.to_datetime(prepared["price_month"]).dt.date
    prepared["as_of"] = pd.to_datetime(prepared["as_of"]).dt.date
    for column in ("cv_rate", "mom_pct", "yoy_pct"):
        prepared[column] = prepared[column].astype(object).where(prepared[column].notna(), None)
    return prepared


def _prepare_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    prepared = frame.copy()
    prepared["loading_date"] = pd.to_datetime(prepared["loading_date"]).dt.date
    prepared["scored_at"] = pd.to_datetime(prepared["scored_at"], utc=True)
    for column in ("actual_price_rub", "abs_error_rub", "ape_pct"):
        prepared[column] = prepared[column].astype(object).where(prepared[column].notna(), None)
    return prepared
