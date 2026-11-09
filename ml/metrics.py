"""Holdout metrics for the tariff regressor.

Names match the research note: RMSE and MAE in rubles, MAPE in percent, R².
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Score a holdout where every actual price is strictly positive.

    MAPE divides by the actual price, so a zero target is a contract error
    rather than a number we quietly drop.
    """

    y_true = np.asarray(actual, dtype=float)
    y_pred = np.asarray(predicted, dtype=float)
    if y_true.size == 0:
        raise ValueError("metrics require at least one row")
    if np.any(y_true <= 0):
        raise ValueError("MAPE requires strictly positive actual prices")
    ape = np.abs(y_true - y_pred) / y_true * 100.0
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mape_pct": float(np.mean(ape)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
    }
