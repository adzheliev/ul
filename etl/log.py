"""One logging setup for CLI and Airflow tasks."""

import logging


def configure_logging() -> None:
    """Configure a single stderr handler when the root logger is empty."""

    root = logging.getLogger()
    if root.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
