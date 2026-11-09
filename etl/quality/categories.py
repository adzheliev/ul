"""Cargo category rules.

Runtime categories are filled in dbt with ``round(weight::numeric, 1)``, which
matches ``ROUND_HALF_UP`` below. Python is the documented oracle and the
fallback when a category arrives null in a dataframe test.
"""

from decimal import ROUND_HALF_UP, Decimal

from etl.quality.spec import WEIGHT_LABELS


def round_tonnes(weight: float) -> Decimal:
    """Round a tonne value to one decimal, half away from zero."""

    return Decimal(str(weight)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def weight_category(weight: float) -> str:
    """Map a tonne value to the platform weight band.

    Bands are closed on the left after rounding to 0.1 t: 30.0 is ``G20T``,
    10.0 is ``FTL``.
    """

    rounded = round_tonnes(weight)
    if rounded >= Decimal("30"):
        return "G20T"
    if rounded >= Decimal("10"):
        return "FTL"
    if rounded >= Decimal("5"):
        return "10T"
    if rounded >= Decimal("2.5"):
        return "5T"
    if rounded >= Decimal("0.5"):
        return "L5T"
    return "OTH"


def volume_category(volume: float) -> str:
    """Map cubic metres to ``FTL`` for ``(0, 120]`` and ``OTH`` otherwise."""

    if 0 < volume <= 120:
        return "FTL"
    return "OTH"


def fill_weight_category(current: str | None, weight: float) -> str:
    """Keep a source category and fill only a blank."""

    if current in WEIGHT_LABELS:
        return current
    return weight_category(weight)


def fill_volume_category(current: str | None, volume: float) -> str:
    """Keep a source category and fill only a blank."""

    if current in {"FTL", "OTH"}:
        return current
    return volume_category(volume)
