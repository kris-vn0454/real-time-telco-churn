-- =============================================================
-- Schema: raw
-- Simulates 3 separate source systems feeding a data warehouse
--   raw.crm      → customer demographics  (from CRM system)
--   raw.services → service subscriptions  (from provisioning system)
--   raw.billing  → contract & charges     (from billing system)
--   raw.cdr      → call/data/sms events   (from network system)
-- =============================================================

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

-- -----------------------------------------------------------
-- CRM system: who the customer is
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.crm (
    customer_id     TEXT PRIMARY KEY,
    gender          TEXT,
    senior_citizen  TEXT,       -- Yes / No
    partner         TEXT,
    dependents      TEXT,
    tenure          INTEGER,
    city            TEXT,
    state           TEXT,
    zip_code        TEXT
);

-- -----------------------------------------------------------
-- Provisioning system: what services the customer subscribes to
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.services (
    customer_id       TEXT PRIMARY KEY REFERENCES raw.crm(customer_id),
    phone_service     TEXT,
    multiple_lines    TEXT,
    internet_service  TEXT,
    online_security   TEXT,
    online_backup     TEXT,
    device_protection TEXT,
    tech_support      TEXT,
    streaming_tv      TEXT,
    streaming_movies  TEXT
);

-- -----------------------------------------------------------
-- Billing system: contract, charges, churn outcome
-- Extra columns from IBM dataset: churn_score, cltv, churn_reason
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.billing (
    customer_id       TEXT PRIMARY KEY REFERENCES raw.crm(customer_id),
    contract          TEXT,
    paperless_billing TEXT,
    payment_method    TEXT,
    monthly_charges   NUMERIC(8,2),
    total_charges     NUMERIC(10,2),
    churn             TEXT,           -- Yes / No
    churn_value       INTEGER,        -- 1 / 0  (numeric version of churn)
    churn_score       INTEGER,        -- 0-100 predicted churn score from IBM
    cltv              INTEGER,        -- Customer Lifetime Value
    churn_reason      TEXT            -- Only populated for churned customers
);

-- -----------------------------------------------------------
-- Network system: one row per CDR event per customer
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.cdr (
    event_id        BIGINT PRIMARY KEY,
    customer_id     TEXT REFERENCES raw.crm(customer_id),
    event_date      TIMESTAMP,
    event_type      TEXT,        -- 'call', 'data', 'sms', 'complaint'
    duration_mins   NUMERIC(8,2),
    data_mb         NUMERIC(10,2),
    call_type       TEXT         -- 'local', 'international', 'roaming', NULL for non-calls
);

CREATE INDEX IF NOT EXISTS idx_cdr_customer   ON raw.cdr(customer_id);
CREATE INDEX IF NOT EXISTS idx_cdr_event_type ON raw.cdr(event_type);
CREATE INDEX IF NOT EXISTS idx_cdr_event_date ON raw.cdr(event_date);
