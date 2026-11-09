"""Decision tree baseline fits on the train feature contract."""

import numpy as np
import pandas as pd

from etl.config import Settings
from ml.features import CATEGORY_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS
from ml.train import _fit_tree


def test_decision_tree_learns_train_rows_only():
    frame = pd.DataFrame({column: np.linspace(1, 40, 40) for column in NUMERIC_COLUMNS})
    for column in CATEGORY_COLUMNS:
        frame[column] = np.where(frame.index % 2 == 0, "А", "Б")
    target = frame["distance"].to_numpy() * 10
    model = _fit_tree(frame.loc[:, list(FEATURE_COLUMNS)], target, Settings())
    predicted = model.predict(frame.loc[:, list(FEATURE_COLUMNS)])
    assert predicted.shape == (40,)
    assert np.isfinite(predicted).all()
