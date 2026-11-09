"""Airflow orchestration for the tariff batch.

Tasks shell out to ``python -m etl.cli`` so the DAG stays free of business
rules. The schedule is manual: compose bootstrap runs the same commands once,
and a trigger here replays a window idempotently.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

COMMANDS = (
    "load-raw",
    "quarantine",
    "dbt",
    "validate",
    "publish-mart",
    "score",
    "publish-predictions",
)

with DAG(
    dag_id="tariff_pipeline",
    description="Raw load, quarantine, dbt mart, ClickHouse publish, batch scoring",
    schedule=None,
    start_date=datetime(2026, 10, 26),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "smartlogistics",
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    params={
        "start_date": "2023-01-01",
        "end_date": "2027-12-31",
    },
    tags=["dwh", "tariffs"],
) as dag:
    previous = None
    for command in COMMANDS:
        task = BashOperator(
            task_id=command.replace("-", "_"),
            bash_command=(
                "cd /opt/airflow/project && /opt/venv/bin/python -m etl.cli "
                f"{command} "
                "--start-date {{ params.start_date }} "
                "--end-date {{ params.end_date }}"
            ),
        )
        if previous is not None:
            previous >> task
        previous = task
