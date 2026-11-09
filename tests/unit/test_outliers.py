"""Oracle for the extra MarkOutlierPrices flag."""

import pandas as pd

from etl.quality.outliers import mark_recomputed_outliers


def test_km_tails_are_marked_only_inside_a_large_enough_group():
    frame = pd.DataFrame(
        [
            _row(1, 10, 10, 100),
            _row(2, 10, 20, 100),
            _row(3, 10, 30, 100),
            _row(4, 10, 40, 100),
            _row(5, 10, 1, 1, is_fact=False),
            _row(6, 10, 100000, 1, in_quarantine=True),
            _row(7, 20, 1000, 10),
            _row(8, 20, 1100, 10),
            _row(9, 20, 9000, 10),
        ]
    )
    marked = mark_recomputed_outliers(frame)
    assert marked.tolist() == [
        True,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
    ]


def test_equal_prices_in_a_group_of_four_stay_inside_both_fences():
    frame = pd.DataFrame([_row(index, 7, 50, 100) for index in range(1, 5)])
    assert not mark_recomputed_outliers(frame).any()


def _row(price_id, group_id, price, distance, *, is_fact=True, in_quarantine=False):
    return {
        "price_id": price_id,
        "price_group_id": group_id,
        "price": price,
        "distance": distance,
        "is_fact": is_fact,
        "in_quarantine": in_quarantine,
    }
