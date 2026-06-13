"""
Generate synthetic CDR (Call Detail Records) for every customer.

In real telecom, CDR is event-level data from the network switch:
one row per call, data session, SMS, or complaint.
A company with 7,000 customers generates millions of these per month.

Logic:
  - Call volume scales with MonthlyCharges (high payers = more usage)
  - Data usage scales with InternetService type (Fiber > DSL > None)
  - Churned customers show declining activity in their last 2 months
  - Churned customers have a higher complaint rate

Run:  python src/generate_cdr.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from db import get_engine

BASE_DATE = datetime(2020, 1, 1)
CHUNK_SIZE = 50_000  # write to DB in batches to avoid memory issues


def _calls_per_month(monthly_charge):
    """Higher monthly charge → more call activity."""
    return max(5, int(monthly_charge / 6))


def _data_mb(internet_service, rng):
    if internet_service == "Fiber optic":
        return round(float(rng.lognormal(mean=3.8, sigma=0.8)), 2)   # ~45 MB avg
    elif internet_service == "DSL":
        return round(float(rng.lognormal(mean=2.6, sigma=0.7)), 2)   # ~13 MB avg
    return 0.0


def generate_for_customer(row, rng):
    customer_id    = row["customer_id"]
    tenure         = max(1, int(row["tenure"]))
    monthly_charge = float(row["monthly_charges"])
    internet       = row["internet_service"]
    churned        = row["churn"] == "Yes"

    calls_pm = _calls_per_month(monthly_charge)
    events   = []

    for month in range(tenure):
        month_start = BASE_DATE + timedelta(days=30 * month)

        # Declining activity signal for churned customers in last 2 months
        if churned and month >= tenure - 2:
            factor = 0.25
        else:
            factor = 1.0

        n_calls = rng.poisson(calls_pm * factor)
        n_sms   = rng.poisson(18 * factor)
        n_data  = rng.poisson(15 * factor) if internet != "No" else 0
        n_comp  = rng.poisson(0.8) if (churned and month >= tenure - 3) else rng.poisson(0.05)

        for _ in range(n_calls):
            day  = int(rng.integers(0, 30))
            hour = int(rng.integers(7, 23))
            events.append({
                "customer_id":  customer_id,
                "event_date":   month_start + timedelta(days=day, hours=hour),
                "event_type":   "call",
                "duration_mins": round(max(0.5, float(rng.normal(5.0, 3.0))), 2),
                "data_mb":      0.0,
                "call_type":    rng.choice(["local", "international", "roaming"],
                                           p=[0.85, 0.10, 0.05]),
            })

        for _ in range(n_sms):
            day = int(rng.integers(0, 30))
            events.append({
                "customer_id":  customer_id,
                "event_date":   month_start + timedelta(days=day),
                "event_type":   "sms",
                "duration_mins": 0.0,
                "data_mb":      0.0,
                "call_type":    None,
            })

        for _ in range(n_data):
            day = int(rng.integers(0, 30))
            events.append({
                "customer_id":  customer_id,
                "event_date":   month_start + timedelta(days=day),
                "event_type":   "data",
                "duration_mins": 0.0,
                "data_mb":      _data_mb(internet, rng),
                "call_type":    None,
            })

        for _ in range(n_comp):
            day = int(rng.integers(0, 30))
            events.append({
                "customer_id":  customer_id,
                "event_date":   month_start + timedelta(days=day),
                "event_type":   "complaint",
                "duration_mins": 0.0,
                "data_mb":      0.0,
                "call_type":    None,
            })

    return events


def generate_all(seed=42):
    engine = get_engine()

    # Load only the columns we need from PostgreSQL
    crm_df = pd.read_sql(
        "SELECT c.customer_id, c.tenure, b.monthly_charges, "
        "s.internet_service, b.churn "
        "FROM raw.crm c "
        "JOIN raw.services s USING (customer_id) "
        "JOIN raw.billing  b USING (customer_id)",
        engine
    )

    rng = np.random.default_rng(seed)
    all_events = []
    event_id   = 1

    print(f"Generating CDR for {len(crm_df):,} customers...")

    for _, row in crm_df.iterrows():
        events = generate_for_customer(row, rng)
        for e in events:
            e["event_id"] = event_id
            event_id += 1
        all_events.extend(events)

        # Write to DB in chunks to avoid loading millions of rows into RAM at once
        if len(all_events) >= CHUNK_SIZE:
            chunk = pd.DataFrame(all_events)
            chunk.to_sql("cdr", engine, schema="raw", if_exists="append", index=False,
                         method="multi", chunksize=5_000)
            print(f"  Written {event_id - 1:,} events so far...")
            all_events = []

    # Final flush
    if all_events:
        pd.DataFrame(all_events).to_sql(
            "cdr", engine, schema="raw", if_exists="append",
            index=False, method="multi", chunksize=5_000
        )

    print(f"\nDone. Total CDR events generated: {event_id - 1:,}")


if __name__ == "__main__":
    # Drop and recreate the CDR table before generating fresh data
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(__import__("sqlalchemy").text("TRUNCATE TABLE raw.cdr"))
    generate_all()
