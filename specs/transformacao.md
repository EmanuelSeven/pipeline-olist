CONTEXTO
Estou construindo um pipeline de dados em Python sobre o dataset público da
Olist. Trabalho com spec-driven development: a spec abaixo é a fonte da
verdade e o código é consequência dela. Não acrescente requisito que não
esteja escrito aqui. Se algo estiver ambíguo, pergunte antes de escrever.

STACK
- Python 3.13, uv, DuckDB 1.5 (olist.duckdb na raiz do projeto)

O QUE JÁ EXISTE (use, não reimplemente)
pipeline/db.py: conectar(), criar_schema(con, nome)
O schema raw, com nove tabelas, todas as colunas VARCHAR.

ARTEFATO A PRODUZIR
pipeline/transformacao.py, executável com:
  uv run python -m pipeline.transformacao

SPEC

1. ESCOPO
   Lê de raw, escreve em refined. Nunca escreve em raw.
   Tabelas que entram: pedidos, itens_pedido, pagamentos, avaliacoes,
     clientes, vendedores, produtos, traducao_categorias (8).
   Tabelas que ficam de fora, e por quê: geolocalizacao — nenhum indicador
     do curso usa; é a tabela mais difícil e terá spec própria (desafio 2).

2. NOMES
   Renomear para português curto. Motivo: os SQLs das aulas 3 e 4 usam
   estes nomes. Corrige o erro de digitação de fábrica (lenght).
   Mapa coluna_original -> coluna_nova, tabela por tabela:
   pedidos:
     order_id -> pedido_id
     customer_id -> cliente_id
     order_status -> status
     order_purchase_timestamp -> data_compra
     order_approved_at -> data_aprovacao
     order_delivered_carrier_date -> data_envio
     order_delivered_customer_date -> data_entrega
     order_estimated_delivery_date -> data_entrega_prevista
   itens_pedido:
     order_id -> pedido_id
     order_item_id -> item_seq
     product_id -> produto_id
     seller_id -> vendedor_id
     shipping_limit_date -> data_limite_envio
     price -> preco
     freight_value -> frete
   pagamentos:
     order_id -> pedido_id
     payment_sequential -> pagamento_seq
     payment_type -> tipo
     payment_installments -> parcelas
     payment_value -> valor
   avaliacoes:
     review_id -> avaliacao_id
     order_id -> pedido_id
     review_score -> nota
     review_comment_title -> titulo
     review_comment_message -> comentario
     review_creation_date -> data_criacao
     review_answer_timestamp -> data_resposta
   clientes:
     customer_id -> cliente_id
     customer_unique_id -> cliente_unico_id
     customer_zip_code_prefix -> cep_prefixo
     customer_city -> cidade
     customer_state -> uf
   vendedores:
     seller_id -> vendedor_id
     seller_zip_code_prefix -> cep_prefixo
     seller_city -> cidade
     seller_state -> uf
   produtos:
     product_id -> produto_id
     product_category_name -> categoria
     product_name_lenght -> tamanho_nome
     product_description_lenght -> tamanho_descricao
     product_photos_qty -> qtd_fotos
     product_weight_g -> peso_g
     product_length_cm -> comprimento_cm
     product_height_cm -> altura_cm
     product_width_cm -> largura_cm
   traducao_categorias:
     product_category_name -> categoria
     product_category_name_english -> categoria_ingles

3. TIPOS
   Datas com hora:  TIMESTAMP  formato declarado: '%Y-%m-%d %H:%M:%S'
     (data_compra, data_aprovacao, data_envio, data_entrega,
      data_limite_envio, data_criacao, data_resposta)
     Motivo: a hora importa (tempo de entrega). Formato declarado, nunca inferido.
   Data sem hora:   DATE  (data_entrega_prevista)
     Motivo: vem sempre com 00:00:00 — a hora é falsa.
   Dinheiro:        DECIMAL(10,2)  (preco, frete, valor)
     Motivo: DOUBLE erra centavo (0.1 + 0.2 = 0.30000000000000004).
   Contagens:       INTEGER  (parcelas, nota, item_seq, pagamento_seq,
     tamanho_nome, tamanho_descricao, qtd_fotos, peso_g, comprimento_cm,
     altura_cm, largura_cm)
   Identificadores que parecem número (CEP, ids): VARCHAR
     Motivo: ninguém soma CEP; 23.995 clientes têm CEP com zero à esquerda.
   Demais textos (cidade, uf, status, tipo, categoria, categoria_ingles,
     titulo, comentario): VARCHAR.

4. CONVERSÃO QUE FALHA
   Para tudo. Antes de gravar, conta, coluna por coluna, os valores não nulos
   que não convertem. Se qualquer coluna tiver 1 falha ou mais: mostra
   "tabela.coluna: N valores não converteram" e sys.exit(1), sem gravar nada.
   Motivo: falha virando nulo se mistura com os nulos reais (2.965 pedidos
   sem entrega) e ninguém nunca mais separa os dois. Proibido TRY_CAST /
   errors="coerce" na gravação.

5. DUPLICATAS
   Chave de cada tabela:
     pedidos: pedido_id
     itens_pedido: (pedido_id, item_seq)
     pagamentos: (pedido_id, pagamento_seq)
     avaliacoes: (avaliacao_id, pedido_id)
     clientes: cliente_id
     vendedores: vendedor_id
     produtos: produto_id
     traducao_categorias: categoria
   Chave repetida com conteúdo idêntico: sai (fica uma cópia), e a quantidade
     removida aparece na tela.
   Chave repetida com conteúdo diferente: para tudo, mostra tabela, chave e
     quantas chaves em conflito, sys.exit(1). Motivo: escolher uma linha seria
     decidir no escuro qual é a verdadeira.

6. NULOS
   Regra geral: todo nulo continua nulo. Nenhuma linha apagada, nada preenchido.
   Exceções, coluna por coluna, com motivo: nenhuma.
     - datas de pedidos: nulo = pedido que não chegou ou foi cancelado (verdade).
       Os 8 pedidos delivered sem data de entrega ficam, como anomalia anotada.
     - categoria de produto (610): "sem_categoria", se precisar, é decisão do mart.
     - titulo/comentario de avaliação: o cliente não escreveu.
   Texto só com espaços em branco (11 valores: 2 títulos e 9 comentários):
     fica como veio, NÃO vira nulo. Motivo: é texto livre que nenhum indicador
     usa para conta; transformar mudaria a contagem de nulos sem ganho.
   Motivo: refined corrige o tipo do dado, não inventa dado.

7. SAÍDA NA TELA
   Por tabela: linhas que entraram -> linhas que saíram, duplicatas removidas,
   e "nulos mantidos" por coluna (só as que têm nulo). Linha final com o total.
     ✓ refined.pedidos          99.441 -> 99.441 linhas  (0 duplicatas)
         nulos mantidos: data_aprovacao 160, data_envio 1.783, data_entrega 2.965
   Milhar com ponto. stdout reconfigurado para utf-8.

REEXECUÇÃO E ERRO (iguais à etapa 1)
   CREATE OR REPLACE, nunca acrescenta.
   Faltando tabela em raw: lista quais, manda rodar
   "uv run python -m pipeline.ingestao", sys.exit(1).

CRITÉRIOS DE ACEITE
   - Linhas: pedidos 99.441, itens_pedido 112.650, pagamentos 103.886,
     clientes 99.441, vendedores 3.095, produtos 32.951,
     traducao_categorias 71, avaliacoes 99.224. Total 550.759.
   - 0 duplicatas removidas em todas as tabelas.
   - 0 falhas de conversão.
   - refined.pedidos: data_aprovacao 160 nulos, data_envio 1.783, data_entrega 2.965
     (os mesmos do raw — a conversão não fabricou nulo).
   - DESCRIBE refined.pedidos mostra TIMESTAMP nas datas e DATE em
     data_entrega_prevista.
   - sum(preco) em refined.itens_pedido = sum(CAST(price AS DECIMAL(10,2))) em raw.
   - 23.995 clientes com cep_prefixo começando em '0' (o zero sobreviveu).
   - date_trunc('month', data_compra) em refined.pedidos roda e devolve 25 meses.
   - Rodar duas vezes seguidas imprime exatamente a mesma coisa.
   - SHOW ALL TABLES não mostra geolocalizacao em refined.

ENTREGA
1. A spec como docstring no topo do arquivo, com o motivo de cada decisão.
2. O código, comentado só onde a decisão não é óbvia.
3. Uma lista final do que você assumiu e que não estava na spec.
