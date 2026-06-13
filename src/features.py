"""
Feature engineering functions shared between notebooks and training pipeline.

Key decisions:
  - Binary Yes/No columns → 0/1 directly (no information lost)
  - Nominal columns (contract, payment_method, etc.) → OneHotEncoder
    NOT LabelEncoder — that would imply false ordering between categories
  - Numerical columns → StandardScaler fit on TRAIN data only
    Fitting on all data leaks test distribution into training
  - Derived features add domain signal beyond raw columns
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Yes/No columns mapped to 1/0
BINARY_COLS = [
    "gender",           # Female→1, Male→0
    "senior_citizen",
    "partner",
    "dependents",
    "phone_service",
    "paperless_billing",
]

# Nominal categories — no natural ordering → OneHotEncoder
NOMINAL_COLS = [
    "multiple_lines",
    "internet_service",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
    "contract",
    "payment_method",
]

# Numerical features (includes derived ones added below)
NUMERIC_COLS = [
    "tenure",
    "monthly_charges",
    "total_charges",
    "churn_score",
    "cltv",
    "num_services",
    "charge_per_month_ratio",
    "total_calls",
    "total_call_mins",
    "total_data_mb",
    "complaint_count",
]


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add domain-driven features on top of raw columns."""
    out = df.copy()

    # Tenure band: ordinal bucket — New, Growing, Loyal, Champion
    out["tenure_band"] = pd.cut(
        out["tenure"],
        bins=[0, 12, 36, 60, 72],
        labels=[0, 1, 2, 3],
        include_lowest=True,
    ).astype(int)

    # Add-on service count — more services = stickier customer
    addons = ["online_security", "online_backup", "device_protection",
              "tech_support", "streaming_tv", "streaming_movies"]
    out["num_services"] = (out[addons] == "Yes").sum(axis=1)

    # High monthly charge relative to total → customer is relatively new
    out["charge_per_month_ratio"] = out["monthly_charges"] / (out["total_charges"] + 1)

    # High-value month-to-month customers: most revenue at risk if they churn
    out["revenue_at_risk"] = (
        (out["contract"] == "Month-to-month") & (out["monthly_charges"] > 70)
    ).astype(int)

    return out


def encode_binary(df: pd.DataFrame) -> pd.DataFrame:
    """Map Yes/No and gender to 0/1 integers."""
    out = df.copy()
    for col in BINARY_COLS:
        if col not in out.columns:
            continue
        if col == "gender":
            out[col] = (out[col] == "Female").astype(int)
        else:
            out[col] = (out[col] == "Yes").astype(int)
    return out


def build_preprocessor() -> ColumnTransformer:
    """
    sklearn ColumnTransformer combining scaling + encoding.
    Call .fit() on training data only — never on the full dataset.
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_COLS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), NOMINAL_COLS),
        ],
        remainder="drop",
    )
