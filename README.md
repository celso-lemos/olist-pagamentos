# Olist — Parcelamento e formas de pagamento

Projeto desenvolvido para o desafio final da Aula 4.

**[Abrir o dashboard público](https://olist-pagamentos-axm698tegwcqo9xwpxzkly.streamlit.app/)**

Painel hospedado no Streamlit Community Cloud, com indicadores agregados
de parcelamento e formas de pagamento.

## Pergunta do projeto

Pedidos de maior valor são parcelados com mais frequência entre as compras
que usaram cartão de crédito? Quais combinações de meios de pagamento são
mais comuns?

## Fonte dos dados

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Licença dos dados: CC BY-NC-SA 4.0, conforme indicada no Kaggle.

Créditos: Olist, publicadora do Brazilian E-Commerce Public Dataset no Kaggle.
Este projeto tem finalidade educacional e não comercial. A licença permite
compartilhamento e adaptação com atribuição, indicação das alterações e
compartilhamento de adaptações sob a mesma licença:
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Os CSVs não são redistribuídos neste repositório. As análises derivadas aqui
apresentadas são disponibilizadas sob CC BY-NC-SA 4.0. As transformações
realizadas são conversão de tipos, consolidação e agregação de indicadores;
os arquivos originais permanecem inalterados.

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

Testes executados com `pytest`, usando dados fictícios e um DuckDB em memória,
sem abrir o banco do projeto nem ler os CSVs. Os casos usam `unittest.TestCase`,
formato coletado e executado pelo pytest. Instale as dependências de testes:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

## Preparação e execução completa

Requer Python (ambiente validado com Python 3.13.13) e os dois CSVs em
`data/raw/`. Na raiz do projeto, no PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe src/pipeline.py
.\.venv\Scripts\python.exe -m pytest -v
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
sql/marts/            Um arquivo SQL por indicador
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
.\.venv\Scripts\python.exe -m pytest -v
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
.\.venv\Scripts\python.exe -m pytest -v
```

Cada indicador tem seu arquivo em `sql/marts/`. As tabelas são recriadas em uma transação:

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

## Diferenças em relação ao curso

Referência: [Aula 1](https://ckoliveiraa.github.io/pipeline-olist/aula-1.html),
[Aula 2](https://ckoliveiraa.github.io/pipeline-olist/aula-2.html),
[Aula 3](https://ckoliveiraa.github.io/pipeline-olist/aula-3.html) e
[Aula 4](https://ckoliveiraa.github.io/pipeline-olist/aula-4.html).

O curso trabalha vendas por mês, categorias, entrega, avaliações, recompra
e outros indicadores. Seu `mix_pagamento` mede participação do valor por
tipo de pagamento em pedidos válidos. Este projeto usa dois arquivos para
investigar parcelamento e combinações de meios no nível do pedido:

| Indicador próprio | Pergunta | SQL |
| --- | --- | --- |
| Parcelamento por faixa | Entre pedidos com cartão, como a taxa varia com o total pago? | `sql/marts/01_installments_by_value.sql` |
| Combinações | Quais conjuntos de meios ocorrem no mesmo pedido e em quantos pedidos pagos? | `sql/marts/02_payment_combinations.sql` |
| Evolução mensal | Como varia a taxa de parcelamento entre pedidos com cartão ao longo dos meses de compra? | `sql/marts/03_monthly_payments.sql` |

A transformação específica reúne todos os pagamentos por pedido, identifica
cartão parcelado e ordena os meios distintos antes de juntar aos pedidos.
Mantém todos os status e sinaliza pedidos sem pagamento. O total pago não
é chamado de receita de produtos e inclui todos os meios do pedido.

## Dados publicados para o dashboard

O pipeline também executa `src/export_marts.py`, gerando
`data/published/dashboard.json`. Esse arquivo é versionado e contém somente
as três tabelas agregadas da camada marts, sem pedidos ou clientes individuais.
O banco, o ambiente virtual e os CSVs originais continuam fora do Git.
Os indicadores derivados são publicados sob CC BY-NC-SA 4.0, com fonte e
licença incluídas no próprio arquivo. Valores monetários são exportados como
texto decimal para preservar os centavos; datas usam o formato ISO.

Para atualizar apenas a exportação após gerar os marts:

```powershell
.\.venv\Scripts\python.exe src/export_marts.py
```

A exportação usa um snapshot das três tabelas. O arquivo final só é
substituído após a leitura e serialização completas. Não há cálculos de
indicadores nessa etapa, somente leitura ordenada e serialização.
## Dashboard em Streamlit

O painel lê somente `data/published/dashboard.json`, exportado da camada
marts. Não abre o banco nem lê os CSVs originais. Não calcula taxas, somas ou
médias: apenas apresenta os indicadores prontos. A navegação troca entre
parcelamento por valor, combinações de pagamento e evolução mensal.
Gráficos têm tooltips; tabelas permitem conferir os valores; o arquivo de
indicadores pode ser baixado pelo painel.

Para abrir localmente, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço informado no terminal (normalmente `http://localhost:8501`).
Use `Ctrl+C` no terminal para encerrar. O painel funciona com o arquivo
agregado versionado, mesmo sem os dados originais e sem executar o pipeline.
Os testes de interface usam dados fictícios e `streamlit.testing.v1.AppTest`.
### Publicar no Streamlit Community Cloud

Com os commits enviados ao GitHub, entre em
[share.streamlit.io](https://share.streamlit.io/) com a conta pessoal vinculada
ao GitHub. Em **Create app**, escolha a opção de usar um repositório existente:

- Repository: `celso-lemos/olist-pagamentos`
- Branch: `main`
- Main file path: `app.py`
- Advanced settings: Python `3.13` (versão principal/secundária validada localmente).

O serviço instala o `requirements.txt` da raiz. Não são necessários secrets,
CSVs originais ou banco DuckDB: os indicadores já estão em
`data/published/dashboard.json`. Confirme a disponibilidade do nome do
subdomínio na plataforma antes de divulgar um endereço.

Após **Deploy**, confira as três visões e o download do JSON. Caso haja erro,
consulte o log da instalação/execução antes de alterar dependências.
O endereço público informado após a implantação está no início deste README.
Mudanças futuras no código ou nos indicadores precisam de commit e push
para atualizar a versão hospedada. As instruções seguem a
[documentação de implantação](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Uso da IA e conferência

- **Testes:** a IA adotou `unittest` embora o desafio exigisse `pytest`.
  A diferença foi identificada ao comparar a implementação com o enunciado
  fornecido pelo aluno. Foram adicionadas dependências de desenvolvimento e
  configuração; os quatro testes passaram executados por `pytest`, com dados
  inventados e DuckDB em memória, sem abrir o banco local.
- **Contagem na ingestão:** a primeira conferência automatizada da IA falhou
  porque assumiu que a primeira linha física do CSV de pedidos era o cabeçalho.
  Havia uma linha vazia inicial. A inspeção mostrou o problema; a conferência
  passou a ignorar linhas vazias antes de identificar o cabeçalho. As contagens
  de registros coincidiram com a carga: 99.441 pedidos e 103.886 pagamentos.
  O CSV original não foi editado.
- **Transformação:** as conferências executadas pela IA mantiveram 99.441
  pedidos antes e depois do JOIN e preservaram a soma dos pagamentos. Um pedido
  sem pagamento foi mantido com total nulo; não foi descartado nem tratado
  como compra gratuita. O aluno acompanhou os resultados informados no chat;
  isso não equivale a uma auditoria independente de todas as regras.
- **Decisões e histórico:** a IA definiu faixas de valor e inclusão de todos
  os status; essas escolhas estão documentadas e foram apresentadas ao aluno.
  Também concentrou a implementação em um commit, contrariando o histórico
  por etapa pedido no desafio. A limitação foi identificada na revisão dos
  requisitos com `git log`; o histórico original foi preservado, sem simular
  uma construção por etapas que não ficou registrada.
