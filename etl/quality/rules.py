"""Pure DQ decisions.

These functions are the oracle for unit tests. The batch job applies the same
predicates in SQL so a 300k window is classified with joins, not row by row.
"""

from etl.quality.spec import RUB_CODE, RUB_PRICE_SOURCE_MIN, ReasonCode


def price_reason_codes(
    *,
    price: float,
    currency_code: str,
    distance: float,
    total_weight: float,
    total_volume: float,
    loading_city_known: bool,
    unloading_city_known: bool,
    fx_rate_found: bool,
) -> tuple[ReasonCode, ...]:
    """Return every DQ reason that applies to one price.

    A non-positive price is reported on its own. The RUB floor applies only to
    a strictly positive ruble amount, so zero is not tagged twice. The same
    city on both ends of a haul is not a reason: the source keeps those rows.

    Args:
        price: Freight amount in the source currency, without VAT.
        currency_code: Numeric ISO code stored by the source.
        distance: Planned distance in kilometres.
        total_weight: Cargo weight in tonnes.
        total_volume: Cargo volume in cubic metres.
        loading_city_known: Whether ``loading_city_gcid`` exists in ``cities``.
        unloading_city_known: Whether ``unloading_city_gcid`` exists in ``cities``.
        fx_rate_found: Whether ``exchange_rates`` has the exact ``nearest_rate_date``.
            Ignored for RUB.

    Returns:
        Reason codes in specification order. Empty when the row is accepted.
    """

    reasons: list[ReasonCode] = []
    if price <= 0:
        reasons.append(ReasonCode.NON_POSITIVE_PRICE)
    elif currency_code == RUB_CODE and price <= RUB_PRICE_SOURCE_MIN:
        reasons.append(ReasonCode.RUB_PRICE_BELOW_SOURCE_MIN)
    if distance <= 0:
        reasons.append(ReasonCode.NON_POSITIVE_DISTANCE)
    if total_weight < 0:
        reasons.append(ReasonCode.NEGATIVE_WEIGHT)
    if total_volume < 0:
        reasons.append(ReasonCode.NEGATIVE_VOLUME)
    if not loading_city_known:
        reasons.append(ReasonCode.UNKNOWN_LOADING_CITY)
    if not unloading_city_known:
        reasons.append(ReasonCode.UNKNOWN_UNLOADING_CITY)
    if currency_code != RUB_CODE and not fx_rate_found:
        reasons.append(ReasonCode.MISSING_FX_RATE)
    return tuple(reasons)
