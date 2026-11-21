import duckdb
import pandas as pd
import pytest

import painel


def test_reais_usa_ponto_no_milhar_e_virgula_no_decimal():
    assert painel.reais(1003862.14) == "R$ 1.003.862,14"


def test_pct_e_numero_arredondam_nas_casas_pedidas():
    assert painel.pct(93.24) == "93,2%"
    assert painel.pct(0.6, 2) == "0,60%"
    assert painel.numero(96470) == "96.470"
    assert painel.numero(12.46, 1) == "12,5"


def test_rotulo_mes():
    assert painel.rotulo_mes("2017-11-01") == "nov/2017"


def dados_inventados():
    return {
        "kpis": pd.DataFrame([{"ticket_medio": 100.5, "pct_cancelados": 1.0, "pct_frete": 10.0,
                               "dias_entrega": 7.0, "nota_media": 4.5}]),
        # 90% das pessoas compraram uma vez -> recompra 10,00%
        "recompra": pd.DataFrame({"pedidos_por_cliente": [1, 2], "pct_clientes": [90.0, 10.0]}),
        "entrega_no_prazo": pd.DataFrame([{"pct_no_prazo": 95.0}]),
        "vendas_mensais": pd.DataFrame({"mes": pd.to_datetime(["2016-12-01", "2017-01-01", "2017-02-01"]),
                                        "pedidos": [1, 5, 9], "receita": [10.0, 50.0, 90.0]}),
        "top_categorias": pd.DataFrame({"categoria": [f"c{i}" for i in range(12)],
                                        "categoria_pt": [f"Cat {i}" for i in range(12)],
                                        "receita": list(range(12))}),
        "mix_pagamento": pd.DataFrame({"tipo": ["a", "b"], "pct_valor": [70.0, 30.0]}),
        "ticket_medio_por_estado": pd.DataFrame({"uf": ["SP", "PB"], "ticket_medio": [100.0, 200.0]}),
        "clientes_por_uf": pd.DataFrame({"uf": ["SP", "RJ"], "clientes": [10, 5]}),
        "nota_por_categoria": pd.DataFrame({"posicao": [1, 2, 3], "categoria": ["pior", "meio", "melhor"],
                                            "categoria_pt": ["Pior", "Meio", "Melhor"],
                                            "nota_media": [3.0, 4.0, 4.5]}),
        "vendedores_pareto": pd.DataFrame({"posicao": [1, 2, 3], "pct_acumulado": [60.0, 90.0, 100.0]}),
    }


def test_cartoes_na_ordem_com_recompra_como_complemento():
    valores = [v for _, v in painel.cartoes(dados_inventados())]
    assert valores == ["R$ 100,50", "1,00%", "10,0%", "10,00%", "95,0%", "7,0", "4,50"]


def test_cada_grafico_tem_um_ponto_por_linha_do_dataframe():
    d = dados_inventados()
    assert len(painel.grafico_faturamento(d["vendas_mensais"]).data[0].x) == 3
    assert len(painel.grafico_mix(d["mix_pagamento"]).data[0].x) == 2
    assert len(painel.grafico_ticket_uf(d["ticket_medio_por_estado"]).data[0].y) == 2
    assert len(painel.grafico_clientes_uf(d["clientes_por_uf"]).data[0].y) == 2
    assert len(painel.grafico_pareto(d["vendedores_pareto"]).data[0].x) == 3


def test_top_categorias_mostra_so_10_com_a_maior_em_cima():
    fig = painel.grafico_categorias(dados_inventados()["top_categorias"])
    assert len(fig.data[0].y) == 10
    assert fig.data[0].y[-1] == "Cat 11"  # plotly desenha a última no topo


def test_nota_pior_categoria_em_cima():
    fig = painel.grafico_nota(dados_inventados()["nota_por_categoria"])
    assert fig.data[0].y[-1] == "Pior"


def test_recortar_periodo_so_filtra_linhas():
    vendas = dados_inventados()["vendas_mensais"]
    assert len(painel.recortar_periodo(vendas, "2017-01-01", "2017-12-01")) == 2


def test_ler_devolve_um_dataframe_por_mart(tmp_path):
    caminho = tmp_path / "m.duckdb"
    con = duckdb.connect(str(caminho))
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.kpis AS SELECT 1 AS x")
    con.close()
    assert list(painel.ler(["kpis"], caminho)["kpis"]["x"]) == [1]


def test_ler_sem_banco_ou_sem_mart_avisa_quais_faltam(tmp_path):
    with pytest.raises(painel.MartsFaltando):
        painel.ler(["kpis"], tmp_path / "nao_existe.duckdb")
    caminho = tmp_path / "m.duckdb"
    duckdb.connect(str(caminho)).close()
    with pytest.raises(painel.MartsFaltando, match="kpis"):
        painel.ler(["kpis"], caminho)
