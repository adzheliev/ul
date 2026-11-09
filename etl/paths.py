"""Repository paths resolved from this file, not from the process cwd."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
DBT_DIR = ROOT / "dbt"
ARTIFACT_DIR = ROOT / "artifacts"
