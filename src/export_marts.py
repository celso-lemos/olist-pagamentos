"""Exporta somente indicadores agregados para consumo pelo dashboard."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb

from ingest import DATABASE, ROOT


OUTPUT = ROOT / "data" / "published" / "dashboard.json"
QUERIES = {
    "installments_by_value":
        "SELECT * FROM marts.installments_by_value ORDER BY band_order",
    "payment_combinations":
        "SELECT * FROM marts.payment_combinations ORDER BY order_count DESC, payment_methods",
    "monthly_payments":
        "SELECT * FROM marts.monthly_payments ORDER BY purchase_month",
}


def serialize(value):
    if isinstance(value, Decimal):
        return str(value)  # Preserva centavos; a tela pode converter para exibicao.
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Tipo nao suportado: {type(value).__name__}")


def export_marts(connection: duckdb.DuckDBPyConnection, output: Path) -> None:
    payload = {
        "source": "Brazilian E-Commerce Public Dataset by Olist",
        "source_url": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
        "license": "CC BY-NC-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "scope": "Todos os status; indicadores agregados; mes da compra",
        "tables": {},
    }
    # Um snapshot consistente das tres tabelas, sem recalcular indicadores.
    connection.execute("BEGIN TRANSACTION")
    try:
        for table, query in QUERIES.items():
            result = connection.execute(query)
            columns = [column[0] for column in result.description]
            rows = result.fetchall()
            if not rows:
                raise ValueError(f"Mart vazio: {table}")
            payload["tables"][table] = [dict(zip(columns, row)) for row in rows]
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    content = json.dumps(payload, ensure_ascii=False, indent=2, default=serialize,
                         allow_nan=False) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(output)


if __name__ == "__main__":
    if not DATABASE.is_file():
        raise FileNotFoundError("Execute primeiro o pipeline.")
    with duckdb.connect(str(DATABASE), read_only=True) as connection:
        export_marts(connection, OUTPUT)
    print(f"Indicadores exportados: {OUTPUT}")
