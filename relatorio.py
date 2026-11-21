"""Relatório HTML — o mesmo painel num arquivo, para quem não roda Streamlit.

SPEC (aula 4, seção 4.5 — encanamento: a spec veio pronta)
1. Lê com painel.ler(), formata e desenha com as funções de painel.py.
   Não importa streamlit. Não desenha gráfico que não esteja em painel.py.
2. Escreve relatorio.html na raiz: um arquivo, as mesmas quatro faixas do app.py.
   Gráficos com to_html(full_html=False); plotly do CDN só no primeiro gráfico,
   nos outros include_plotlyjs=False. div_id fixo ("g01", "g02"...).
   Motivo: sem ele o plotly sorteia id e o arquivo muda sem o dado mudar.
3. Sem filtro: faturamento no período padrão (jan/2017 a ago/2018), escrito no título.
4. Rodapé "Dados de dd/mm/aaaa hh:mm". Motivo: o arquivo não fala com o banco.
5. Imprime caminho e tamanho em KB. stdout em utf-8.
Critérios: cartões iguais ao app.py; arquivo < 200 KB; duas execuções mudam só o rodapé.
"""

import sys
from datetime import datetime
from html import escape
from pathlib import Path

import painel

SAIDA = Path(__file__).resolve().parent / "relatorio.html"
PERIODO = ("2017-01-01", "2018-08-01")


def montar(dados, agora: datetime) -> str:
    vendas = painel.recortar_periodo(dados["vendas_mensais"], *PERIODO)
    fig_fat = painel.grafico_faturamento(vendas)
    fig_fat.update_layout(title=fig_fat.layout.title.text + " · jan/2017 a ago/2018")
    figuras = [
        [fig_fat],
        [painel.grafico_categorias(dados["top_categorias"]),
         painel.grafico_mix(dados["mix_pagamento"]),
         painel.grafico_ticket_uf(dados["ticket_medio_por_estado"])],
        [painel.grafico_clientes_uf(dados["clientes_por_uf"]),
         painel.grafico_nota(dados["nota_por_categoria"]),
         painel.grafico_pareto(dados["vendedores_pareto"])],
    ]

    cartoes = "".join(
        f'<div class="cartao"><div class="rotulo">{escape(r)}</div>'
        f'<div class="valor">{escape(v)}</div></div>'
        for r, v in painel.cartoes(dados)
    )

    faixas, n = [], 0
    for linha in figuras:
        blocos = []
        for fig in linha:
            n += 1
            blocos.append(fig.to_html(
                full_html=False, include_plotlyjs="cdn" if n == 1 else False,
                div_id=f"g{n:02d}",
            ))
        faixas.append(f'<div class="faixa c{len(linha)}">' + "".join(
            f"<div>{b}</div>" for b in blocos) + "</div>")

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>OLIST · OPERAÇÃO E LOGÍSTICA DO E-COMMERCE</title>
<style>
body{{font-family:system-ui,sans-serif;margin:24px 48px;color:#111}}
.cartoes{{display:grid;grid-template-columns:repeat(7,1fr);gap:12px;margin:16px 0}}
.cartao{{border:1px solid #ddd;border-radius:8px;padding:12px}}
.rotulo{{font-size:12px;color:#555}} .valor{{font-size:26px;font-weight:600;margin-top:4px}}
.faixa{{display:grid;gap:16px;margin:16px 0}} .c1{{grid-template-columns:1fr}}
.c3{{grid-template-columns:repeat(3,1fr)}}
footer{{color:#666;font-size:12px;margin-top:24px}}
</style></head><body>
<h1>OLIST · OPERAÇÃO E LOGÍSTICA DO E-COMMERCE</h1>
<h2>VENDAS, ENTREGAS E SATISFAÇÃO</h2>
<p>Os cartões valem para o período inteiro; o faturamento mostra jan/2017 a ago/2018.</p>
<div class="cartoes">{cartoes}</div>
{"".join(faixas)}
<footer>Dados de {agora:%d/%m/%Y %H:%M}</footer>
</body></html>
"""


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        dados = painel.ler()
    except painel.MartsFaltando as erro:
        print(erro)
        print('Rode: "uv run python -m pipeline.marts"')
        sys.exit(1)
    SAIDA.write_text(montar(dados, datetime.now()), encoding="utf-8")
    print(f"{SAIDA}  ({SAIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
