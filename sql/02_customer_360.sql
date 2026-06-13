-- =============================================================
-- Customer 360 View
-- Joins all 4 source tables into one unified analytical dataset.
-- Analysts query this view — never the raw tables directly.
-- =============================================================

CREATE OR REPLACE VIEW analytics.customer_360 AS
SELECT
    -- Identity
    c.customer_id,

    -- CRM: demographics
    c.gender,
    c.senior_citizen,
    c.partner,
    c.dependents,
    c.tenure,
    c.city,
    c.state,

    -- Services
    s.phone_service,
    s.multiple_lines,
    s.internet_service,
    s.online_security,
    s.online_backup,
    s.device_protection,
    s.tech_support,
    s.streaming_tv,
    s.streaming_movies,

    -- Billing
    b.contract,
    b.paperless_billing,
    b.payment_method,
    b.monthly_charges,
    b.total_charges,
    b.churn,
    b.churn_value,
    b.churn_score,
    b.cltv,
    b.churn_reason,

    -- CDR aggregates: usage behaviour from network events
    COUNT(CASE WHEN cdr.event_type = 'call'      THEN 1 END)  AS total_calls,
    COUNT(CASE WHEN cdr.event_type = 'sms'       THEN 1 END)  AS total_sms,
    COUNT(CASE WHEN cdr.event_type = 'data'      THEN 1 END)  AS total_data_sessions,
    COUNT(CASE WHEN cdr.event_type = 'complaint' THEN 1 END)  AS complaint_count,

    COALESCE(SUM(CASE WHEN cdr.event_type = 'call' THEN cdr.duration_mins END), 0) AS total_call_mins,
    COALESCE(SUM(CASE WHEN cdr.event_type = 'data' THEN cdr.data_mb      END), 0) AS total_data_mb,

    ROUND(
        COALESCE(SUM(CASE WHEN cdr.event_type = 'call' THEN cdr.duration_mins END), 0)
        / NULLIF(c.tenure, 0), 2
    ) AS avg_monthly_call_mins,

    ROUND(
        COALESCE(SUM(CASE WHEN cdr.event_type = 'data' THEN cdr.data_mb END), 0)
        / NULLIF(c.tenure, 0), 2
    ) AS avg_monthly_data_mb,

    -- Derived segments (computed in SQL, reused by all consumers)
    CASE
        WHEN c.tenure <= 12 THEN 'New'
        WHEN c.tenure <= 36 THEN 'Growing'
        WHEN c.tenure <= 60 THEN 'Loyal'
        ELSE 'Champion'
    END AS tenure_segment,

    (
        (CASE WHEN s.online_security   = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN s.online_backup     = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN s.device_protection = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN s.tech_support      = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN s.streaming_tv      = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN s.streaming_movies  = 'Yes' THEN 1 ELSE 0 END)
    ) AS num_services,

    CASE
        WHEN b.contract = 'Month-to-month' AND b.monthly_charges > 70 THEN 1
        ELSE 0
    END AS revenue_at_risk

FROM raw.crm c
JOIN raw.services s USING (customer_id)
JOIN raw.billing  b USING (customer_id)
LEFT JOIN raw.cdr cdr ON cdr.customer_id = c.customer_id

GROUP BY
    c.customer_id, c.gender, c.senior_citizen, c.partner, c.dependents,
    c.tenure, c.city, c.state,
    s.phone_service, s.multiple_lines, s.internet_service, s.online_security,
    s.online_backup, s.device_protection, s.tech_support, s.streaming_tv, s.streaming_movies,
    b.contract, b.paperless_billing, b.payment_method, b.monthly_charges, b.total_charges,
    b.churn, b.churn_value, b.churn_score, b.cltv, b.churn_reason;
