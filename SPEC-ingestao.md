# SPEC — Etapa 1: Ingestão

Aula 1 · `pipeline/db.py` · `pipeline/ingestao.py`

Objetivo: copiar os 9 CSVs de `raw/` para o schema `raw` do `olist.duckdb`, **sem mudar nada**.

## 1. Tabelas (arquivo → tabela)

| arquivo em `raw/` | tabela |
|---|---|
| olist_customers_dataset.csv.gz | raw.clientes |
| olist_geolocation_dataset.csv.gz | raw.geolocalizacao |
| olist_orders_dataset.csv.gz | raw.pedidos |
| olist_order_items_dataset.csv.gz | raw.itens_pedido |
| olist_order_payments_dataset.csv.gz | raw.pagamentos |
| olist_order_reviews_dataset.csv.gz | raw.avaliacoes |
| olist_products_dataset.csv.gz | raw.produtos |
| olist_sellers_dataset.csv.gz | raw.vendedores |
| product_category_name_translation.csv.gz | raw.traducao_categorias |

Nomes de tabela traduzidos; nomes de coluna ficam os originais do CSV.

## 2. Proibido nesta etapa

- Nenhuma conversão de tipo.
- Nenhuma linha descartada (linha com erro de leitura derruba a execução, não é pulada).
- Nenhum nome de coluna alterado.
- Nunca escrever nada dentro da pasta `raw/`.

## 3. Rodar duas vezes

Cada tabela é **recriada do zero** (`CREATE OR REPLACE`). Rodar 1 ou 10 vezes dá o mesmo resultado.

## 4. Como o arquivo é lido

- Encoding declarado: `utf-8`.
- `.csv.gz` lido direto, sem descompactar.
- Primeira linha é cabeçalho.

## 5. Tipos

**Tudo entra como texto (VARCHAR).** A conversão é decisão da etapa 2.
Motivo: inferência de tipo destrói identificador com cara de número (CEP `01310` viraria `1310`).
Campo vazio no CSV continua nulo.

## 6. Saída na tela

Uma linha por tabela, com a contagem vinda do banco e milhar com ponto:

```
✓ raw.pedidos               99.441 linhas
```

E uma linha final com o total: `9 tabelas   1.550.922 registros`.

## 7. Quando der errado

Antes de ingerir qualquer coisa, confere se os 9 arquivos existem em `raw/`.
Se faltar algum: lista quais faltam e encerra com `sys.exit(1)`, sem criar nenhuma tabela.
Motivo: ingerir 8 de 9 em silêncio produz um dashboard errado que parece certo.

## Critérios de aceite

- As contagens batem com o anexo A1 da aula 1 (total 1.550.922 registros).
- `DESCRIBE raw.pedidos` mostra todas as colunas como `VARCHAR`.
- Rodar duas vezes seguidas imprime exatamente a mesma coisa.
- Renomear um arquivo de `raw/` faz a ingestão parar com o nome do arquivo que falta.
