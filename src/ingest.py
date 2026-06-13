"""
Split the IBM Telco CSV into 3 source tables in PostgreSQL.

This version handles the richer IBM dataset (33 columns) which includes
Churn Score, CLTV, Churn Reason, and geographic columns.

Column names are normalised to snake_case on the way in.

Run:  python src/ingest.py
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from db import get_engine, text

RAW_CSV = Path(__file__).parent.parent / "data" / "raw" / "Telco_customer_churn.csv"

# Rename messy IBM column names → clean snake_case
RENAME = {
    "CustomerID":        "customer_id",
    "Gender":            "gender",
    "Senior Citizen":    "senior_citizen",
    "Partner":           "partner",
    "Dependents":        "dependents",
    "Tenure Months":     "tenure",
    "City":              "city",
    "State":             "state",
    "Zip Code":          "zip_code",
    "Phone Service":     "phone_service",
    "Multiple Lines":    "multiple_lines",
    "Internet Service":  "internet_service",
    "Online Security":   "online_security",
    "Online Backup":     "online_backup",
    "Device Protection": "device_protection",
    "Tech Support":      "tech_support",
    "Streaming TV":      "streaming_tv",
    "Streaming Movies":  "streaming_movies",
    "Contract":          "contract",
    "Paperless Billing": "paperless_billing",
    "Payment Method":    "payment_method",
    "Monthly Charges":   "monthly_charges",
    "Total Charges":     "total_charges",
    "Churn Label":       "churn",
    "Churn Value":       "churn_value",
    "Churn Score":       "churn_score",
    "CLTV":              "cltv",
    "Churn Reason":      "churn_reason",
}

CRM_COLS     = ["customer_id", "gender", "senior_citizen", "partner",
                "dependents", "tenure", "city", "state", "zip_code"]
SERVICE_COLS = ["customer_id", "phone_service", "multiple_lines", "internet_service",
                "online_security", "online_backup", "device_protection",
                "tech_support", "streaming_tv", "streaming_movies"]
BILLING_COLS = ["customer_id", "contract", "paperless_billing", "payment_method",
                "monthly_charges", "total_charges", "churn", "churn_value",
                "churn_score", "cltv", "churn_reason"]


def load():
    print("Reading CSV...")
    df = pd.read_csv(RAW_CSV)
    df = df.rename(columns=RENAME)

    # Total Charges has blank strings for new customers — convert and fill
    df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")
    df["total_charges"] = df["total_charges"].fillna(df["total_charges"].median())

    engine = get_engine()

    # Truncate in reverse FK order (cdr → billing → services → crm)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE raw.cdr, raw.billing, raw.services, raw.crm CASCADE"))

    df[CRM_COLS].to_sql("crm", engine, schema="raw", if_exists="append", index=False)
    print(f"  raw.crm      → {len(df):,} rows")

    df[SERVICE_COLS].to_sql("services", engine, schema="raw", if_exists="append", index=False)
    print(f"  raw.services → {len(df):,} rows")

    df[BILLING_COLS].to_sql("billing", engine, schema="raw", if_exists="append", index=False)
    print(f"  raw.billing  → {len(df):,} rows")

    print("\nDone. 3 source tables loaded into PostgreSQL raw schema.")


if __name__ == "__main__":
    load()
