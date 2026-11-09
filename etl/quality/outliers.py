"""Extra outlier mark in the style of MarkOutlierPrices.

This is not a quarantine reason and it does not replace ``outlier_mark``.
The market mart and the trainer drop a row when either flag is true.
``recomputed_outlier`` is never a model feature.

The population is accepted facts: not quarantined, ``is_fact``, a non-null
``price_group_id``, ``price > 0`` and ``distance > 0``. A group smaller than
four rows is left unmarked.

Fences are continuous percentiles of that group, including the row itself,
the same way a nightly group job reads the snapshot. They are not refit on
the train cohort.

* Tukey on raw ``price``: below ``Q1 - 1.5 * IQR`` or above ``Q3 + 1.5 * IQR``.
* Per-kilometre band on raw ``price / distance``: below P5 or above P95.

A row is marked when it falls outside either fence.
"""

from __future__ import annotations

import pandas as pd

MIN_GROUP_SIZE = 4
IQR_MULTIPLIER = 1.5


def mark_recomputed_outliers(frame: pd.DataFrame) -> pd.Series:
    """Return the extra outlier flag aligned to ``frame``.

    Args:
        frame: One row per price. Required columns are ``price_group_id``,
            ``price``, ``distance``, ``is_fact`` and ``in_quarantine``.

    Returns:
        A boolean series. Rows outside the eligible population are false.
    """

    eligible = (
        frame["is_fact"].astype(bool)
        & ~frame["in_quarantine"].astype(bool)
        & frame["price_group_id"].notna()
        & frame["price"].gt(0)
        & frame["distance"].gt(0)
    )
    marked = pd.Series(False, index=frame.index)
    if not eligible.any():
        return marked

    work = frame.loc[eligible, ["price_group_id", "price", "distance"]].copy()
    work["price_km"] = work["price"] / work["distance"]
    group_size = work.groupby("price_group_id")["price"].transform("size")
    sized = work.loc[group_size >= MIN_GROUP_SIZE]
    if sized.empty:
        return marked

    bounds = sized.groupby("price_group_id").agg(
        price_q1=("price", lambda values: values.quantile(0.25)),
        price_q3=("price", lambda values: values.quantile(0.75)),
        km_p5=("price_km", lambda values: values.quantile(0.05)),
        km_p95=("price_km", lambda values: values.quantile(0.95)),
    )
    iqr = bounds["price_q3"] - bounds["price_q1"]
    bounds["price_low"] = bounds["price_q1"] - IQR_MULTIPLIER * iqr
    bounds["price_high"] = bounds["price_q3"] + IQR_MULTIPLIER * iqr
    joined = sized.join(bounds, on="price_group_id")
    outside = (
        joined["price"].lt(joined["price_low"])
        | joined["price"].gt(joined["price_high"])
        | joined["price_km"].lt(joined["km_p5"])
        | joined["price_km"].gt(joined["km_p95"])
    )
    marked.loc[outside.index] = outside.to_numpy()
    return marked
