"""Página do painel. Só arruma na tela o que painel.py entrega.

Executável com:  uv run streamlit run app.py
Spec: docstring de painel.py (seção 3, layout; seção 5, filtro; seção 6, cache e erro).
"""

import pandas as pd
import streamlit as st

import painel

st.set_page_config(page_title="Olist · Operação e Logística", layout="wide")


@st.cache_data
def carregar() -> dict[str, pd.DataFrame]:
    return painel.ler()


try:
    dados = carregar()
except painel.MartsFaltando as erro:
    st.error(f"{erro}\n\nRode: `uv run python -m pipeline.marts`")
    st.stop()

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
