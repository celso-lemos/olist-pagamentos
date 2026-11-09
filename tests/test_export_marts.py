"""A exportacao preserva valores e nunca publica registros individuais."""

import json
from pathlib import Path
import sys

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from export_marts import export_marts


def test_exporta_marts_sem_dados_individuais_e_sem_variar_na_reexecucao(tmp_path):
    output = tmp_path / 'published' / 'dashboard.json'
    with duckdb.connect() as connection:
        connection.execute("""
            CREATE SCHEMA marts;
            CREATE TABLE marts.installments_by_value AS
                SELECT 1 AS band_order, 50.0 AS installment_rate_pct;
            CREATE TABLE marts.payment_combinations AS
                SELECT 'credit_card' AS payment_methods, 2 AS order_count,
                       120.30::DECIMAL(18,2) AS total_payment_value;
            CREATE TABLE marts.monthly_payments AS
                SELECT DATE '2020-01-01' AS purchase_month;
        """)
        export_marts(connection, output)
        first = output.read_bytes()
        export_marts(connection, output)
        assert output.read_bytes() == first
    data = json.loads(first)
    assert data['tables']['payment_combinations'][0]['total_payment_value'] == '120.30'
    assert data['tables']['monthly_payments'][0]['purchase_month'] == '2020-01-01'
    assert len(data['tables']) == 3
    assert 'order_id' not in data['tables']['payment_combinations'][0]
    assert not output.with_suffix('.tmp').exists()


def test_falha_preserva_exportacao_anterior(tmp_path):
    output = tmp_path / 'dashboard.json'
    output.write_text('anterior', encoding='utf-8')
    with duckdb.connect() as connection:
        with pytest.raises(duckdb.Error):
            export_marts(connection, output)
    assert output.read_text(encoding='utf-8') == 'anterior'
