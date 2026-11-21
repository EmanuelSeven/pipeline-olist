# Olist · Operação e Logística do E-commerce

Pipeline de dados do CSV ao dashboard sobre **99 mil pedidos reais** do e-commerce
brasileiro (2016–2018): ingestão, transformação com tipos e chaves conferidos,
indicadores em SQL, painel em Streamlit, relatório HTML e testes automatizados.

**Painel online:** https://olist-emmanuel.streamlit.app

Projeto construído no curso prático *Pipeline Olist em 4 aulas*, com
spec-driven development: cada etapa começa por uma spec escrita, com as
decisões e os motivos, e o código é conferido contra ela.

## Stack

Python 3.13 · [uv](https://docs.astral.sh/uv) · DuckDB · SQL · Streamlit · Plotly · pytest

## O dado

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
licença **CC BY-NC-SA 4.0** (uso não comercial, com atribuição). Nove arquivos
`.csv.gz` em `raw/`, 1.550.922 registros. Os arquivos de `raw/` nunca são editados.

| tabela | uma linha é... | chave |
|---|---|---|
| pedidos | um pedido | pedido_id |
| itens_pedido | um item de um pedido | (pedido_id, item_seq) |
| pagamentos | um pagamento de um pedido | (pedido_id, pagamento_seq) |
| avaliacoes | uma avaliação de um pedido | (avaliacao_id, pedido_id) |
| clientes | um cliente **por pedido** (a pessoa é `cliente_unico_id`) | cliente_id |
| vendedores | um vendedor | vendedor_id |
| produtos | um produto | produto_id |
| traducao_categorias | uma categoria | categoria |
| geolocalizacao | um ponto observado de um CEP (fica fora do pipeline — ver `specs/geolocalizacao.md`) | — |

## As três camadas

```
raw/*.csv.gz ──ingestao.py──▶ raw.*      espelho fiel do CSV, tudo texto
             ──transformacao.py──▶ refined.*  tipos certos, cópias removidas, nulos mantidos
             ──sql/marts/*.sql──▶ marts.*    uma tabela por pergunta de negócio
                                     │
                     app.py / relatorio.py  só leem marts — nenhum cálculo na tela
```

O banco inteiro é um arquivo, `olist.duckdb`, que **não vai para o git**: ele é
reconstruído do zero a partir de `raw/` em segundos. Toda etapa pode ser rodada
de novo sem quebrar (idempotente).

Specs com as decisões e os motivos: `SPEC-ingestao.md`, `specs/transformacao.md`
e `specs/geolocalizacao.md`. Cada arquivo de `sql/marts/` começa com a pergunta
e o grão do resultado.

## Os indicadores

| indicador | valor | mart |
|---|---|---|
| Ticket médio por pedido | R$ 137,42 | 11_kpis |
| Pedidos cancelados | 0,63% | 11_kpis |
| Peso do frete no que o cliente pagou | 14,2% | 11_kpis |
| Recompra (pessoas com 2+ pedidos) | 3,04% | 05_recompra |
| Entregas no prazo | 93,2% | 03_entrega_no_prazo |
| Dias da compra à entrega | 12,5 (mediana 10) | 11_kpis |
| Nota média | 4,09 | 11_kpis |

E mais: faturamento mensal (pico em nov/2017, Black Friday), receita por
categoria, mix de pagamento, ticket e tempo de entrega por UF, nota de quem
recebeu no prazo × atrasado (4,29 × 2,27) e concentração de vendedores
(540 de 3.053 fazem 80% da receita).

## Como rodar do zero

```bash
uv sync                                   # instala tudo na versão do uv.lock
uv run python -m pipeline.ingestao        # CSV -> raw      (1.550.922 registros)
uv run python -m pipeline.transformacao   # raw -> refined  (550.759 linhas)
uv run python -m pipeline.marts           # refined -> marts (13 marts)
uv run streamlit run app.py               # painel em http://localhost:8501
uv run python relatorio.py                # relatorio.html, abre com dois cliques
uv run pytest --cov                       # 37 testes, coverage mínimo de 60%
```

Sem o `olist.duckdb`, o próprio `app.py` roda as três etapas antes de abrir o
painel — é assim que ele funciona na Streamlit Cloud.

## Testes

37 testes unitários com pytest, todos sobre **dado inventado** (poucas linhas,
cada uma com o motivo de estar ali) e banco temporário — nenhum teste abre o
`olist.duckdb` nem lê `raw/`. Coverage de 97%. Exemplos do que provam:
pedido cancelado fica fora da receita; entrega às 15h do dia previsto está no
prazo; valor que não converte para o tipo encerra sem gravar nada; mart vazio
encerra e mantém o schema anterior.

## Onde a IA errou ou assumiu, e como descobri

A IA (Claude e Claude Code) entrou em todas as etapas, e o código das aulas 3 e 4
foi escrito por ela. Toda saída foi conferida contra números de referência,
quase sempre **contando linhas antes e depois**.

- **Contagem de nulos errada.** Ao testar a transformação, o Claude Code contou
  os nulos com `UNPIVOT`, que descarta os nulos antes de contar. Os números não
  batiam com a investigação manual (160 / 1.783 / 2.965); a contagem foi refeita
  com `count(*) - count(coluna)`.
- **Buraco na spec.** A IA encontrou 11 textos de avaliação só com espaços, que a
  spec não cobria. Ela parou e perguntou em vez de decidir; a decisão (ficam como
  vieram) virou uma linha nova na spec antes de virar código.
- **Ambiente.** O DuckDB 2.0 ainda não tinha a extensão do notebook (`ui`) e não
  havia DuckDB 1.5 para Python 3.15; o projeto foi fixado em Python 3.13 e DuckDB 1.5.
- **Painel com idiomas misturados.** A primeira versão mostrava meses, números e
  formas de pagamento em inglês. Corrigido só na formatação (nenhum número muda);
  a tradução das categorias foi para um mart próprio, `00_categorias_pt.sql`.
