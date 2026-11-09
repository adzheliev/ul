"""Thresholds from the assignment, kept in one place.

SQL in ``sql/dml/refresh_quarantine.sql`` and the dbt category macro repeat
these values. ``tests/unit/test_sql_contract.py`` checks that the SQL still
names every reason code defined here.
"""

from enum import StrEnum

RUB_CODE = "643"
USD_CODE = "840"
EUR_CODE = "978"
FOREIGN_CURRENCY_CODES = frozenset({USD_CODE, EUR_CODE})

# Source validation: a positive RUB price at or below this floor is rejected.
RUB_PRICE_SOURCE_MIN = 1000.0

# Unflagged hauls above this unit rate are peaks the two outlier flags missed.
# The synthetic clean maximum is about 1 016 RUB/km, so 2 000 leaves headroom.
UNFLAGGED_MAX_RUB_PER_KM = 2000.0

HIGH_MIN_TRIPS = 30
HIGH_MIN_CARRIERS = 5
HIGH_MAX_AGE_DAYS = 30
MEDIUM_MIN_TRIPS = 10

WEIGHT_LABELS = ("G20T", "FTL", "10T", "5T", "L5T", "OTH")
VOLUME_LABELS = ("FTL", "OTH")
BODY_GROUPS = ("Тент", "Рефрижератор", "Изотерм", "Борт", "Прочие", "Не указан")
RELIABILITY_LEVELS = ("HIGH", "MEDIUM", "LOW_DATA")


class ReasonCode(StrEnum):
    """Why a source price was written to the dead-letter table.

    A row can carry several codes. ``outlier_mark`` is intentionally absent:
    outliers stay in core and are filtered later by the mart and the trainer.
    """

    NON_POSITIVE_PRICE = "NON_POSITIVE_PRICE"
    RUB_PRICE_BELOW_SOURCE_MIN = "RUB_PRICE_BELOW_SOURCE_MIN"
    NON_POSITIVE_DISTANCE = "NON_POSITIVE_DISTANCE"
    NEGATIVE_WEIGHT = "NEGATIVE_WEIGHT"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    UNKNOWN_LOADING_CITY = "UNKNOWN_LOADING_CITY"
    UNKNOWN_UNLOADING_CITY = "UNKNOWN_UNLOADING_CITY"
    MISSING_FX_RATE = "MISSING_FX_RATE"
