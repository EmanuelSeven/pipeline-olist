from pathlib import Path

import duckdb
import pytest

from pipeline import marts

SQL_DO_PROJETO = Path(__file__).resolve().parent.parent / "sql" / "marts"


def rodar_sql(banco, arquivo):
    con = duckdb.connect(str(banco))
    return con.execute(marts.ler_sql(SQL_DO_PROJETO / arquivo)).fetchall()


def test_mart01_cancelado_fica_fora_e_pedido_com_dois_itens_conta_uma_vez(banco_refined):
    # nov/2017: A (10 + 30) e B (20) válidos -> 2 pedidos, R$ 60; C cancelado (R$ 99) fora
    linhas = rodar_sql(banco_refined, "01_vendas_mensais.sql")
    assert len(linhas) == 1
    _, pedidos, receita = linhas[0]
    assert pedidos == 2
    assert str(receita) == "60.00"


def test_mart03_entrega_no_dia_previsto_a_tarde_esta_no_prazo(banco_refined):
    # A chegou às 15h do dia previsto (no prazo); B um dia depois (atrasado)
    entregues, no_prazo, atrasados, pct = rodar_sql(banco_refined, "03_entrega_no_prazo.sql")[0]
    assert (entregues, no_prazo, atrasados) == (2, 1, 1)
    assert pct == 50.0


def test_mart05_recompra_conta_a_pessoa_e_nao_o_cliente_id(banco_refined):
    # pessoa1 fez A e B (2 pedidos válidos); pessoa2 só tem pedido cancelado
    assert rodar_sql(banco_refined, "05_recompra.sql") == [(2, 1, 100.0)]


def escrever(pasta, nome, sql):
    pasta.mkdir(exist_ok=True)
    (pasta / nome).write_text(sql, encoding="utf-8")


def test_um_arquivo_vira_uma_tabela_sem_prefixo(tmp_path, banco_refined, monkeypatch, capsys):
    escrever(tmp_path / "sql", "00_teste.sql", "SELECT 1 AS x;")
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "sql")
    marts.main()
    assert "marts.teste" in capsys.readouterr().out
    con = duckdb.connect(str(banco_refined))
    assert con.execute("SELECT x FROM marts.teste").fetchall() == [(1,)]


def test_arquivo_apagado_faz_o_mart_sumir(tmp_path, banco_refined, monkeypatch):
    escrever(tmp_path / "sql", "00_teste.sql", "SELECT 1 AS x")
    escrever(tmp_path / "sql", "01_outro.sql", "SELECT 2 AS y")
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "sql")
    marts.main()
    (tmp_path / "sql" / "00_teste.sql").unlink()
    marts.main()
    con = duckdb.connect(str(banco_refined))
    nomes = {n for (n,) in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'marts'").fetchall()}
    assert nomes == {"outro"}


def test_arquivo_sem_prefixo_para_antes_de_executar(tmp_path, banco_refined, monkeypatch, capsys):
    escrever(tmp_path / "sql", "teste.sql", "SELECT 1 AS x")
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "sql")
    with pytest.raises(SystemExit):
        marts.main()
    assert "teste.sql" in capsys.readouterr().out


def test_mart_vazio_encerra_e_deixa_o_schema_como_estava(tmp_path, banco_refined, monkeypatch):
    escrever(tmp_path / "sql", "00_teste.sql", "SELECT 1 AS x")
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "sql")
    marts.main()
    escrever(tmp_path / "sql", "01_vazio.sql", "SELECT 1 AS x WHERE false")
    with pytest.raises(SystemExit):
        marts.main()
    con = duckdb.connect(str(banco_refined))
    nomes = {n for (n,) in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'marts'").fetchall()}
    assert nomes == {"teste"}


def test_erro_de_sintaxe_mostra_o_arquivo_e_mantem_o_schema(tmp_path, banco_refined, monkeypatch, capsys):
    escrever(tmp_path / "sql", "00_teste.sql", "SELECT 1 AS x")
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "sql")
    marts.main()
    escrever(tmp_path / "sql", "01_quebrado.sql", "SELEC x")
    with pytest.raises(SystemExit):
        marts.main()
    assert "01_quebrado.sql" in capsys.readouterr().out
    con = duckdb.connect(str(banco_refined))
    assert con.execute("SELECT count(*) FROM marts.teste").fetchone()[0] == 1


def test_dois_arquivos_com_o_mesmo_nome_de_tabela_param(tmp_path, banco_refined, monkeypatch, capsys):
    escrever(tmp_path / "sql", "01_x.sql", "SELECT 1")
    escrever(tmp_path / "sql", "02_x.sql", "SELECT 2")
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "sql")
    with pytest.raises(SystemExit):
        marts.main()
    assert "marts.x" in capsys.readouterr().out


def test_pasta_vazia_encerra(tmp_path, banco_refined, monkeypatch):
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "nada")
    with pytest.raises(SystemExit):
        marts.main()


def test_refined_faltando_encerra(tmp_path, banco, monkeypatch, capsys):
    escrever(tmp_path / "sql", "00_teste.sql", "SELECT 1 AS x")
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path / "sql")
    with pytest.raises(SystemExit):
        marts.main()
    assert "pipeline.transformacao" in capsys.readouterr().out
