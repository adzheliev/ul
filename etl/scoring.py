"""Read observations, score them, and replace the prediction slice."""

import logging
import math
import uuid

import pandas as pd

from etl.config import DateWindow, Settings
from etl.db import connect
from ml.train import ModelScore, train_and_predict

logger = logging.getLogger(__name__)

OBSERVATION_SQL = "SELECT * FROM mart.ml_observation"

PREDICTION_COLUMNS = (
    "price_id",
    "loading_date",
    "loading_city_gcid",
    "unloading_city_gcid",
    "body_group",
    "actual_price_rub",
    "predicted_price_rub",
    "abs_error_rub",
    "ape_pct",
    "model_name",
    "scored_at",
)


def score_window(settings: Settings, window: DateWindow) -> list[ModelScore]:
    """Train on the fixed split and replace predictions whose loading date is in the window."""

    with connect(settings) as conn:
        observations = pd.read_sql_query(OBSERVATION_SQL, conn)
    scores = train_and_predict(observations, settings)
    _persist(settings, window, scores)
    return scores


def _persist(settings: Settings, window: DateWindow, scores: list[ModelScore]) -> None:
    with connect(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM mart.ml_price_predictions
                WHERE loading_date BETWEEN %s AND %s
                """,
                (window.start_date, window.end_date),
            )
            for score in scores:
                _copy_predictions(cursor, score.predictions, window)
                cursor.execute(
                    "DELETE FROM mart.ml_run WHERE model_name = %s",
                    (score.model_name,),
                )
                cursor.execute(
                    """
                    INSERT INTO mart.ml_run (
                        run_id, model_name, trained_at, r2, mape_pct, rmse, mae,
                        train_rows, test_rows, random_seed
                    )
                    VALUES (%s, %s, now(), %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid.uuid4(),
                        score.model_name,
                        score.metrics["r2"],
                        score.metrics["mape_pct"],
                        score.metrics["rmse"],
                        score.metrics["mae"],
                        score.train_rows,
                        score.test_rows,
                        settings.ml_seed,
                    ),
                )
        logger.info("stored predictions for %s model(s)", len(scores))


def _copy_predictions(cursor, frame: pd.DataFrame, window: DateWindow) -> None:
    scoped = frame[
        (frame["loading_date"] >= window.start_date) & (frame["loading_date"] <= window.end_date)
    ]
    if scoped.empty:
        return
    with cursor.copy(
        """
        COPY mart.ml_price_predictions (
            price_id, loading_date, loading_city_gcid, unloading_city_gcid, body_group,
            actual_price_rub, predicted_price_rub, abs_error_rub, ape_pct, model_name, scored_at
        ) FROM STDIN
        """
    ) as copy:
        for record in scoped.to_dict(orient="records"):
            values = [_null_if_nan(record[column]) for column in PREDICTION_COLUMNS]
            copy.write_row(values)


def _null_if_nan(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value
