FROM apache/superset:4.1.2

USER root
RUN pip install --no-cache-dir --retries 5 --timeout 180 \
    "clickhouse-connect[sqlalchemy]==0.8.18" \
    "psycopg2-binary==2.9.10"
USER superset
