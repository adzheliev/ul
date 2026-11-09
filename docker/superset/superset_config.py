"""Superset metadata lives in Postgres, not in a container-local sqlite file."""

import os

SQLALCHEMY_DATABASE_URI = os.environ["SUPERSET_METADATA_URI"]
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "local-demo-secret")
PREVENT_UNSAFE_DB_CONNECTIONS = False
WTF_CSRF_ENABLED = True
