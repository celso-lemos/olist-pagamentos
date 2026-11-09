CREATE OR REPLACE TABLE marts.installments_by_value AS
WITH classified AS (
    SELECT *,
        CASE WHEN total_payment_value <= 100 THEN 1
             WHEN total_payment_value <= 200 THEN 2
             WHEN total_payment_value <= 500 THEN 3
             ELSE 4 END AS band_order,
        CASE WHEN total_payment_value <= 100 THEN 'Ate R$ 100'
             WHEN total_payment_value <= 200 THEN 'Acima de R$ 100 ate R$ 200'
             WHEN total_payment_value <= 500 THEN 'Acima de R$ 200 ate R$ 500'
             ELSE 'Acima de R$ 500' END AS value_band
    FROM refined.order_payments
    WHERE has_credit_card
)
SELECT band_order, value_band, count(*) AS credit_card_orders,
       count(*) FILTER (WHERE is_installment) AS installment_orders,
       100.0 * count(*) FILTER (WHERE is_installment) / count(*)
           AS installment_rate_pct,
       avg(total_payment_value) AS avg_order_payment
FROM classified
GROUP BY band_order, value_band;
