"""dbt build for core and mart models."""

import json
import logging
import os
import subprocess

from etl.config import Settings
from etl.paths import DBT_DIR

logger = logging.getLogger(__name__)


def dbt_build(settings: Settings) -> None:
    """Run ``dbt build`` so tests gate the mart before publish."""

    env = os.environ.copy()
    env.update(
        {
            "POSTGRES_HOST": settings.postgres_host,
            "POSTGRES_PORT": str(settings.postgres_port),
            "POSTGRES_DB": settings.postgres_db,
            "POSTGRES_USER": settings.postgres_user,
            "POSTGRES_PASSWORD": settings.postgres_password,
        }
    )
    command = [
        "dbt",
        "build",
        "--project-dir",
        str(DBT_DIR),
        "--profiles-dir",
        str(DBT_DIR),
        "--vars",
        json.dumps({"as_of": settings.as_of.isoformat()}),
    ]
    logger.info("dbt build as_of=%s", settings.as_of)
    subprocess.run(command, check=True, env=env, cwd=DBT_DIR)
