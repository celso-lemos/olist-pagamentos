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

## Camadas implementadas

- `raw` — carrega os CSVs preservando os dados de origem.
- `refined` — consolida os pagamentos em uma linha por pedido.
- `marts` — gera indicadores de parcelamento por faixa de valor, combinações
  de pagamento e evolução mensal.

## Regra principal

Um pedido é considerado parcelado quando tem pelo menos um pagamento
com cartão de crédito em duas ou mais parcelas. A taxa de parcelamento
usa como base os pedidos que tiveram pagamento com cartão de crédito.

## Validação

Testes com `unittest` e dados fictícios, executados sem depender do banco
do projeto. Usamos a biblioteca padrão do Python, sem dependência adicional.

## Preparação e execução completa

Requer Python (ambiente validado com Python 3.13.13) e os dois CSVs em
`data/raw/`. Na raiz do projeto, no PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/pipeline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Se a `.venv` já existir, pule sua criação. Não é necessário ativá-la ao usar
o caminho explícito do Python. O pipeline usa o mesmo interpretador nas três
etapas e interrompe a execução ao primeiro erro. Cada camada tem sua própria
transação; uma falha em refined ou marts não desfaz camadas anteriores já
confirmadas. Após corrigir a causa, execute o pipeline completo novamente.

Estrutura do código:

```text
requirements.txt       Versão do DuckDB
src/ingest.py          CSVs -> raw
src/refine.py          Executa e valida refined
src/marts.py           Executa e valida marts
src/pipeline.py        Executa as três etapas em ordem
sql/refined.sql       Conversões e consolidação por pedido
sql/marts.sql         Indicadores analíticos
tests/                Testes com dados fictícios em memória
```

O resultado local é `data/olist.duckdb`, que pode ser recriado a partir dos
CSVs e do código. Apenas código, testes, documentação e dependências devem
ser versionados; CSVs, banco e ambiente virtual ficam ignorados.

## Executar a ingestão

No terminal PowerShell, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/ingest.py
```

O script cria `data/olist.duckdb` com as tabelas `raw.orders` e
`raw.order_payments`. Todas as colunas são carregadas como texto; conversões
de datas e valores serão feitas na camada refined. Os CSVs não são alterados.
Executar novamente substitui as tabelas raw sem acumular linhas. A carga das
duas tabelas usa uma transação: se uma falhar, nenhuma alteração é confirmada.
O banco gerado e os CSVs ficam fora do Git.

## Executar a camada refined

Após a ingestão:

```powershell
.\.venv\Scripts\python.exe src/refine.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O SQL fica em `sql/refined.sql`; o Python executa a transformação e valida
os resultados na mesma transação. Conversões inválidas interrompem a carga.

- `refined.orders`: um registro por pedido, com datas convertidas.
- `refined.payments`: um registro por pagamento, com inteiros e valores em
  `DECIMAL(18,2)` para evitar aproximações de ponto flutuante.
- `refined.order_payments`: um registro por pedido, com total pago, combinação
  ordenada dos meios de pagamento e indicadores de cartão e parcelamento.

Um pedido sem pagamento é preservado com `has_payment = false` e total nulo.
Parcelamento considera somente cartão de crédito com duas ou mais parcelas.
O total pago representa todos os meios de pagamento do pedido; não é o valor
de cada parcela. Status dos pedidos são preservados, sem filtro nesta camada.
As validações conferem unicidade dos pedidos e sequências de pagamento,
vínculos, campos de pagamento obrigatórios, valores não negativos,
preservação da quantidade de pedidos e soma dos pagamentos.

## Executar os indicadores (marts)

Após a camada refined:

```powershell
.\.venv\Scripts\python.exe src/marts.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O SQL está em `sql/marts.sql`. As tabelas são recriadas em uma transação:

- `marts.installments_by_value`: quantidade de pedidos com cartão, quantidade
  parcelada e taxa percentual por faixa do total pago pelo pedido.
- `marts.payment_combinations`: combinações distintas de meios por pedido,
  quantidade de pedidos, total pago e participação entre pedidos com pagamento.
- `marts.monthly_payments`: pedidos, pedidos pagos, pedidos com cartão,
  parcelados, taxa e total pago, agrupados pelo mês da compra.

As faixas exploratórias são: até R$ 100 (inclusive), acima de R$ 100 até
R$ 200 (inclusive), acima de R$ 200 até R$ 500 (inclusive) e acima de R$ 500.
Elas usam o total de todos os pagamentos do pedido, inclusive em compras com
cartão combinado com outro meio. Não representam o valor de cada parcela.
A taxa é `100 * pedidos parcelados / pedidos com cartão`; meses sem cartão
têm taxa nula. As combinações usam pedidos pagos como denominador.
Todos os status são incluídos, inclusive cancelados e indisponíveis.
`not_defined` é preservado como categoria da fonte, sem reclassificação.
Os meses inicial e final do conjunto podem ser incompletos; não se deve
interpretar suas contagens como meses completos. Meses sem pedidos não geram
linhas. As taxas armazenadas não são arredondadas; arredonde para exibição.

### Resultados observados nos CSVs locais

| Total pago por pedido | Pedidos com cartão | Parcelados | Taxa |
| --- | ---: | ---: | ---: |
| Até R$ 100 | 34.859 | 17.452 | 50,06% |
| Acima de R$ 100 até R$ 200 | 25.111 | 19.260 | 76,70% |
| Acima de R$ 200 até R$ 500 | 13.000 | 11.213 | 86,25% |
| Acima de R$ 500 | 3.535 | 3.245 | 91,80% |

Nestas faixas, pedidos de maior valor têm maior frequência de parcelamento.
É uma associação descritiva, sem demonstração de causalidade e sem controle
por status, período ou perfil do comprador.

Dos 99.440 pedidos com pagamento, 74.259 usam somente cartão de crédito e
19.784 somente boleto. Entre os pedidos com mais de um meio, a combinação
mais frequente é cartão de crédito com voucher (2.245 pedidos); há também
um pedido com cartão de crédito e débito. A série contém 25 meses com pedidos,
de setembro de 2016 a outubro de 2018.
