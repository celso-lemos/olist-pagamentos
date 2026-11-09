CREATE SCHEMA IF NOT EXISTS refined;

CREATE OR REPLACE TABLE refined.orders AS
SELECT order_id, customer_id, order_status,
       CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
       CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
       CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
       CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
       CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date
FROM raw.orders;

CREATE OR REPLACE TABLE refined.payments AS
SELECT order_id,
       CAST(payment_sequential AS INTEGER) AS payment_sequential,
       payment_type,
       CAST(payment_installments AS INTEGER) AS payment_installments,
       CAST(payment_value AS DECIMAL(18, 2)) AS payment_value
FROM raw.order_payments;

-- Agregar antes do JOIN evita multiplicar pedidos com varios pagamentos.
CREATE OR REPLACE TABLE refined.order_payments AS
WITH payments_by_order AS (
    SELECT order_id,
           count(*) AS payment_count,
           sum(payment_value) AS total_payment_value,
           count(DISTINCT payment_type) AS payment_method_count,
           string_agg(DISTINCT payment_type, ' + ' ORDER BY payment_type)
               AS payment_methods,
           bool_or(payment_type = 'credit_card') AS has_credit_card,
           bool_or(payment_type = 'credit_card' AND payment_installments >= 2)
               AS is_installment,
           max(CASE WHEN payment_type = 'credit_card'
                    THEN payment_installments END) AS max_credit_card_installments
    FROM refined.payments
    GROUP BY order_id
)
SELECT o.*,
       coalesce(p.payment_count, 0) AS payment_count,
       p.total_payment_value,
       coalesce(p.payment_method_count, 0) AS payment_method_count,
       p.payment_methods,
       coalesce(p.has_credit_card, false) AS has_credit_card,
       coalesce(p.is_installment, false) AS is_installment,
       p.max_credit_card_installments,
       p.order_id IS NOT NULL AS has_payment
FROM refined.orders o
LEFT JOIN payments_by_order p USING (order_id);
