"""Chronological cohorts for tariff scoring.

``as_of`` is the snapshot date from the assignment, not the wall clock.
Train is ``[as_of - 3 months, as_of - 3 weeks)``. Test is ``[as_of - 3 weeks, as_of]``.
The boundary day belongs only to test.
"""

from datetime import date
from typing import Literal

Cohort = Literal["history", "train", "test", "future"]

AS_OF = date(2026, 10, 26)
TRAIN_START = date(2026, 7, 26)
TEST_START = date(2026, 10, 5)


def cohort(loading_date: date, *, as_of: date = AS_OF) -> Cohort:
    """Classify a loading date relative to the fixed snapshot.

    Dates before the train window stay in ``history`` (they feed the mart,
    not the model). Dates after ``as_of`` are planned hauls.
    """

    if loading_date > as_of:
        return "future"
    if loading_date >= TEST_START:
        return "test"
    if loading_date >= TRAIN_START:
        return "train"
    return "history"
