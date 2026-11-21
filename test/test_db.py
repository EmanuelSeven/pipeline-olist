import duckdb

from pipeline import db


def test_conectar_cria_o_arquivo_no_caminho_dado(tmp_path):
    caminho = tmp_path / "x.duckdb"
    con = db.conectar(caminho)
    con.close()
    assert caminho.is_file()


def test_criar_schema_rodar_duas_vezes_nao_quebra(tmp_path):
    con = duckdb.connect(str(tmp_path / "x.duckdb"))
    db.criar_schema(con, "raw")
    db.criar_schema(con, "raw")
    schemas = [s for (s,) in con.execute("SELECT schema_name FROM information_schema.schemata").fetchall()]
    assert schemas.count("raw") == 1
