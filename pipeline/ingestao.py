"""Etapa 1 — Ingestão: CSV → schema raw.

SPEC (ver SPEC-ingestao.md)
1. Tabelas: mapa ARQUIVOS abaixo. Tabelas traduzidas, colunas originais.
2. Proibido: converter tipo, descartar linha, renomear coluna, escrever em raw/.
   Motivo: raw é o espelho fiel do que chegou; julgamento é da etapa 2.
3. Rodar duas vezes: CREATE OR REPLACE — recria do zero (idempotente).
4. Leitura: utf-8 declarado, .csv.gz lido direto, primeira linha é cabeçalho.
5. Tipos: tudo VARCHAR (all_varchar). Motivo: inferência estraga CEP com zero à esquerda.
6. Tela: "✓ raw.<tabela>   N linhas" por tabela + linha de total.
7. Erro: falta arquivo em raw/ → lista quais e sys.exit(1), antes de criar qualquer tabela.

Critérios de aceite: contagens do anexo A1 (total 1.550.922), DESCRIBE só VARCHAR,
duas execuções imprimem o mesmo, arquivo faltando para com o nome dele.
"""

import sys
from pathlib import Path

from pipeline.db import RAIZ, conectar, criar_schema

PASTA_RAW = RAIZ / "raw"

ARQUIVOS = {
    "olist_customers_dataset.csv.gz": "clientes",
    "olist_geolocation_dataset.csv.gz": "geolocalizacao",
    "olist_orders_dataset.csv.gz": "pedidos",
    "olist_order_items_dataset.csv.gz": "itens_pedido",
    "olist_order_payments_dataset.csv.gz": "pagamentos",
    "olist_order_reviews_dataset.csv.gz": "avaliacoes",
    "olist_products_dataset.csv.gz": "produtos",
    "olist_sellers_dataset.csv.gz": "vendedores",
    "product_category_name_translation.csv.gz": "traducao_categorias",
}


def milhar(n: int) -> str:
    """99441 -> '99.441'"""
    return f"{n:,}".replace(",", ".")


def conferir_arquivos(pasta: Path) -> None:
    """Para tudo se faltar qualquer arquivo — antes de ingerir o primeiro."""
    faltando = [nome for nome in ARQUIVOS if not (pasta / nome).is_file()]
    if faltando:
        print(f"Faltam {len(faltando)} arquivo(s) em {pasta}:")
        for nome in faltando:
            print(f"  ✗ {nome}")
        print("Nenhuma tabela foi criada.")
        sys.exit(1)


def ingerir_tabela(con, caminho: Path, tabela: str) -> int:
    """Copia um CSV para raw.<tabela>, tudo como texto. Devolve a contagem do banco."""
    # all_varchar: nenhum tipo inferido. ignore_errors=false (padrão): linha ruim
    # derruba a execução em vez de sumir em silêncio.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw.{tabela} AS
        SELECT * FROM read_csv(
            ?,
            header = true,
            all_varchar = true,
            encoding = 'utf-8',
            compression = 'gzip'
        )
        """,
        [caminho.as_posix()],
    )
    return con.execute(f"SELECT count(*) FROM raw.{tabela}").fetchone()[0]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    conferir_arquivos(PASTA_RAW)

    con = conectar()
    try:
        criar_schema(con, "raw")
        total = 0
        for arquivo, tabela in ARQUIVOS.items():
            linhas = ingerir_tabela(con, PASTA_RAW / arquivo, tabela)
            total += linhas
            print(f"✓ {'raw.' + tabela:<26}{milhar(linhas):>10} linhas")
        print(f"{len(ARQUIVOS)} tabelas{milhar(total):>27} registros")
    finally:
        con.close()


if __name__ == "__main__":
    main()
