"""O painel apresenta as taxas prontas, usando apenas dados inventados."""

from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import dashboard_data


def test_tres_visoes_exibem_indicadores_sem_recalcular(monkeypatch):
    # Taxa propositalmente diferente da divisao das contagens: a tela deve
    # exibir o valor publicado, e nunca substituir a regra vinda do mart.
    fake = {
        'source_url': 'https://example.com', 'license': 'CC BY-NC-SA 4.0',
        'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'tables': {
            'installments_by_value': [dict(band_order=1, value_band='Até R$ 100',
                credit_card_orders=10, installment_orders=5,
                installment_rate_pct=42.0, avg_order_payment=80)],
            'payment_combinations': [dict(payment_methods='credit_card',
                order_count=10, share_of_paid_orders_pct=100.0)],
            'monthly_payments': [dict(purchase_month='2020-01-01', order_count=12,
                credit_card_orders=10, installment_orders=5, installment_rate_pct=42.0)],
        },
    }
    monkeypatch.setattr(dashboard_data, 'load_data', lambda: fake)
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == '42,00%'
    app.segmented_control(key='view').set_value('Meios de pagamento').run()
    assert not app.exception
    assert app.dataframe[0].value.iloc[0]['Pedidos'] == 10
    app.segmented_control(key='view').set_value('Evolução mensal').run()
    assert not app.exception
    assert app.dataframe[0].value.iloc[0]['Taxa (%)'] == 42.0


def test_arquivo_ausente_exibe_erro_claro(monkeypatch):
    def missing():
        raise FileNotFoundError('sem arquivo')
    monkeypatch.setattr(dashboard_data, 'load_data', missing)
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
    assert not app.exception
    assert 'não estão disponíveis' in app.error[0].value
