"""Converte os tipos e consolida pagamentos sem perder pedidos."""

import duckdb

from ingest import DATABASE, ROOT


def build_refined(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Executa SQL e valida a camada dentro da mesma transacao."""
    connection.execute("BEGIN TRANSACTION")
    try:
        connection.execute((ROOT / "sql" / "refined.sql").read_text(encoding="utf-8"))
        checks = {
            "pedido com identificador nulo ou duplicado": """
                SELECT count(*) - count(DISTINCT order_id) FROM refined.orders""",
            "pagamento sem pedido correspondente": """
                SELECT count(*) FROM refined.payments
                ANTI JOIN refined.orders USING (order_id)""",
            "sequencia de pagamento nula ou duplicada": """
                SELECT count(*) FROM (
                    SELECT order_id, payment_sequential FROM refined.payments
                    GROUP BY 1, 2 HAVING count(*) > 1 OR payment_sequential IS NULL
                )""",
            "pagamento invalido": """
                SELECT count(*) FROM refined.payments
                WHERE payment_value IS NULL OR payment_value < 0
                   OR payment_installments IS NULL OR payment_installments < 0
                   OR payment_type IS NULL""",
            "quantidade de pedidos alterada": """
                SELECT abs((SELECT count(*) FROM refined.orders) -
                           (SELECT count(*) FROM refined.order_payments))""",
            "soma dos pagamentos alterada": """
                SELECT CASE WHEN
                    (SELECT coalesce(sum(payment_value), 0) FROM refined.payments) =
                    (SELECT coalesce(sum(total_payment_value), 0)
                     FROM refined.order_payments)
                THEN 0 ELSE 1 END""",
        }
        for label, query in checks.items():
            if connection.execute(query).fetchone()[0]:
                raise ValueError(f"Validacao falhou: {label}")
        counts = {
            table: connection.execute(f"SELECT count(*) FROM refined.{table}").fetchone()[0]
            for table in ("orders", "payments", "order_payments")
        }
        connection.execute("COMMIT")
        return counts
    except Exception:
        connection.execute("ROLLBACK")
        raise


if __name__ == "__main__":
    if not DATABASE.is_file():
        raise FileNotFoundError("Execute primeiro: python src/ingest.py")
    with duckdb.connect(str(DATABASE)) as connection:
        for table, count in build_refined(connection).items():
            print(f"refined.{table}: {count:,} linhas")
        print("Pedidos sem pagamento:", connection.execute(
            "SELECT count(*) FROM refined.order_payments WHERE NOT has_payment"
        ).fetchone()[0])
