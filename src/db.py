"""PostgreSQL connection helper used by all scripts and notebooks."""

import pandas as pd
from sqlalchemy import create_engine, text  # text re-exported for callers

# Local socket connection — no password needed for local dev
DB_URL = "postgresql:///telecom_churn"


def get_engine():
    return create_engine(DB_URL)


def query(sql, **params):
    """Run a SQL query and return a DataFrame."""
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)
