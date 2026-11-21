"""Painel — leitura, formatação e gráficos. Não importa streamlit.

SPEC (aula 4, seção 4.3)
1. Leitura: ler(marts) -> dict nome -> DataFrame. Só SELECT * FROM marts.<nome>.
   Conexão read_only, aberta e fechada dentro de ler().
   Motivo: conexão aberta segura o arquivo e o pipeline.marts não grava.
2. Nenhum cálculo: proibido agrupar, somar, tirar média, contar, juntar tabelas e conta entre
   colunas. Permitido: ordenar, filtrar linhas, head(n), renomear, formatar.
   Motivo: número novo na tela exige um .sql novo em marts.
   Única exceção (escrita na spec): recompra = 100 - recompra.pct_clientes
   da linha pedidos_por_cliente = 1, porque o mart 05 guarda o complemento.
3. Layout: ver app.py (quatro faixas: cartões, faturamento, onde, por quê).
4. Formato: funções puras reais/pct/numero — milhar com ponto, decimal com
   vírgula, sem locale. Motivo: o resultado não pode depender da máquina.
   Uma função por gráfico, recebendo o DataFrame e devolvendo a figura plotly.
   Motivo: o relatório HTML reaproveita as mesmas funções.
5. Filtro de período: recorta só as linhas do faturamento (feito no app.py).
6. Cache e erro: no app.py.

Critérios de aceite: cartões R$ 137,42 · 0,63% · 14,2% · 3,04% · 93,2% · 12,5 · 4,09;
faturamento abre com 20 meses (jan/2017 a ago/2018) e 24 com o filtro aberto;
top 10 com health_beauty em cima; nota com office_furniture em cima;
ticket por UF com PB em cima e SP embaixo; nenhuma agregação em painel.py/app.py.

Assumido (não estava na spec): cor única azul "#2563eb" e destaque laranja
"#ea580c" só no maior mês e na pior categoria; rótulo de mês "jan/2017";
rótulos de tela em português (meses, formas de pagamento, separador decimal),
categorias pela coluna categoria_pt (tradução no mart 00_categorias_pt.sql)
— formatação de texto, nenhum número muda.
"""

from decimal import Decimal
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CAMINHO_BANCO = Path(__file__).resolve().parent / "olist.duckdb"

MARTS = [
    "vendas_mensais", "top_categorias", "entrega_no_prazo", "nota_por_categoria",
    "recompra", "ticket_medio_por_estado", "mix_pagamento", "nota_por_prazo",
    "vendedores_pareto", "tempo_entrega_por_estado", "kpis", "clientes_por_uf",
    "tabelas_por_camada", "camadas",
]

COR = "#2563eb"
DESTAQUE = "#ea580c"
# Só rótulo de tela (formatar texto): o valor e a ordem vêm do mart 07.
ROTULOS_PAGAMENTO = {"credit_card": "Cartão de crédito", "boleto": "Boleto",
                     "voucher": "Voucher", "debit_card": "Cartão de débito",
                     "not_defined": "Não definido"}

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# ---------- 1. Leitura ----------

class MartsFaltando(Exception):
    """Sem banco, ou faltando mart. A mensagem lista quais."""


def ler(marts: list[str] = MARTS, caminho: Path | str = CAMINHO_BANCO) -> dict[str, pd.DataFrame]:
    caminho = Path(caminho)
    if not caminho.is_file():
        raise MartsFaltando(f"Banco não encontrado: {caminho}")
    con = duckdb.connect(str(caminho), read_only=True)
    try:
        existentes = {
            n for (n,) in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'marts'"
            ).fetchall()
        }
        faltando = [m for m in marts if m not in existentes]
        if faltando:
            raise MartsFaltando("Faltam marts: " + ", ".join(faltando))
        return {m: con.execute(f"SELECT * FROM marts.{m}").df() for m in marts}
    finally:
        con.close()


# ---------- 4. Formato (funções puras) ----------

def _br(valor, casas: int) -> str:
    texto = f"{Decimal(str(valor)):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def reais(valor, casas: int = 2) -> str:
    return f"R$ {_br(valor, casas)}"


def pct(valor, casas: int = 1) -> str:
    return f"{_br(valor, casas)}%"


def numero(valor, casas: int = 0) -> str:
    return _br(valor, casas)


def rotulo_mes(data) -> str:
    """2017-11-01 -> 'nov/2017'"""
    data = pd.Timestamp(data)
    return f"{MESES[data.month - 1]}/{data.year}"


# ---------- Cartões ----------

def cartoes(d: dict[str, pd.DataFrame]) -> list[tuple[str, str]]:
    """(rótulo com definição, valor formatado), na ordem da faixa 1."""
    k = d["kpis"].iloc[0]
    um_pedido = d["recompra"].loc[d["recompra"]["pedidos_por_cliente"] == 1, "pct_clientes"].iloc[0]
    prazo = d["entrega_no_prazo"].iloc[0]["pct_no_prazo"]
    return [
        ("Ticket médio · por pedido", reais(k["ticket_medio"])),
        ("Cancelados · % dos pedidos", pct(k["pct_cancelados"], 2)),
        ("Peso do frete · % do pago", pct(k["pct_frete"], 1)),
        # Exceção escrita na spec: o mart 05 guarda quem comprou uma vez.
        ("Recompra · 2+ pedidos", pct(100 - float(um_pedido), 2)),
        ("No prazo · % entregues", pct(prazo, 1)),
        ("Dias até entregar · média", numero(k["dias_entrega"], 1)),
        ("Nota média · 1 a 5", numero(k["nota_media"], 2)),
    ]


# ---------- Gráficos (uma função por gráfico) ----------

ALTURA = 520  # 27 UFs cabem com todos os rótulos


def _estilo(fig: go.Figure, titulo: str, altura: int = ALTURA) -> go.Figure:
    # separators=",.": decimal com vírgula e milhar com ponto em eixos e tooltips.
    fig.update_layout(title=titulo, margin={"l": 10, "r": 10, "t": 50, "b": 10},
                      showlegend=False, height=altura, separators=",.")
    return fig


def _todas_as_linhas(fig: go.Figure, rotulos) -> None:
    """Mostra todos os rótulos do eixo vertical (o plotly esconde alguns sozinho)."""
    rotulos = list(rotulos)
    fig.update_yaxes(tickmode="array", tickvals=rotulos, ticktext=rotulos,
                     tickfont={"size": 11})



def recortar_periodo(vendas: pd.DataFrame, inicio, fim) -> pd.DataFrame:
    """Só filtra linhas — nenhum cálculo."""
    mes = pd.to_datetime(vendas["mes"])
    return vendas[(mes >= pd.Timestamp(inicio)) & (mes <= pd.Timestamp(fim))]


def grafico_faturamento(vendas: pd.DataFrame) -> go.Figure:
    df = vendas.sort_values("mes")
    maior = df["receita"].idxmax() if len(df) else None
    cores = [DESTAQUE if i == maior else COR for i in df.index]
    fig = go.Figure(go.Scatter(
        x=pd.to_datetime(df["mes"]), y=df["receita"].astype(float),
        mode="lines+markers", line={"color": COR}, marker={"color": cores, "size": 8},
    ))
    marcas = list(pd.to_datetime(df["mes"]))[::3]
    fig.update_xaxes(title="Mês da compra", tickvals=marcas,
                     ticktext=[rotulo_mes(m) for m in marcas])
    fig.update_yaxes(title="Receita (R$)", tickformat=",.0f")
    titulo = "01 · Faturamento mensal"
    if maior is not None:
        titulo += f" · pico em {rotulo_mes(df.loc[maior, 'mes'])}"
    return _estilo(fig, titulo, altura=420)


def grafico_categorias(top: pd.DataFrame) -> go.Figure:
    df = top.sort_values("receita", ascending=False).head(10).iloc[::-1]
    fig = px.bar(x=df["receita"].astype(float), y=df["categoria_pt"], orientation="h",
                 color_discrete_sequence=[COR])
    fig.update_xaxes(title="Receita (R$)", tickformat=",.0f")
    fig.update_yaxes(title=None)
    return _estilo(fig, "02 · Receita por categoria · top 10")


def grafico_mix(mix: pd.DataFrame) -> go.Figure:
    df = mix.sort_values("pct_valor", ascending=False)
    tipos = [ROTULOS_PAGAMENTO.get(t, t) for t in df["tipo"]]
    fig = px.bar(x=tipos, y=df["pct_valor"], color_discrete_sequence=[COR])
    fig.update_yaxes(title="% do valor pago")
    fig.update_xaxes(title=None)
    return _estilo(fig, "07 · Mix de pagamento")


def grafico_ticket_uf(ticket: pd.DataFrame) -> go.Figure:
    df = ticket.sort_values("ticket_medio", ascending=True)
    fig = px.bar(df, x="ticket_medio", y="uf", orientation="h", color_discrete_sequence=[COR])
    fig.update_xaxes(title="Ticket médio (R$)")
    fig.update_yaxes(title=None)
    _todas_as_linhas(fig, df["uf"])
    return _estilo(fig, "06 · Ticket médio por UF")


def grafico_clientes_uf(clientes: pd.DataFrame) -> go.Figure:
    df = clientes.sort_values("clientes", ascending=True)
    fig = px.bar(df, x="clientes", y="uf", orientation="h", color_discrete_sequence=[COR])
    fig.update_xaxes(title="Pessoas", tickformat=",.0f")
    fig.update_yaxes(title=None)
    _todas_as_linhas(fig, df["uf"])
    return _estilo(fig, "12 · Clientes por UF")


def grafico_nota(nota: pd.DataFrame) -> go.Figure:
    df = nota.sort_values(["posicao", "categoria"]).head(10).iloc[::-1]
    cores = [COR] * len(df)
    if len(df):
        cores[-1] = DESTAQUE  # a pior categoria, em cima
    fig = go.Figure(go.Scatter(x=df["nota_media"], y=df["categoria_pt"], mode="markers",
                               marker={"color": cores, "size": 12}))
    fig.update_xaxes(title="Nota média (1 a 5)")
    return _estilo(fig, "04 · Nota por categoria · 10 piores")


def grafico_pareto(pareto: pd.DataFrame) -> go.Figure:
    df = pareto.sort_values("posicao")
    fig = go.Figure(go.Scatter(x=df["posicao"], y=df["pct_acumulado"], mode="lines",
                               line={"color": COR}))
    fig.add_hline(y=80, line_dash="dash", line_color=DESTAQUE)
    fig.update_xaxes(title="Vendedores, do maior para o menor", tickformat=",.0f")
    fig.update_yaxes(title="% acumulado da receita")
    return _estilo(fig, "09 · Concentração de vendedores")


# ---------- Página "Como foi feito" ----------

NOMES_CAMADA = {
    "raw": "Raw · dado bruto",
    "refined": "Refined · dado confiável",
    "marts": "Marts · indicadores",
}

DESCRICAO_CAMADA = {
    "raw": "Espelho fiel dos 9 CSVs: tudo como texto, nenhuma linha alterada.",
    "refined": "Tipos certos (data, dinheiro, inteiro), chaves conferidas, nulos mantidos.",
    "marts": "Uma tabela por pergunta de negócio, escrita em SQL. O painel só lê daqui.",
}

DIAGRAMA = """
digraph {
  rankdir=LR; bgcolor="transparent";
  node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=12,
        color="#2563eb", fillcolor="#eff6ff"];
  edge [color="#64748b", fontname="sans-serif", fontsize=10];
  csv [label="9 arquivos CSV", fillcolor="#f1f5f9", color="#64748b"];
  raw [label="raw"]; refined [label="refined"]; marts [label="marts"];
  painel [label="painel", fillcolor="#fff7ed", color="#ea580c"];
  csv -> raw [label="ingestão"];
  raw -> refined [label="transformação"];
  refined -> marts [label="SQL"];
  marts -> painel [label="só leitura"];
}
"""

DECISOES = [
    "**Raw não muda nada**: tudo entra como texto. Um CEP como 01310 viraria 1310 se fosse lido como número.",
    "**Nulo continua nulo**: 2.965 pedidos sem data de entrega são, quase todos, pedidos a caminho ou cancelados.",
    "**Conversão que falha para tudo**: valor que não vira data ou número encerra o pipeline, em vez de virar nulo calado.",
    "**Cópia exata sai, conflito para**: chave repetida com conteúdo diferente encerra, para ninguém escolher no escuro.",
    "**Painel sem cálculo**: todo número da tela sai pronto de um arquivo SQL em sql/marts/.",
]


def cartoes_camadas(d: dict[str, pd.DataFrame]) -> list[tuple[str, str, str]]:
    """(nome da camada, registros formatados, legenda), na ordem do pipeline."""
    df = d["camadas"].sort_values("ordem")
    return [
        (NOMES_CAMADA.get(c, c), numero(r), f"{numero(t)} tabelas · {DESCRICAO_CAMADA.get(c, '')}")
        for c, r, t in zip(df["camada"], df["registros"], df["tabelas"])
    ]


def tabelas_da_camada(d: dict[str, pd.DataFrame], camada: str) -> pd.DataFrame:
    """Só filtra, ordena, renomeia e formata — nenhum cálculo."""
    df = d["tabelas_por_camada"]
    df = df[df["camada"] == camada].sort_values("linhas", ascending=False)
    return pd.DataFrame({"Tabela": df["tabela"].to_list(),
                         "Registros": [numero(n) for n in df["linhas"]]})
