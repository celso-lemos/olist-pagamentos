"""Testes independentes dos CSVs e do banco local."""

from pathlib import Path
import sys
import unittest
from decimal import Decimal

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from refine import build_refined


class RefinedTests(unittest.TestCase):
    def setUp(self):
        self.connection = duckdb.connect()
        self.addCleanup(self.connection.close)
        self.connection.execute("""
            CREATE SCHEMA raw;
            CREATE TABLE raw.orders AS
            SELECT id AS order_id, 'customer' AS customer_id,
                   'delivered' AS order_status,
                   '2020-01-01 12:00:00' AS order_purchase_timestamp,
                   NULL::VARCHAR AS order_approved_at,
                   NULL::VARCHAR AS order_delivered_carrier_date,
                   NULL::VARCHAR AS order_delivered_customer_date,
                   '2020-01-10' AS order_estimated_delivery_date
            FROM (VALUES ('a'), ('b'), ('c'), ('d')) t(id);
            CREATE TABLE raw.order_payments (
                order_id VARCHAR, payment_sequential VARCHAR,
                payment_type VARCHAR, payment_installments VARCHAR,
                payment_value VARCHAR
            );
            INSERT INTO raw.order_payments VALUES
                ('a', '1', 'credit_card', '3', '100.10'),
                ('a', '2', 'voucher', '1', '20.20'),
                ('b', '1', 'credit_card', '1', '50.00'),
                ('d', '1', 'voucher', '4', '10.00');
        """)

    def test_business_rules_and_repeatability(self):
        expected = {'orders': 4, 'payments': 4, 'order_payments': 4}
        self.assertEqual(build_refined(self.connection), expected)
        self.assertEqual(build_refined(self.connection), expected)
        rows = self.connection.execute("""
            SELECT order_id, total_payment_value, has_credit_card,
                   is_installment, has_payment, payment_methods
            FROM refined.order_payments ORDER BY order_id
        """).fetchall()
        self.assertEqual(rows, [
            ('a', Decimal('120.30'), True, True, True, 'credit_card + voucher'),
            ('b', Decimal('50.00'), True, False, True, 'credit_card'),
            ('c', None, False, False, False, None),
            ('d', Decimal('10.00'), False, False, True, 'voucher'),
        ])

    def test_invalid_amount_rolls_back_previous_tables(self):
        build_refined(self.connection)
        self.connection.execute("UPDATE raw.order_payments SET payment_value = '-1'")
        with self.assertRaisesRegex(ValueError, 'pagamento invalido'):
            build_refined(self.connection)
        self.assertEqual(self.connection.execute(
            'SELECT sum(payment_value) FROM refined.payments'
        ).fetchone()[0], Decimal('180.30'))

    def test_orphan_payment_is_rejected(self):
        self.connection.execute("""
            INSERT INTO raw.order_payments VALUES ('missing','1','boleto','1','5')
        """)
        with self.assertRaisesRegex(ValueError, 'sem pedido'):
            build_refined(self.connection)


if __name__ == '__main__':
    unittest.main()
