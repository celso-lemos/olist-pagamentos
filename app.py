"""Dashboard: apresenta indicadores prontos da camada marts, sem agrega-los."""

import json

import altair as alt
import pandas as pd
import streamlit as st

from dashboard_data import load_data


st.set_page_config(page_title="Olist | Pagamentos", page_icon=":material/payments:", layout="wide")
st.caption("OLIST / ANÁLISE DE PAGAMENTOS")
st.title("Como os pedidos são pagos?")
st.write("Explore parcelamento, combinações de pagamento e sua evolução no tempo.")

try:
    snapshot = load_data()
except (OSError, ValueError):
    st.error("Os indicadores não estão disponíveis. Gere a exportação do pipeline.")
    st.stop()

with st.sidebar:
    st.header("Sobre a análise")
    st.write("Pedidos da Olist entre 2016 e 2018. Todos os status são incluídos, inclusive cancelados.")
    st.markdown("**Parcelado:** pedido com pelo menos um pagamento em cartão de crédito com duas ou mais parcelas.")
    st.markdown("**Base da taxa:** pedidos com cartão de crédito.")
    st.caption("O total pago reúne todos os meios do pedido e não representa o valor de uma parcela.")
    st.link_button("Fonte dos dados · Olist", snapshot["source_url"], icon=":material/open_in_new:")
    st.markdown(f"Dados e análises: [{snapshot['license']}]({snapshot['license_url']}). Uso educacional não comercial.")

view = st.segmented_control(
    "Indicador", ["Parcelamento por valor", "Meios de pagamento", "Evolução mensal"],
    default="Parcelamento por valor", required=True, key="view",
)

if view == "Parcelamento por valor":
    frame = pd.DataFrame(snapshot["tables"]["installments_by_value"])
    st.subheader("Pedidos de maior valor são mais parcelados?")
    st.caption("Faixas do total pago por pedido. Cada taxa considera somente os pedidos com cartão daquela faixa.")
    with st.container(horizontal=True):
        for row in frame.to_dict("records"):
            st.metric(row["value_band"], f"{row['installment_rate_pct']:.2f}%".replace(".", ","), border=True)
    chart = alt.Chart(frame).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X("installment_rate_pct:Q", title="Pedidos parcelados (%)", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("value_band:N", title=None, sort=frame["value_band"].tolist()),
        tooltip=[alt.Tooltip("value_band:N", title="Total pago"),
                 alt.Tooltip("installment_rate_pct:Q", title="Taxa (%)", format=".2f"),
                 alt.Tooltip("credit_card_orders:Q", title="Pedidos com cartão", format=","),
                 alt.Tooltip("installment_orders:Q", title="Parcelados", format=",")],
    ).properties(height=280)
    st.altair_chart(chart, width="stretch", alt="Taxa de parcelamento por faixa do total pago")
    st.info("A comparação é descritiva: uma associação entre valor e parcelamento não demonstra causalidade.")
    details = frame.drop(columns=["band_order", "avg_order_payment"]).rename(columns={
        "value_band": "Faixa do total pago", "credit_card_orders": "Pedidos com cartão",
        "installment_orders": "Pedidos parcelados", "installment_rate_pct": "Taxa (%)",
    })
elif view == "Meios de pagamento":
    frame = pd.DataFrame(snapshot["tables"]["payment_combinations"])
    st.subheader("Quais meios aparecem juntos no pedido?")
    st.caption("Participação entre todos os pedidos com pagamento. Cada pedido pertence a uma única combinação.")
    chart = alt.Chart(frame).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X("order_count:Q", title="Pedidos"),
        y=alt.Y("payment_methods:N", title=None, sort=frame["payment_methods"].tolist()),
        tooltip=[alt.Tooltip("payment_methods:N", title="Meios"),
                 alt.Tooltip("order_count:Q", title="Pedidos", format=","),
                 alt.Tooltip("share_of_paid_orders_pct:Q", title="Participação (%)", format=".2f")],
    ).properties(height=340)
    st.altair_chart(chart, width="stretch", alt="Quantidade de pedidos por combinação de meios de pagamento")
    st.caption("credit_card = crédito · debit_card = débito · boleto = boleto · voucher = vale · not_defined = não definido na fonte.")
    details = frame[["payment_methods", "order_count", "share_of_paid_orders_pct"]].rename(columns={
        "payment_methods": "Meios de pagamento", "order_count": "Pedidos",
        "share_of_paid_orders_pct": "Participação (%)",
    })
else:
    frame = pd.DataFrame(snapshot["tables"]["monthly_payments"])
    frame["purchase_month"] = pd.to_datetime(frame["purchase_month"])
    st.subheader("Como o parcelamento varia ao longo do tempo?")
    st.caption("Mês da compra · taxa calculada entre os pedidos com cartão de cada mês.")
    chart = alt.Chart(frame).mark_line(point=True).encode(
        x=alt.X("purchase_month:T", title="Mês da compra"),
        y=alt.Y("installment_rate_pct:Q", title="Parcelamento (%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=[alt.Tooltip("purchase_month:T", title="Mês", format="%m/%Y"),
                 alt.Tooltip("installment_rate_pct:Q", title="Taxa (%)", format=".2f"),
                 alt.Tooltip("credit_card_orders:Q", title="Pedidos com cartão", format=",")],
    ).properties(height=340)
    st.altair_chart(chart, width="stretch", alt="Evolução mensal da taxa de parcelamento")
    st.warning("Os meses inicial e final podem ser incompletos. Meses com poucos pedidos são mais sensíveis a variações; sem cartão, a taxa é nula. Meses sem pedidos não têm observação.")
    details = frame[["purchase_month", "order_count", "credit_card_orders", "installment_orders", "installment_rate_pct"]].rename(columns={
        "purchase_month": "Mês da compra", "order_count": "Pedidos",
        "credit_card_orders": "Pedidos com cartão", "installment_orders": "Parcelados",
        "installment_rate_pct": "Taxa (%)",
    })

st.subheader("Confira os números")
st.dataframe(details, hide_index=True, width="stretch", alt="Valores do indicador selecionado")
st.download_button("Baixar indicadores publicados", data=json.dumps(snapshot, ensure_ascii=False, indent=2),
                   file_name="olist-indicadores.json", mime="application/json", icon=":material/download:")
st.caption("Projeto educacional · Desafio final da Aula 4 · Indicadores calculados no SQL e apresentados sem recálculo.")
