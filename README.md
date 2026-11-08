# Olist — Parcelamento e formas de pagamento

Projeto desenvolvido para o desafio final da Aula 4.

## Pergunta do projeto

Pedidos de maior valor são parcelados com mais frequência entre as compras
que usaram cartão de crédito? Quais combinações de meios de pagamento são
mais comuns?

## Fonte dos dados

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Licença dos dados: CC BY-NC-SA 4.0, conforme indicada no Kaggle.

Arquivos utilizados:
- `olist_orders_dataset.csv`
- `olist_order_payments_dataset.csv`

Baixe os arquivos da fonte e coloque-os em `data/raw/`.
A ligação entre os dois arquivos é feita pela coluna `order_id`.

## Camadas planejadas

- `raw` — carrega os CSVs preservando os dados de origem.
- `refined` — consolida os pagamentos em uma linha por pedido.
- `marts` — gera indicadores de parcelamento por faixa de valor, combinações
  de pagamento e evolução mensal.

## Regra principal

Um pedido é considerado parcelado quando tem pelo menos um pagamento
com cartão de crédito em duas ou mais parcelas. A taxa de parcelamento
usa como base os pedidos que tiveram pagamento com cartão de crédito.

## Validação planejada

Testes com `pytest` e dados fictícios, executados sem depender do banco
do projeto.