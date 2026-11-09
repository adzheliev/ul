"""Train the tariff models and build a fact-versus-forecast frame.

CatBoost is the model we publish as primary. Ridge is a linear baseline.
DecisionTreeRegressor is the tree baseline from the R&D note. Imputing,
one-hot encoding and Ridge scaling are fit only on the train window.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

from etl.config import Settings
from etl.paths import ARTIFACT_DIR
from ml.contracts import FeatureSchema
from ml.features import CATEGORY_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS, build_features
from ml.metrics import regression_metrics
from ml.splits import cohort

logger = logging.getLogger(__name__)

TREE_MAX_DEPTH = 12
TREE_MIN_SAMPLES_LEAF = 50


@dataclass(frozen=True)
class ModelScore:
    """Holdout metrics and the rows to persist for one model."""

    model_name: str
    metrics: dict[str, float]
    train_rows: int
    test_rows: int
    predictions: pd.DataFrame


def train_and_predict(observations: pd.DataFrame, settings: Settings) -> list[ModelScore]:
    """Fit on the train cohort and score the test cohort plus future hauls."""

    frame = _prepare(observations, settings)
    trainable = frame[
        frame["is_fact"].astype(bool)
        & ~frame["outlier_mark"].astype(bool)
        & ~frame["recomputed_outlier"].astype(bool)
        & ~frame["complex"].astype(bool)
        & frame["distance"].gt(0)
        & frame["price_rub"].gt(0)
    ]
    train = trainable[trainable["cohort"] == "train"]
    test = trainable[trainable["cohort"] == "test"]
    future = frame[
        (frame["cohort"] == "future")
        & ~frame["complex"].astype(bool)
        & frame["distance"].gt(0)
        & frame["price_rub"].gt(0)
    ]
    if train.empty or test.empty:
        raise ValueError(
            f"time split produced train={len(train)} test={len(test)}; both cohorts need rows"
        )

    features_train = build_features(train)
    FeatureSchema.validate(features_train)
    target = train["price_rub"].to_numpy(dtype=float)
    catboost_model = _fit_catboost(features_train, target, settings)
    ridge_model = _fit_ridge(features_train, target, settings)
    tree_model = _fit_tree(features_train, target, settings)
    return [
        _score("catboost", catboost_model, test, future, len(train)),
        _score("ridge", ridge_model, test, future, len(train)),
        _score("decision_tree", tree_model, test, future, len(train)),
    ]


def _prepare(observations: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    frame = observations.copy()
    frame["loading_date"] = pd.to_datetime(frame["loading_date"]).dt.date
    frame["cohort"] = frame["loading_date"].map(lambda value: cohort(value, as_of=settings.as_of))
    return frame


def _fit_catboost(features: pd.DataFrame, target: np.ndarray, settings: Settings):
    from catboost import CatBoostRegressor, Pool

    model = CatBoostRegressor(
        loss_function="RMSE",
        random_seed=settings.ml_seed,
        iterations=400,
        depth=6,
        learning_rate=0.08,
        thread_count=settings.ml_thread_count,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(Pool(features, target, cat_features=list(CATEGORY_COLUMNS)))
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(ARTIFACT_DIR / "catboost_regressor.cbm")
    return model


def _fit_ridge(features: pd.DataFrame, target: np.ndarray, settings: Settings) -> Pipeline:
    model = Pipeline(
        [
            ("prepare", _encoded_columns(scale_numeric=True)),
            ("model", Ridge(alpha=1.0, random_state=settings.ml_seed)),
        ]
    )
    model.fit(features[list(FEATURE_COLUMNS)], target)
    return model


def _fit_tree(features: pd.DataFrame, target: np.ndarray, settings: Settings) -> Pipeline:
    """Tree baseline. Encoding is fit on train. Trees are not scaled."""

    model = Pipeline(
        [
            ("prepare", _encoded_columns(scale_numeric=False)),
            (
                "model",
                DecisionTreeRegressor(
                    max_depth=TREE_MAX_DEPTH,
                    min_samples_leaf=TREE_MIN_SAMPLES_LEAF,
                    random_state=settings.ml_seed,
                ),
            ),
        ]
    )
    model.fit(features[list(FEATURE_COLUMNS)], target)
    return model


def _encoded_columns(*, scale_numeric: bool) -> ColumnTransformer:
    numeric_steps: list = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline(numeric_steps), list(NUMERIC_COLUMNS)),
            (
                "category",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "one_hot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                list(CATEGORY_COLUMNS),
            ),
        ]
    )


def _score(
    model_name: str,
    model,
    test: pd.DataFrame,
    future: pd.DataFrame,
    train_rows: int,
) -> ModelScore:
    test_features = build_features(test)
    FeatureSchema.validate(test_features)
    test_pred = np.asarray(model.predict(test_features), dtype=float)
    metrics = regression_metrics(test["price_rub"].to_numpy(dtype=float), test_pred)
    logger.info(
        "model=%s r2=%.4f mape_pct=%.2f rmse=%.1f mae=%.1f train=%s test=%s",
        model_name,
        metrics["r2"],
        metrics["mape_pct"],
        metrics["rmse"],
        metrics["mae"],
        train_rows,
        len(test),
    )
    pieces = [_prediction_frame(test, test_pred, model_name, keep_actual=True)]
    if not future.empty:
        future_features = build_features(future)
        FeatureSchema.validate(future_features)
        future_pred = np.asarray(model.predict(future_features), dtype=float)
        pieces.append(_prediction_frame(future, future_pred, model_name, keep_actual=False))
    return ModelScore(
        model_name=model_name,
        metrics=metrics,
        train_rows=train_rows,
        test_rows=len(test),
        predictions=pd.concat(pieces, ignore_index=True),
    )


def _prediction_frame(
    source: pd.DataFrame,
    predicted: np.ndarray,
    model_name: str,
    *,
    keep_actual: bool,
) -> pd.DataFrame:
    actual = (
        source["price_rub"].to_numpy(dtype=float) if keep_actual else np.full(len(source), np.nan)
    )
    error = np.abs(actual - predicted) if keep_actual else np.full(len(source), np.nan)
    ape = error / actual * 100.0 if keep_actual else np.full(len(source), np.nan)
    scored_at = datetime.now(UTC)
    return pd.DataFrame(
        {
            "price_id": source["price_id"].to_numpy(),
            "loading_date": list(source["loading_date"]),
            "loading_city_gcid": source["loading_city_gcid"].to_numpy(),
            "unloading_city_gcid": source["unloading_city_gcid"].to_numpy(),
            "body_group": source["body_group"].to_numpy(),
            "actual_price_rub": actual,
            "predicted_price_rub": predicted,
            "abs_error_rub": error,
            "ape_pct": ape,
            "model_name": model_name,
            "scored_at": scored_at,
        }
    )
