"""Fábrica de dado inventado. Nenhum teste abre olist.duckdb nem lê raw/."""

import duckdb
import pytest

COLUNAS_RAW = {
    "pedidos": ["order_id", "customer_id", "order_status", "order_purchase_timestamp",
                "order_approved_at", "order_delivered_carrier_date",
                "order_delivered_customer_date", "order_estimated_delivery_date"],
    "itens_pedido": ["order_id", "order_item_id", "product_id", "seller_id",
                     "shipping_limit_date", "price", "freight_value"],
    "pagamentos": ["order_id", "payment_sequential", "payment_type",
                   "payment_installments", "payment_value"],
    "avaliacoes": ["review_id", "order_id", "review_score", "review_comment_title",
                   "review_comment_message", "review_creation_date", "review_answer_timestamp"],
    "clientes": ["customer_id", "customer_unique_id", "customer_zip_code_prefix",
                 "customer_city", "customer_state"],
    "vendedores": ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    "produtos": ["product_id", "product_category_name", "product_name_lenght",
                 "product_description_lenght", "product_photos_qty", "product_weight_g",
                 "product_length_cm", "product_height_cm", "product_width_cm"],
    "traducao_categorias": ["product_category_name", "product_category_name_english"],
}


def raw_minimo():
    """Uma loja de brinquedo, cada linha com o motivo de estar ali."""
    return {
        "pedidos": [
            # A: entregue às 15h do dia previsto -> no prazo; 2 itens
            ("A", "cA", "delivered", "2017-11-03 10:00:00", "2017-11-03 11:00:00",
             "2017-11-04 09:00:00", "2017-11-10 15:00:00", "2017-11-10 00:00:00"),
            # B: entregue um dia depois do previsto -> atrasado
            ("B", "cB", "delivered", "2017-11-05 10:00:00", "2017-11-05 11:00:00",
             "2017-11-06 09:00:00", "2017-11-12 08:00:00", "2017-11-11 00:00:00"),
            # C: cancelado com item de R$ 99 -> fora da receita
            ("C", "cC", "canceled", "2017-12-01 10:00:00", None, None, None,
             "2017-12-20 00:00:00"),
        ],
        "itens_pedido": [
            ("A", "1", "p1", "s1", "2017-11-05 10:00:00", "10.00", "2.00"),
            ("A", "2", "p2", "s1", "2017-11-05 10:00:00", "30.00", "3.00"),
            ("B", "1", "p1", "s2", "2017-11-07 10:00:00", "20.00", "1.00"),
            ("C", "1", "p2", "s2", "2017-12-02 10:00:00", "99.00", "5.00"),
        ],
        "pagamentos": [("A", "1", "credit_card", "2", "45.00"),
                       ("B", "1", "boleto", "1", "21.00")],
        "avaliacoes": [("r1", "A", "5", None, "ótimo", "2017-11-11 00:00:00", "2017-11-12 10:00:00"),
                       ("r2", "B", "1", "  ", None, "2017-11-13 00:00:00", "2017-11-14 10:00:00")],
        "clientes": [("cA", "pessoa1", "01310", "sao paulo", "SP"),
                     ("cB", "pessoa1", "01310", "sao paulo", "SP"),   # mesma pessoa, 2º pedido
                     ("cC", "pessoa2", "20000", "rio", "RJ")],
        "vendedores": [("s1", "01000", "sao paulo", "SP"), ("s2", "30000", "bh", "MG")],
        "produtos": [("p1", "brinquedos", "10.0", "100.0", "1.0", "200.0", "10.0", "10.0", "10.0"),
                     ("p2", None, None, None, None, "300.0", "5.0", "5.0", "5.0")],
        "traducao_categorias": [("brinquedos", "toys")],
    }


def gravar_raw(con, linhas_por_tabela):
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for tabela, colunas in COLUNAS_RAW.items():
        cols = ", ".join(f"{c} VARCHAR" for c in colunas)
        con.execute(f"CREATE OR REPLACE TABLE raw.{tabela} ({cols})")
        linhas = linhas_por_tabela.get(tabela, [])
        if linhas:
            marcas = ", ".join("?" for _ in colunas)
            con.executemany(f"INSERT INTO raw.{tabela} VALUES ({marcas})", linhas)


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Caminho de um DuckDB novo; todo módulo do pipeline passa a abrir este."""
    caminho = tmp_path / "teste.duckdb"
    import pipeline.ingestao
    import pipeline.marts
    import pipeline.transformacao

    def abrir(*_args, **_kwargs):
        return duckdb.connect(str(caminho))

    for modulo in (pipeline.ingestao, pipeline.transformacao, pipeline.marts):
        monkeypatch.setattr(modulo, "conectar", abrir)
    return caminho


@pytest.fixture
def banco_refined(banco):
    """Banco com raw inventado e refined gerado pela transformação de verdade."""
    from pipeline import transformacao
    con = duckdb.connect(str(banco))
    gravar_raw(con, raw_minimo())
    con.close()
    transformacao.main()
    return banco
