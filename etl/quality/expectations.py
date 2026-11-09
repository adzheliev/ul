"""Great Expectations gate for conformed prices.

Dirty source rows are expected and are routed to ``dq.quarantine_prices`` by SQL.
This suite runs on core, where the contract is strict: a failure stops publish.
"""

from dataclasses import dataclass

import great_expectations as gx
import pandas as pd
from great_expectations.expectations import (
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeInSet,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToEqual,
)

from etl.quality.spec import BODY_GROUPS, UNFLAGGED_MAX_RUB_PER_KM, VOLUME_LABELS, WEIGHT_LABELS

SUITE_NAME = "core.fact_price"


@dataclass(frozen=True)
class ExpectationOutcome:
    """Summary persisted in ``dq.expectation_result``."""

    suite_name: str
    success: bool
    evaluated: int
    unexpected: int


COMPLETE_COLUMNS = (
    "price_id",
    "price_rub",
    "distance",
    "currency_code",
    "weight_category",
    "volume_category",
    "body_group",
    "outlier_mark",
    "recomputed_outlier",
)


def validate_core_frame(
    frame: pd.DataFrame, *, expected_rows: int | None = None
) -> ExpectationOutcome:
    """Run the core suite against an in-memory frame.

    ``expected_rows`` is the batch completeness check: raw prices minus the
    distinct quarantined ids. Column checks cover nulls, duplicates, and peaks
    on hauls that neither outlier flag marked.
    """

    work = frame.copy()
    flagged = work["outlier_mark"].astype(bool) | work["recomputed_outlier"].astype(bool)
    per_km = work["price_rub"] / work["distance"].where(work["distance"].gt(0))
    work["price_per_km"] = per_km.mask(flagged)

    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas(name="core_pandas")
    asset = source.add_dataframe_asset(name="fact_price")
    batch = asset.add_batch_definition_whole_dataframe(name="whole")
    suite = gx.ExpectationSuite(name=SUITE_NAME)
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="price_id"))
    for column in COMPLETE_COLUMNS:
        suite.add_expectation(ExpectColumnValuesToNotBeNull(column=column))
    suite.add_expectation(
        ExpectColumnValuesToBeBetween(column="price_rub", min_value=0, strict_min=True)
    )
    suite.add_expectation(
        ExpectColumnValuesToBeBetween(column="distance", min_value=0, strict_min=True)
    )
    suite.add_expectation(ExpectColumnValuesToBeBetween(column="total_weight", min_value=0))
    suite.add_expectation(ExpectColumnValuesToBeBetween(column="total_volume", min_value=0))
    suite.add_expectation(
        ExpectColumnValuesToBeBetween(
            column="price_per_km",
            min_value=0,
            max_value=UNFLAGGED_MAX_RUB_PER_KM,
            strict_min=True,
        )
    )
    suite.add_expectation(
        ExpectColumnValuesToBeInSet(column="currency_code", value_set=["643", "840", "978"])
    )
    suite.add_expectation(
        ExpectColumnValuesToBeInSet(column="weight_category", value_set=list(WEIGHT_LABELS))
    )
    suite.add_expectation(
        ExpectColumnValuesToBeInSet(column="volume_category", value_set=list(VOLUME_LABELS))
    )
    suite.add_expectation(
        ExpectColumnValuesToBeInSet(column="body_group", value_set=list(BODY_GROUPS))
    )
    if expected_rows is not None:
        suite.add_expectation(ExpectTableRowCountToEqual(value=expected_rows))
    context.suites.add(suite)
    validation = gx.ValidationDefinition(name="core_fact_price", data=batch, suite=suite)
    context.validation_definitions.add(validation)
    result = validation.run(batch_parameters={"dataframe": work})
    stats = result.statistics or {}
    return ExpectationOutcome(
        suite_name=SUITE_NAME,
        success=bool(result.success),
        evaluated=int(stats.get("evaluated_expectations", 0)),
        unexpected=int(stats.get("unsuccessful_expectations", 0)),
    )
