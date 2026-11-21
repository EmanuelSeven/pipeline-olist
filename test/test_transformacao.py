import duckdb
import pytest

from pipeline import transformacao
from test.conftest import gravar_raw, raw_minimo


def test_datas_viram_timestamp_e_dinheiro_decimal(banco_refined):
    con = duckdb.connect(str(banco_refined))
    tipos = {c: t for (c, t, *_) in con.execute("DESCRIBE refined.pedidos").fetchall()}
    assert tipos["data_compra"] == "TIMESTAMP"
    assert tipos["data_entrega_prevista"] == "DATE"
    tipos_itens = {c: t for (c, t, *_) in con.execute("DESCRIBE refined.itens_pedido").fetchall()}
    assert tipos_itens["preco"] == "DECIMAL(10,2)"
    assert tipos_itens["item_seq"] == "INTEGER"


def test_nulo_continua_nulo_e_nenhuma_linha_some(banco_refined):
    con = duckdb.connect(str(banco_refined))
    # o pedido C (cancelado) não tem data de entrega: continua lá, com nulo
    assert con.execute("SELECT count(*) FROM refined.pedidos").fetchone()[0] == 3
    assert con.execute("SELECT data_entrega FROM refined.pedidos WHERE pedido_id = 'C'").fetchone()[0] is None


def test_cep_mantem_o_zero_e_texto_so_com_espacos_fica_como_veio(banco_refined):
    con = duckdb.connect(str(banco_refined))
    assert con.execute("SELECT cep_prefixo FROM refined.clientes WHERE cliente_id = 'cA'").fetchone()[0] == "01310"
    assert con.execute("SELECT titulo FROM refined.avaliacoes WHERE avaliacao_id = 'r2'").fetchone()[0] == "  "


def test_duplicata_exata_sai_e_aparece_na_tela(banco, capsys):
    dados = raw_minimo()
    dados["pedidos"].append(dados["pedidos"][0])  # cópia exata do pedido A
    con = duckdb.connect(str(banco))
    gravar_raw(con, dados)
    con.close()
    transformacao.main()
    saida = capsys.readouterr().out
    assert "4 ->       3 linhas  (1 duplicatas)" in saida


def test_chave_repetida_com_conteudo_diferente_para_tudo(banco, capsys):
    dados = raw_minimo()
    conflito = list(dados["pedidos"][0])
    conflito[2] = "shipped"  # mesmo pedido A, outro status
    dados["pedidos"].append(tuple(conflito))
    con = duckdb.connect(str(banco))
    gravar_raw(con, dados)
    con.close()
    with pytest.raises(SystemExit):
        transformacao.main()
    assert "chaves em conflito" in capsys.readouterr().out


def test_valor_que_nao_converte_encerra_sem_gravar(banco, capsys):
    dados = raw_minimo()
    linha = list(dados["itens_pedido"][0])
    linha[5] = "dez reais"  # preço que não vira DECIMAL
    dados["itens_pedido"][0] = tuple(linha)
    con = duckdb.connect(str(banco))
    gravar_raw(con, dados)
    con.close()
    with pytest.raises(SystemExit):
        transformacao.main()
    assert "itens_pedido.preco: 1 valores não converteram" in capsys.readouterr().out
    con = duckdb.connect(str(banco))
    refined = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'refined'"
    ).fetchone()[0]
    assert refined == 0


def test_tabela_faltando_em_raw_encerra(banco, capsys):
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA raw")
    con.close()
    with pytest.raises(SystemExit):
        transformacao.main()
    assert "pipeline.ingestao" in capsys.readouterr().out
