# Telecom Churn Analytics Platform

An end-to-end customer churn prediction and analytics system built on PostgreSQL, scikit-learn / XGBoost, and Streamlit. It simulates a real telecom data pipeline — from raw CDR ingestion to an interactive churn dashboard with live ML scoring.

---

## Project Structure

```
telecom_churn/
├── data/
│   ├── raw/                  # Source CSV (IBM Telco dataset)
│   └── processed/            # Trained model & churn probability scores
├── notebooks/
│   ├── 01_eda.ipynb          # Exploratory data analysis
│   ├── 02_feature_engineering.ipynb
│   └── 03_modeling.ipynb     # Model training & evaluation
├── sql/
│   ├── 01_schema.sql         # PostgreSQL schema (raw → analytics)
│   └── 02_customer_360.sql   # Customer 360 aggregation view
├── src/
│   ├── db.py                 # Database connection helpers
│   ├── ingest.py             # Load IBM Telco CSV → PostgreSQL
│   ├── generate_cdr.py       # Synthetic CDR event generation
│   └── features.py           # Feature engineering pipeline
├── dashboard/
│   └── app.py                # Streamlit analytics dashboard
└── requirements.txt
```

---

## Architecture

```
IBM Telco CSV
     │
     ▼
src/ingest.py  ──────────────► raw.crm
                                raw.services       (PostgreSQL)
                                raw.billing
                                     │
src/generate_cdr.py ─────────► raw.cdr_events
                                     │
                                     ▼
                            sql/02_customer_360.sql
                                     │
                                     ▼
                          analytics.customer_360   (view)
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
                   notebooks/           dashboard/app.py
                   (ML training)        (Streamlit UI)
```

---

## Features

- **Data pipeline** — ingests the IBM Telco dataset into a PostgreSQL warehouse split across three source schemas (`raw.crm`, `raw.services`, `raw.billing`)
- **Synthetic CDR generation** — creates realistic call-detail records with usage patterns tied to contract type, tenure, and churn status
- **Customer 360 view** — SQL aggregation combining all sources into a single analytics-ready view
- **ML modeling** — XGBoost churn classifier with SHAP explainability, class imbalance handling (imbalanced-learn), and MLflow experiment tracking
- **Interactive dashboard** — Streamlit app with KPI cards, churn distribution charts, segment filters, and live model scoring

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up PostgreSQL

Create a database and run the schema scripts:

```bash
psql -U postgres -c "CREATE DATABASE telecom_churn;"
psql -U postgres -d telecom_churn -f sql/01_schema.sql
psql -U postgres -d telecom_churn -f sql/02_customer_360.sql
```

### 3. Configure database connection

Set the connection string in your environment (or update `src/db.py`):

```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/telecom_churn"
```

### 4. Ingest data

Download the [IBM Telco Customer Churn dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) and place it at `data/raw/Telco_customer_churn.csv`, then run:

```bash
python src/ingest.py
python src/generate_cdr.py
```

### 5. Train the model

Run the notebooks in order:

```
notebooks/01_eda.ipynb
notebooks/02_feature_engineering.ipynb
notebooks/03_modeling.ipynb
```

The trained model is saved to `data/processed/best_model.joblib`.

### 6. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data warehouse | PostgreSQL |
| Data manipulation | pandas, NumPy |
| ML | scikit-learn, XGBoost, imbalanced-learn |
| Explainability | SHAP |
| Experiment tracking | MLflow |
| Dashboard | Streamlit |
| Synthetic data | Faker |

---

## Dataset

[IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) — ~7,000 customers with demographic, service subscription, billing, and churn label columns.

---

## License

MIT
