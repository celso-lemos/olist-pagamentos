CREATE OR REPLACE TABLE marts.monthly_payments AS
SELECT CAST(date_trunc('month', order_purchase_timestamp) AS DATE) AS purchase_month,
       count(*) AS order_count,
       count(*) FILTER (WHERE has_payment) AS paid_orders,
       count(*) FILTER (WHERE has_credit_card) AS credit_card_orders,
       count(*) FILTER (WHERE is_installment) AS installment_orders,
       100.0 * count(*) FILTER (WHERE is_installment) /
           nullif(count(*) FILTER (WHERE has_credit_card), 0)
           AS installment_rate_pct,
       sum(total_payment_value) AS total_payment_value
FROM refined.order_payments
GROUP BY purchase_month;
