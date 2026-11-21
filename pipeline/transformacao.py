"""Etapa 2 — Transformação: raw → refined.

SPEC (ver specs/transformacao.md, a fonte da verdade)
1. Escopo: lê de raw, escreve em refined, nunca escreve em raw.
   Entram 8 tabelas: pedidos, itens_pedido, pagamentos, avaliacoes, clientes,
   vendedores, produtos, traducao_categorias.
   Fica de fora: geolocalizacao. Motivo: nenhum indicador do curso usa; é a
   tabela mais difícil e terá spec própria (desafio 2).
2. Nomes: colunas renomeadas para português curto (mapa nos SELECT de TABELAS),
   corrigindo o "lenght" de fábrica. Motivo: os SQLs das aulas 3 e 4 usam estes nomes.
3. Tipos:
   - Datas com hora -> TIMESTAMP, formato declarado '%Y-%m-%d %H:%M:%S'.
     Motivo: a hora importa (tempo de entrega). Formato declarado, nunca inferido.
   - data_entrega_prevista -> DATE. Motivo: vem sempre com 00:00:00, a hora é falsa.
   - preco, frete, valor -> DECIMAL(10,2).
     Motivo: DOUBLE erra centavo (0.1 + 0.2 = 0.30000000000000004).
   - Contagens (parcelas, nota, item_seq, pagamento_seq, tamanhos, fotos,
     peso e medidas) -> INTEGER.
   - Identificadores que parecem número (CEP, ids) -> VARCHAR.
     Motivo: ninguém soma CEP; 23.995 clientes têm CEP com zero à esquerda.
   - Demais textos -> VARCHAR.
4. Conversão que falha: para tudo. Antes de gravar, conta coluna por coluna os
   valores não nulos que não convertem. 1 falha ou mais -> mostra
   "tabela.coluna: N valores não converteram" e sys.exit(1), sem gravar nada.
   Proibido TRY_CAST / errors="coerce" na gravação.
   Motivo: falha virando nulo se mistura com os nulos reais (2.965 pedidos sem
   entrega) e ninguém nunca mais separa os dois.
5. Duplicatas (chave de cada tabela em TABELAS):
   - Chave repetida com conteúdo idêntico: sai, fica uma cópia, e a quantidade
     removida aparece na tela.
   - Chave repetida com conteúdo diferente: para tudo, mostra tabela, chave e
     quantas chaves em conflito, sys.exit(1).
     Motivo: escolher uma linha seria decidir no escuro qual é a verdadeira.
6. Nulos: todo nulo continua nulo. Nenhuma linha apagada, nada preenchido.
   - datas de pedidos: nulo = pedido que não chegou ou foi cancelado. Os 8
     pedidos delivered sem data de entrega ficam, como anomalia anotada.
   - categoria de produto (610): "sem_categoria", se precisar, é decisão do mart.
   - titulo/comentario de avaliação: o cliente não escreveu.
   - Texto só com espaços (2 títulos e 9 comentários) fica como veio, NÃO vira
     nulo. Motivo: texto livre que nenhum indicador usa para conta.
   Motivo geral: refined corrige o tipo do dado, não inventa dado.
7. Tela: por tabela, linhas que entraram -> linhas que saíram, duplicatas
   removidas e "nulos mantidos" por coluna (só as que têm nulo). Linha final
   com o total. Milhar com ponto, stdout em utf-8.
Reexecução: CREATE OR REPLACE, nunca acrescenta.
Erro: faltando tabela em raw -> lista quais, manda rodar
  "uv run python -m pipeline.ingestao" e sys.exit(1).

Critérios de aceite: 550.759 linhas no total (pedidos 99.441, itens_pedido
112.650, pagamentos 103.886, clientes 99.441, vendedores 3.095, produtos 32.951,
traducao_categorias 71, avaliacoes 99.224); 0 duplicatas; 0 falhas; nulos de
pedidos iguais aos do raw (160, 1.783, 2.965); TIMESTAMP/DATE no DESCRIBE;
sum(preco) igual ao raw; 23.995 CEPs com '0'; 25 meses em data_compra;
duas execuções imprimem o mesmo; sem geolocalizacao em refined.
"""

import sys

from pipeline.db import conectar, criar_schema
from pipeline.ingestao import milhar

# Expressões usadas SÓ para contar falhas antes de gravar (seção 4).
# Os SELECT de gravação usam CAST/strptime, que dão erro em vez de virar nulo.
TESTE_TIMESTAMP = "try_strptime({c}, '%Y-%m-%d %H:%M:%S')"
TESTE_INTEGER = "TRY_CAST({c} AS INTEGER)"
TESTE_DECIMAL = "TRY_CAST({c} AS DECIMAL(10,2))"

# tabela -> chave (seção 5), testes de conversão (coluna nova, coluna raw, teste)
# e o SELECT de gravação. Colunas só renomeadas (VARCHAR -> VARCHAR) não têm teste.
# SELECT DISTINCT * remove as cópias idênticas; o que sobrar repetido na chave
# é conflito.
TABELAS = {
    "pedidos": {
        "chave": ["pedido_id"],
        "testes": [
            ("data_compra", "order_purchase_timestamp", TESTE_TIMESTAMP),
            ("data_aprovacao", "order_approved_at", TESTE_TIMESTAMP),
            ("data_envio", "order_delivered_carrier_date", TESTE_TIMESTAMP),
            ("data_entrega", "order_delivered_customer_date", TESTE_TIMESTAMP),
            ("data_entrega_prevista", "order_estimated_delivery_date", TESTE_TIMESTAMP),
        ],
        "select": """
            SELECT order_id AS pedido_id, customer_id AS cliente_id, order_status AS status,
              strptime(order_purchase_timestamp,      '%Y-%m-%d %H:%M:%S') AS data_compra,
              strptime(order_approved_at,             '%Y-%m-%d %H:%M:%S') AS data_aprovacao,
              strptime(order_delivered_carrier_date,  '%Y-%m-%d %H:%M:%S') AS data_envio,
              strptime(order_delivered_customer_date, '%Y-%m-%d %H:%M:%S') AS data_entrega,
              CAST(strptime(order_estimated_delivery_date, '%Y-%m-%d %H:%M:%S') AS DATE) AS data_entrega_prevista
            FROM (SELECT DISTINCT * FROM raw.pedidos)
        """,
    },
    "itens_pedido": {
        "chave": ["pedido_id", "item_seq"],
        "testes": [
            ("item_seq", "order_item_id", TESTE_INTEGER),
            ("data_limite_envio", "shipping_limit_date", TESTE_TIMESTAMP),
            ("preco", "price", TESTE_DECIMAL),
            ("frete", "freight_value", TESTE_DECIMAL),
        ],
        "select": """
            SELECT order_id AS pedido_id, CAST(order_item_id AS INTEGER) AS item_seq,
              product_id AS produto_id, seller_id AS vendedor_id,
              strptime(shipping_limit_date, '%Y-%m-%d %H:%M:%S') AS data_limite_envio,
              CAST(price AS DECIMAL(10,2)) AS preco, CAST(freight_value AS DECIMAL(10,2)) AS frete
            FROM (SELECT DISTINCT * FROM raw.itens_pedido)
        """,
    },
    "pagamentos": {
        "chave": ["pedido_id", "pagamento_seq"],
        "testes": [
            ("pagamento_seq", "payment_sequential", TESTE_INTEGER),
            ("parcelas", "payment_installments", TESTE_INTEGER),
            ("valor", "payment_value", TESTE_DECIMAL),
        ],
        "select": """
            SELECT order_id AS pedido_id, CAST(payment_sequential AS INTEGER) AS pagamento_seq,
              payment_type AS tipo, CAST(payment_installments AS INTEGER) AS parcelas,
              CAST(payment_value AS DECIMAL(10,2)) AS valor
            FROM (SELECT DISTINCT * FROM raw.pagamentos)
        """,
    },
    "avaliacoes": {
        "chave": ["avaliacao_id", "pedido_id"],
        "testes": [
            ("nota", "review_score", TESTE_INTEGER),
            ("data_criacao", "review_creation_date", TESTE_TIMESTAMP),
            ("data_resposta", "review_answer_timestamp", TESTE_TIMESTAMP),
        ],
        "select": """
            SELECT review_id AS avaliacao_id, order_id AS pedido_id, CAST(review_score AS INTEGER) AS nota,
              review_comment_title AS titulo, review_comment_message AS comentario,
              strptime(review_creation_date,    '%Y-%m-%d %H:%M:%S') AS data_criacao,
              strptime(review_answer_timestamp, '%Y-%m-%d %H:%M:%S') AS data_resposta
            FROM (SELECT DISTINCT * FROM raw.avaliacoes)
        """,
    },
    "clientes": {
        "chave": ["cliente_id"],
        "testes": [],
        "select": """
            SELECT customer_id AS cliente_id, customer_unique_id AS cliente_unico_id,
              customer_zip_code_prefix AS cep_prefixo, customer_city AS cidade, customer_state AS uf
            FROM (SELECT DISTINCT * FROM raw.clientes)
        """,
    },
    "vendedores": {
        "chave": ["vendedor_id"],
        "testes": [],
        "select": """
            SELECT seller_id AS vendedor_id, seller_zip_code_prefix AS cep_prefixo,
              seller_city AS cidade, seller_state AS uf
            FROM (SELECT DISTINCT * FROM raw.vendedores)
        """,
    },
    "produtos": {
        "chave": ["produto_id"],
        "testes": [
            ("tamanho_nome", "product_name_lenght", TESTE_INTEGER),
            ("tamanho_descricao", "product_description_lenght", TESTE_INTEGER),
            ("qtd_fotos", "product_photos_qty", TESTE_INTEGER),
            ("peso_g", "product_weight_g", TESTE_INTEGER),
            ("comprimento_cm", "product_length_cm", TESTE_INTEGER),
            ("altura_cm", "product_height_cm", TESTE_INTEGER),
            ("largura_cm", "product_width_cm", TESTE_INTEGER),
        ],
        "select": """
            SELECT product_id AS produto_id, product_category_name AS categoria,
              CAST(product_name_lenght AS INTEGER) AS tamanho_nome,
              CAST(product_description_lenght AS INTEGER) AS tamanho_descricao,
              CAST(product_photos_qty AS INTEGER) AS qtd_fotos, CAST(product_weight_g AS INTEGER) AS peso_g,
              CAST(product_length_cm AS INTEGER) AS comprimento_cm, CAST(product_height_cm AS INTEGER) AS altura_cm,
              CAST(product_width_cm AS INTEGER) AS largura_cm
            FROM (SELECT DISTINCT * FROM raw.produtos)
        """,
    },
    "traducao_categorias": {
        "chave": ["categoria"],
        "testes": [],
        "select": """
            SELECT product_category_name AS categoria, product_category_name_english AS categoria_ingles
            FROM (SELECT DISTINCT * FROM raw.traducao_categorias)
        """,
    },
}


def conferir_raw(con) -> None:
    """Para tudo se faltar qualquer tabela de entrada em raw — antes de gravar a primeira."""
    existentes = {
        nome
        for (nome,) in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw'"
        ).fetchall()
    }
    faltando = [tabela for tabela in TABELAS if tabela not in existentes]
    if faltando:
        print(f"Faltam {len(faltando)} tabela(s) em raw:")
        for tabela in faltando:
            print(f"  ✗ raw.{tabela}")
        print('Rode antes: "uv run python -m pipeline.ingestao"')
        print("Nenhuma tabela foi gravada.")
        sys.exit(1)


def contar_falhas(con, tabela: str, testes: list) -> list[str]:
    """Valores não nulos que não convertem, por coluna. Devolve as mensagens das que falharam."""
    if not testes:
        return []
    # count() ignora nulo: não nulos no raw - não nulos após o teste = falhas.
    expressoes = ", ".join(
        f"count({raw}) - count({teste.format(c=raw)})" for _, raw, teste in testes
    )
    contagens = con.execute(f"SELECT {expressoes} FROM raw.{tabela}").fetchone()
    return [
        f"{tabela}.{nova}: {milhar(n)} valores não converteram"
        for (nova, _, _), n in zip(testes, contagens)
        if n > 0
    ]


def contar_conflitos(con, select: str, chave: list[str]) -> int:
    """Chaves que continuam repetidas depois do DISTINCT = mesma chave, conteúdo diferente."""
    colunas = ", ".join(chave)
    return con.execute(
        f"SELECT count(*) FROM (SELECT {colunas} FROM ({select}) GROUP BY {colunas} HAVING count(*) > 1)"
    ).fetchone()[0]


def contar_entrada(con, tabela: str) -> tuple[int, int]:
    """(linhas em raw, cópias idênticas que o DISTINCT vai remover)."""
    linhas, distintas = con.execute(
        f"SELECT (SELECT count(*) FROM raw.{tabela}),"
        f" (SELECT count(*) FROM (SELECT DISTINCT * FROM raw.{tabela}))"
    ).fetchone()
    return linhas, linhas - distintas


def nulos_por_coluna(con, tabela: str) -> list[tuple[str, int]]:
    """Nulos de cada coluna de refined.<tabela>, só as que têm algum."""
    colunas = [linha[0] for linha in con.execute(f"DESCRIBE refined.{tabela}").fetchall()]
    expressoes = ", ".join(f'count(*) - count("{c}")' for c in colunas)
    contagens = con.execute(f"SELECT {expressoes} FROM refined.{tabela}").fetchone()
    return [(c, n) for c, n in zip(colunas, contagens) if n > 0]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    con = conectar()
    try:
        conferir_raw(con)

        # Seção 4: todas as tabelas são conferidas antes de gravar a primeira,
        # para que uma falha em produtos não deixe pedidos já gravado.
        falhas = [
            msg
            for tabela, spec in TABELAS.items()
            for msg in contar_falhas(con, tabela, spec["testes"])
        ]
        if falhas:
            for msg in falhas:
                print(f"✗ {msg}")
            print("Nenhuma tabela foi gravada.")
            sys.exit(1)

        # Seção 5: só roda depois das falhas, porque o SELECT usa CAST e
        # quebraria com erro genérico em vez da mensagem da spec.
        conflitos = [
            (tabela, spec["chave"], n)
            for tabela, spec in TABELAS.items()
            if (n := contar_conflitos(con, spec["select"], spec["chave"])) > 0
        ]
        if conflitos:
            for tabela, chave, n in conflitos:
                print(f"✗ {tabela}: {milhar(n)} chaves em conflito em ({', '.join(chave)})")
            print("Nenhuma tabela foi gravada.")
            sys.exit(1)

        criar_schema(con, "refined")
        resultados = []
        # Transação: ou as 8 tabelas são gravadas, ou nenhuma.
        con.execute("BEGIN TRANSACTION")
        try:
            for tabela, spec in TABELAS.items():
                entraram, duplicatas = contar_entrada(con, tabela)
                con.execute(f"CREATE OR REPLACE TABLE refined.{tabela} AS {spec['select']}")
                sairam = con.execute(f"SELECT count(*) FROM refined.{tabela}").fetchone()[0]
                resultados.append((tabela, entraram, sairam, duplicatas, nulos_por_coluna(con, tabela)))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise

        for tabela, entraram, sairam, duplicatas, nulos in resultados:
            print(
                f"✓ {'refined.' + tabela:<28}{milhar(entraram):>8} -> {milhar(sairam):>7} linhas"
                f"  ({milhar(duplicatas)} duplicatas)"
            )
            if nulos:
                print("    nulos mantidos: " + ", ".join(f"{c} {milhar(n)}" for c, n in nulos))

        total_entrou = sum(r[1] for r in resultados)
        total_saiu = sum(r[2] for r in resultados)
        total_dup = sum(r[3] for r in resultados)
        print(
            f"{len(TABELAS)} tabelas{milhar(total_entrou):>29} -> {milhar(total_saiu):>7} linhas"
            f"  ({milhar(total_dup)} duplicatas)"
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
