"""Página do painel. Só arruma na tela o que painel.py entrega.

Executável com:  uv run streamlit run app.py
Spec: docstring de painel.py (seção 3, layout; seção 5, filtro; seção 6, cache e erro).
"""

import pandas as pd
import streamlit as st

import painel

st.set_page_config(page_title="Olist · Operação e Logística do E-commerce",layout="wide")


@st.cache_resource(show_spinner=False)
def garantir_banco() -> None:
    """Sem olist.duckdb, ou com algum mart faltando (ex.: na Streamlit Cloud, onde o
    banco não vai para o git, ou depois de um mart novo), roda o pipeline do zero a
    partir de raw/: ingestão -> transformação -> marts.
    O painel continua só lendo marts; quem calcula é o pipeline."""
    try:
        painel.ler()
        return
    except painel.MartsFaltando:
        pass
    from pipeline import ingestao, marts, transformacao

    with st.spinner("Primeira abertura: construindo o banco a partir dos CSVs (raw → refined → marts)..."):
        for etapa in (ingestao, transformacao, marts):
            try:
                etapa.main()
            except SystemExit:
                st.error(f"O pipeline parou na etapa {etapa.__name__}. Veja o log do servidor.")
                st.stop()


@st.cache_data
def carregar() -> dict[str, pd.DataFrame]:
    return painel.ler()


garantir_banco()


try:
    dados = carregar()
except painel.MartsFaltando as erro:
    st.error(f"{erro}\n\nRode: `uv run python -m pipeline.marts`")
    st.stop()

REPOSITORIO = "https://github.com/EmanuelSeven/pipeline-olist"


def pagina_painel() -> None:
    # Cabeçalho: título à esquerda, filtro de período à direita
    esq, dir_ = st.columns([2, 1])
    with esq:
        st.title("OLIST · OPERAÇÃO E LOGÍSTICA DO E-COMMERCE")
        st.subheader("VENDAS, ENTREGAS E SATISFAÇÃO")
        if st.button("Recarregar dados"):
            carregar.clear()
            st.rerun()
    with dir_:
        # Opções como texto "AAAA-MM-DD": compara igual em qualquer versão de pandas/streamlit.
        meses = [str(m)[:10] for m in dados["vendas_mensais"].sort_values("mes")["mes"]]
        padrao_ini = next(m for m in meses if m >= "2017-01-01")
        padrao_fim = [m for m in meses if m <= "2018-08-01"][-1]
        inicio, fim = st.select_slider(
            "Período do faturamento", options=meses, value=(padrao_ini, padrao_fim),
            format_func=painel.rotulo_mes,
        )
        st.caption("O filtro recorta só o faturamento mensal; os cartões valem para o período inteiro.")

    # Faixa 1: está tudo bem?
    for coluna, (rotulo, valor) in zip(st.columns(7), painel.cartoes(dados)):
        coluna.metric(rotulo, valor)

    # Faixa 2: está subindo?
    vendas = painel.recortar_periodo(dados["vendas_mensais"], inicio, fim)
    st.plotly_chart(painel.grafico_faturamento(vendas), width="stretch")

    # Faixa 3: onde?
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(painel.grafico_categorias(dados["top_categorias"]), width="stretch")
    c2.plotly_chart(painel.grafico_mix(dados["mix_pagamento"]), width="stretch")
    c3.plotly_chart(painel.grafico_ticket_uf(dados["ticket_medio_por_estado"]), width="stretch")

    # Faixa 4: por quê?
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(painel.grafico_clientes_uf(dados["clientes_por_uf"]), width="stretch")
    c2.plotly_chart(painel.grafico_nota(dados["nota_por_categoria"]), width="stretch")
    c3.plotly_chart(painel.grafico_pareto(dados["vendedores_pareto"]), width="stretch")


def pagina_como_foi_feito() -> None:
    st.title("COMO FOI FEITO")
    st.subheader("DO CSV AO PAINEL, EM TRÊS CAMADAS")
    st.graphviz_chart(painel.DIAGRAMA)

    for coluna, (nome, registros, legenda) in zip(st.columns(3), painel.cartoes_camadas(dados)):
        coluna.metric(nome, registros)
        coluna.caption(legenda)

    st.markdown("#### Tabelas de cada camada")
    for camada, nome in painel.NOMES_CAMADA.items():
        with st.expander(nome):
            st.dataframe(painel.tabelas_da_camada(dados, camada), hide_index=True, width="stretch")

    st.markdown("#### Decisões principais")
    st.markdown("\n".join(f"- {d}" for d in painel.DECISOES))

    st.markdown("#### Para saber mais")
    st.markdown(
        f"- [Código e README]({REPOSITORIO})\n"
        f"- [Spec da ingestão]({REPOSITORIO}/blob/main/SPEC-ingestao.md)\n"
        f"- [Spec da transformação]({REPOSITORIO}/blob/main/specs/transformacao.md)\n"
        f"- [Os SQL dos indicadores]({REPOSITORIO}/tree/main/sql/marts)"
    )


st.navigation(
    [st.Page(pagina_painel, title="Painel", default=True),
     st.Page(pagina_como_foi_feito, title="Como foi feito", url_path="como-foi-feito")],
    position="top",
).run()
