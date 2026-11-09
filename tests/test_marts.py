"""Confere denominadores e limites com dados sinteticos em memoria."""

from pathlib import Path
import sys
import unittest

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from marts import build_marts


class MartsTests(unittest.TestCase):
    def test_boundaries_denominators_and_repeatability(self):
        with duckdb.connect() as connection:
            connection.execute("""
                CREATE SCHEMA refined;
                CREATE TABLE refined.order_payments AS
                SELECT * FROM (VALUES
                    (TIMESTAMP '2020-01-01', 100.00, true, true, false, 'credit_card', 1),
                    (TIMESTAMP '2020-01-02', 100.01, true, true, true, 'credit_card', 1),
                    (TIMESTAMP '2020-01-03', 200.00, true, true, false, 'credit_card', 1),
                    (TIMESTAMP '2020-01-04', 200.01, true, true, true, 'credit_card + voucher', 2),
                    (TIMESTAMP '2020-01-05', 500.00, true, true, true, 'credit_card', 1),
                    (TIMESTAMP '2020-01-06', 500.01, true, true, true, 'credit_card', 1),
                    (TIMESTAMP '2020-02-01', 50.00, true, false, false, 'boleto', 1),
                    (TIMESTAMP '2020-02-02', NULL, false, false, false, NULL, 0)
                ) t(order_purchase_timestamp, total_payment_value, has_payment,
                    has_credit_card, is_installment, payment_methods, payment_method_count)
            """)
            expected = {'installments_by_value': 4, 'payment_combinations': 3,
                        'monthly_payments': 2}
            self.assertEqual(build_marts(connection), expected)
            self.assertEqual(build_marts(connection), expected)
            self.assertEqual(connection.execute('''
                SELECT credit_card_orders, installment_orders, installment_rate_pct
                FROM marts.installments_by_value ORDER BY band_order
            ''').fetchall(), [(1, 0, 0.0), (2, 1, 50.0), (2, 2, 100.0), (1, 1, 100.0)])
            monthly = connection.execute('''
                SELECT order_count, paid_orders, installment_rate_pct
                FROM marts.monthly_payments ORDER BY purchase_month
            ''').fetchall()
            self.assertAlmostEqual(monthly[0][2], 100 * 4 / 6)
            self.assertEqual(monthly[1], (2, 1, None))
            share = connection.execute('''
                SELECT share_of_paid_orders_pct FROM marts.payment_combinations
                WHERE payment_methods = 'credit_card + voucher'
            ''').fetchone()[0]
            self.assertAlmostEqual(share, 100 / 7)
