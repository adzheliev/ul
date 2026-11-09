"""Command line for the tariff pipeline.

Airflow tasks call the same subcommands. ``run-all`` is the compose bootstrap.
"""

import argparse
import logging
from datetime import date

from etl.config import DateWindow, get_settings
from etl.log import configure_logging
from etl.publish import publish_predictions, publish_route_card
from etl.scoring import score_window
from etl.transform import dbt_build
from etl.validate import validate_core
from etl.warehouse import load_raw, refresh_quarantine

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and run one pipeline command."""

    configure_logging()
    parser = argparse.ArgumentParser(prog="etl")
    parser.add_argument("--start-date", help="Inclusive loading-date window start (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Inclusive loading-date window end (YYYY-MM-DD)")
    parser.add_argument(
        "command",
        choices=(
            "run-all",
            "load-raw",
            "quarantine",
            "dbt",
            "validate",
            "publish-mart",
            "score",
            "publish-predictions",
        ),
    )
    args = parser.parse_args(argv)
    settings = get_settings()
    window = _window(args.start_date, args.end_date, settings.window)
    if args.command == "run-all":
        run_all(settings, window)
    elif args.command == "load-raw":
        load_raw(settings, window)
    elif args.command == "quarantine":
        refresh_quarantine(settings, window)
    elif args.command == "dbt":
        dbt_build(settings)
    elif args.command == "validate":
        validate_core(settings)
    elif args.command == "publish-mart":
        publish_route_card(settings)
    elif args.command == "score":
        score_window(settings, window)
    elif args.command == "publish-predictions":
        publish_predictions(settings)


def run_all(settings, window: DateWindow) -> None:
    """Execute the warehouse path and the batch score in order."""

    load_raw(settings, window)
    refresh_quarantine(settings, window)
    dbt_build(settings)
    validate_core(settings)
    publish_route_card(settings)
    score_window(settings, window)
    publish_predictions(settings)
    logger.info("pipeline finished for %s..%s", window.start_date, window.end_date)


def _window(start: str | None, end: str | None, default: DateWindow) -> DateWindow:
    return DateWindow(
        start_date=date.fromisoformat(start) if start else default.start_date,
        end_date=date.fromisoformat(end) if end else default.end_date,
    )


if __name__ == "__main__":
    main()
