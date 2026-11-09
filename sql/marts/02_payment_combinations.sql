CREATE OR REPLACE TABLE marts.payment_combinations AS
SELECT payment_methods, payment_method_count, count(*) AS order_count,
       sum(total_payment_value) AS total_payment_value,
       100.0 * count(*) / sum(count(*)) OVER () AS share_of_paid_orders_pct
FROM refined.order_payments
WHERE has_payment
GROUP BY payment_methods, payment_method_count;
