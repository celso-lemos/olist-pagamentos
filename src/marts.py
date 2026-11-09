"""Gera indicadores de parcelamento, combinacoes e evolucao mensal."""

import duckdb

from ingest import DATABASE, ROOT


def build_marts(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    connection.execute("BEGIN TRANSACTION")
    try:
        connection.execute((ROOT / "sql" / "marts.sql").read_text(encoding="utf-8"))
        checks = {
            "base de cartao por faixa": """
                SELECT coalesce(sum(credit_card_orders), 0) =
                (SELECT count(*) FROM refined.order_payments WHERE has_credit_card)
                FROM marts.installments_by_value""",
            "pedidos pagos por combinacao": """
                SELECT coalesce(sum(order_count), 0) =
                (SELECT count(*) FROM refined.order_payments WHERE has_payment)
                FROM marts.payment_combinations""",
            "pedidos por mes": """
                SELECT coalesce(sum(order_count), 0) =
                (SELECT count(*) FROM refined.order_payments)
                FROM marts.monthly_payments""",
            "total pago por mes": """
                SELECT coalesce(sum(total_payment_value), 0) =
                (SELECT coalesce(sum(total_payment_value), 0)
                 FROM refined.order_payments) FROM marts.monthly_payments""",
            "parcelamentos por faixa": """
                SELECT coalesce(sum(installment_orders), 0) =
                (SELECT count(*) FROM refined.order_payments WHERE is_installment)
                FROM marts.installments_by_value""",
            "taxas validas": """
                SELECT count(*) = 0 FROM (
                    SELECT installment_rate_pct AS rate FROM marts.installments_by_value
                    UNION ALL
                    SELECT installment_rate_pct FROM marts.monthly_payments
                ) WHERE rate < 0 OR rate > 100""",
        }
        for label, query in checks.items():
            if not connection.execute(query).fetchone()[0]:
                raise ValueError(f"Validacao falhou: {label}")
        counts = {
            table: connection.execute(f"SELECT count(*) FROM marts.{table}").fetchone()[0]
            for table in ("installments_by_value", "payment_combinations", "monthly_payments")
        }
        connection.execute("COMMIT")
        return counts
    except Exception:
        connection.execute("ROLLBACK")
        raise


if __name__ == "__main__":
    if not DATABASE.is_file():
        raise FileNotFoundError("Execute primeiro a ingestao e a camada refined.")
    with duckdb.connect(str(DATABASE)) as connection:
        for table, count in build_marts(connection).items():
            print(f"marts.{table}: {count} linhas")
