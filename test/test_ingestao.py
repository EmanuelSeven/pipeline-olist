import gzip

import duckdb
import pytest

from pipeline import ingestao


def escrever_csvs(pasta):
    pasta.mkdir()
    for arquivo in ingestao.ARQUIVOS:
        with gzip.open(pasta / arquivo, "wt", encoding="utf-8") as f:
            # CEP com zero à esquerda, comentário com quebra de linha e campo vazio
            f.write('id,cep,comentario\n1,01310,"linha um\nlinha dois"\n2,02000,\n')


def test_csv_vira_tabela_com_as_mesmas_linhas_tudo_texto(tmp_path, banco, monkeypatch):
    escrever_csvs(tmp_path / "raw")
    monkeypatch.setattr(ingestao, "PASTA_RAW", tmp_path / "raw")
    ingestao.main()
    con = duckdb.connect(str(banco))
    assert con.execute("SELECT count(*) FROM raw.pedidos").fetchone()[0] == 2
    tipos = {t for (_, t, *_) in con.execute("DESCRIBE raw.pedidos").fetchall()}
    assert tipos == {"VARCHAR"}
    assert con.execute("SELECT cep FROM raw.pedidos WHERE id = '1'").fetchone()[0] == "01310"
    assert con.execute("SELECT comentario FROM raw.pedidos WHERE id = '2'").fetchone()[0] is None


def test_rodar_duas_vezes_recria_e_nao_duplica(tmp_path, banco, monkeypatch, capsys):
    escrever_csvs(tmp_path / "raw")
    monkeypatch.setattr(ingestao, "PASTA_RAW", tmp_path / "raw")
    ingestao.main()
    primeira = capsys.readouterr().out
    ingestao.main()
    assert capsys.readouterr().out == primeira
    assert "18 registros" in primeira  # 9 tabelas x 2 linhas


def test_arquivo_faltando_encerra_sem_criar_tabela(tmp_path, banco, monkeypatch, capsys):
    escrever_csvs(tmp_path / "raw")
    (tmp_path / "raw" / "olist_sellers_dataset.csv.gz").unlink()
    monkeypatch.setattr(ingestao, "PASTA_RAW", tmp_path / "raw")
    with pytest.raises(SystemExit):
        ingestao.main()
    assert "olist_sellers_dataset.csv.gz" in capsys.readouterr().out
    assert not banco.exists()


def test_milhar_usa_ponto():
    assert ingestao.milhar(1550922) == "1.550.922"
