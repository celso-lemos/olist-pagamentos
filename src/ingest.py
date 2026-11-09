"""Carrega os CSVs originais na camada raw, sem conversoes de tipos."""

from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "olist.duckdb"
SOURCES = {
    "orders": "olist_orders_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
}


def ingest() -> dict[str, int]:
    """Substitui as tabelas raw em uma unica transacao, sem duplicar linhas."""
    paths = {name: ROOT / "data" / "raw" / filename
             for name, filename in SOURCES.items()}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(f"CSV nao encontrado: {path}")

    counts = {}
    with duckdb.connect(str(DATABASE)) as connection:
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
            for table, path in paths.items():
                # Nomes das tabelas sao constantes; caminhos usam parametros SQL.
                connection.execute(
                    f"CREATE OR REPLACE TABLE raw.{table} AS "
                    "SELECT * FROM read_csv(?, header = true, all_varchar = true)",
                    [str(path)],
                )
                counts[table] = connection.execute(
                    f"SELECT count(*) FROM raw.{table}"
                ).fetchone()[0]
                if counts[table] == 0:
                    raise ValueError(f"O CSV de {table} esta vazio.")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return counts


if __name__ == "__main__":
    for name, count in ingest().items():
        print(f"raw.{name}: {count:,} linhas")
    print(f"Banco: {DATABASE}")
