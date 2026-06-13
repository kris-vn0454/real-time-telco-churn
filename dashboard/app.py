"""
Telecom Churn Analytics Dashboard — Streamlit
Reads live from PostgreSQL analytics.customer_360 view.
Run: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from db import query

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="Telecom Churn Analytics",
    page_icon="📡",
    layout="wide",
)

sns.set_theme(style="whitegrid")

# ── Data loading ────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    return query("SELECT * FROM analytics.customer_360")

@st.cache_resource
def load_model():
    model_path = Path(__file__).parent.parent / "data" / "processed" / "best_model.joblib"
    if model_path.exists():
        return joblib.load(model_path)
    return None

@st.cache_data(ttl=300)
def load_probabilities():
    prob_path = Path(__file__).parent.parent / "data" / "processed" / "churn_probabilities.csv"
    if prob_path.exists():
        return pd.read_csv(prob_path)["0"].values
    return None

df   = load_data()
proba = load_probabilities()

# ── Header ──────────────────────────────────────────────────
st.title("📡 Telecom Churn Analytics Platform")
st.caption("Data sourced from PostgreSQL · Customer 360 View · Updated in real-time")
st.divider()

# ── Sidebar filters ─────────────────────────────────────────
st.sidebar.header("Filters")
contract_filter = st.sidebar.multiselect(
    "Contract Type",
    options=df["contract"].unique().tolist(),
    default=df["contract"].unique().tolist(),
)
segment_filter = st.sidebar.multiselect(
    "Tenure Segment",
    options=["New", "Growing", "Loyal", "Champion"],
    default=["New", "Growing", "Loyal", "Champion"],
)
internet_filter = st.sidebar.multiselect(
    "Internet Service",
    options=df["internet_service"].unique().tolist(),
    default=df["internet_service"].unique().tolist(),
)

filtered = df[
    df["contract"].isin(contract_filter) &
    df["tenure_segment"].isin(segment_filter) &
    df["internet_service"].isin(internet_filter)
]

# ── KPI Cards ───────────────────────────────────────────────
total       = len(filtered)
churned     = (filtered["churn"] == "Yes").sum()
churn_rate  = churned / total if total > 0 else 0
revenue_risk = filtered[filtered["churn"] == "Yes"]["monthly_charges"].sum()
avg_cltv    = filtered["cltv"].mean()
high_complaints = (filtered["complaint_count"] > 0).sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Customers",      f"{total:,}")
k2.metric("Churned Customers",    f"{churned:,}")
k3.metric("Churn Rate",           f"{churn_rate:.1%}")
k4.metric("Monthly Revenue at Risk", f"${revenue_risk:,.0f}")
k5.metric("Avg Customer LTV",     f"${avg_cltv:,.0f}")

st.divider()

# ── Row 1: Contract & Tenure ────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Churn Rate by Contract Type")
    ct = (filtered.groupby("contract")["churn"]
                  .apply(lambda x: (x == "Yes").mean())
                  .reset_index()
                  .rename(columns={"churn": "churn_rate"})
                  .sort_values("churn_rate", ascending=False))

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#e74c3c", "#f39c12", "#2ecc71"][:len(ct)]
    bars = ax.bar(ct["contract"], ct["churn_rate"], color=colors, edgecolor="white")
    ax.set_ylabel("Churn Rate")
    ax.set_ylim(0, ct["churn_rate"].max() * 1.25)
    for bar, val in zip(bars, ct["churn_rate"]):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
                f"{val:.1%}", ha="center", fontweight="bold", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("Churn Rate by Tenure Segment")
    order = ["New", "Growing", "Loyal", "Champion"]
    ts = (filtered.groupby("tenure_segment")["churn"]
                  .apply(lambda x: (x == "Yes").mean())
                  .reindex(order)
                  .reset_index()
                  .rename(columns={"churn": "churn_rate"})
                  .dropna())

    fig, ax = plt.subplots(figsize=(6, 4))
    seg_colors = ["#e74c3c", "#f39c12", "#3498db", "#2ecc71"]
    bars = ax.bar(ts["tenure_segment"], ts["churn_rate"],
                  color=seg_colors[:len(ts)], edgecolor="white")
    ax.set_ylabel("Churn Rate")
    ax.set_ylim(0, ts["churn_rate"].max() * 1.25)
    for bar, val in zip(bars, ts["churn_rate"]):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
                f"{val:.1%}", ha="center", fontweight="bold", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ── Row 2: Internet & CDR ───────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Churn Rate by Internet Service")
    ic = (filtered.groupby("internet_service")["churn"]
                  .apply(lambda x: (x == "Yes").mean())
                  .reset_index()
                  .rename(columns={"churn": "churn_rate"})
                  .sort_values("churn_rate", ascending=True))

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(ic["internet_service"], ic["churn_rate"],
            color=["#2ecc71", "#f39c12", "#e74c3c"][:len(ic)], edgecolor="white")
    ax.set_xlabel("Churn Rate")
    for i, val in enumerate(ic["churn_rate"]):
        ax.text(val + 0.002, i, f"{val:.1%}", va="center", fontweight="bold", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col4:
    st.subheader("CDR Usage: Churned vs Retained")
    cdr_means = (filtered.groupby("churn")[["total_calls", "total_data_mb", "complaint_count"]]
                         .mean()
                         .T
                         .rename(columns={"No": "Retained", "Yes": "Churned"}))

    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(cdr_means))
    w = 0.35
    ax.bar(x - w/2, cdr_means["Retained"], width=w, label="Retained", color="#2ecc71", edgecolor="white")
    ax.bar(x + w/2, cdr_means["Churned"],  width=w, label="Churned",  color="#e74c3c", edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(["Total Calls", "Data MB", "Complaints"], fontsize=9)
    ax.legend()
    ax.set_title("Average CDR Metrics")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

st.divider()

# ── High Risk Customers Table ────────────────────────────────
st.subheader("🔴 High-Risk Customers")

if proba is not None and len(proba) == len(df):
    df_risk = df.copy()
    df_risk["churn_probability"] = proba
    df_risk = df_risk[
        df_risk["contract"].isin(contract_filter) &
        df_risk["tenure_segment"].isin(segment_filter) &
        df_risk["internet_service"].isin(internet_filter)
    ]
    high_risk = (df_risk[df_risk["churn"] == "No"]
                 .sort_values("churn_probability", ascending=False)
                 .head(20)[["customer_id", "contract", "internet_service",
                             "monthly_charges", "tenure", "num_services",
                             "complaint_count", "churn_probability"]])
    high_risk["churn_probability"] = high_risk["churn_probability"].map("{:.1%}".format)
    high_risk["monthly_charges"] = high_risk["monthly_charges"].map("${:.2f}".format)
    st.dataframe(high_risk, use_container_width=True)
    st.caption("Customers predicted as 'Retained' but with highest churn risk — ideal targets for retention offers")
else:
    st.info("Run the modeling notebook (03_modeling.ipynb) first to generate churn probabilities.")

st.divider()

# ── Churn Reasons ────────────────────────────────────────────
st.subheader("Top Churn Reasons")
reasons = (filtered[filtered["churn"] == "Yes"]["churn_reason"]
             .dropna()
             .value_counts()
             .head(8))

if len(reasons) > 0:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.barh(reasons.index[::-1], reasons.values[::-1], color="#e74c3c", edgecolor="white")
    ax.set_xlabel("Number of Customers")
    for i, val in enumerate(reasons.values[::-1]):
        ax.text(val + 1, i, str(val), va="center", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

st.caption("Built with PostgreSQL · scikit-learn · XGBoost · MLflow · Streamlit")
