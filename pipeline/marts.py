"""Etapa 3 — Marts: refined → marts.

SPEC (aula 3, seção 3.6 — encanamento: a spec veio pronta)
1. Escopo: lê de refined, escreve no schema marts. Nunca escreve em raw nem refined.
   O schema marts é apagado e recriado a cada execução (DROP SCHEMA IF EXISTS
   marts CASCADE). Motivo: um mart cujo arquivo foi apagado não pode continuar
   existindo no banco.
2. Um arquivo, uma tabela: lê sql/marts/*.sql em ordem alfabética.
   Nome da tabela = nome do arquivo sem extensão e sem o prefixo NN_.
     sql/marts/01_vendas_mensais.sql -> marts.vendas_mensais
   Executa CREATE TABLE marts.<nome> AS <conteúdo do arquivo>.
   Tira espaços e um ponto e vírgula do final, e nada mais.
   Motivo: a regra de negócio mora inteira no .sql; o Python não altera SQL.
3. Tela: uma linha por mart com a contagem vinda do banco, milhar com ponto,
   e uma linha final com o número de marts e o total de linhas. stdout em utf-8.
4. Erro:
   - Falta tabela em refined: lista quais, manda rodar a transformação, sys.exit(1).
   - Um .sql falha: mostra o arquivo e a mensagem do DuckDB, não executa os
     seguintes, sys.exit(1).
   - Mart com zero linhas: mostra o nome e sys.exit(1).
     Motivo: mart vazio é quase sempre um JOIN que não casou.
   - sql/marts/ vazio: avisa e sys.exit(1).
   - Antes de qualquer SQL: arquivo sem prefixo NN_ ou dois arquivos com o mesmo
     nome de tabela -> lista quais e sys.exit(1).
   - Tudo numa transação só: se qualquer passo falhar (inclusive mart vazio),
     o schema marts volta a ser o da última execução que deu certo.
     Motivo: um schema pela metade quebra o dashboard sem aviso.

Critérios de aceite: 00_teste.sql com "SELECT 1 AS x" cria marts.teste com 1 linha;
apagar o arquivo faz marts.teste sumir; erro de sintaxe para tudo e deixa marts
como estava; teste.sql sem prefixo para antes de executar; duas execuções
imprimem o mesmo.

Assumido (não estava na spec): o prefixo NN_ são exatamente dois dígitos e um "_";
"linha"/"linhas" no singular/plural na saída.
"""

import re
import sys
from pathlib import Path

from pipeline.db import RAIZ, conectar
from pipeline.ingestao import milhar

PASTA_SQL = RAIZ / "sql" / "marts"

TABELAS_REFINED = [
    "pedidos", "itens_pedido", "pagamentos", "avaliacoes",
    "clientes", "vendedores", "produtos", "traducao_categorias",
]

PREFIXO = re.compile(r"^(\d{2})_(.+)$")


def encerrar(*linhas: str) -> None:
    for linha in linhas:
        print(linha)
    sys.exit(1)


def listar_arquivos(pasta: Path) -> list[tuple[str, Path]]:
    """(nome da tabela, arquivo), validados antes de executar qualquer SQL."""
    arquivos = sorted(pasta.glob("*.sql")) if pasta.is_dir() else []
    if not arquivos:
        encerrar(f"Nenhum arquivo .sql em {pasta}.")

    sem_prefixo = [a.name for a in arquivos if not PREFIXO.match(a.stem)]
    if sem_prefixo:
        encerrar("Arquivos sem prefixo NN_:", *[f"  ✗ {n}" for n in sem_prefixo])

    pares = [(PREFIXO.match(a.stem).group(2), a) for a in arquivos]
    vistos: dict[str, list[str]] = {}
    for nome, arquivo in pares:
        vistos.setdefault(nome, []).append(arquivo.name)
    repetidos = {n: fs for n, fs in vistos.items() if len(fs) > 1}
    if repetidos:
        encerrar(
            "Arquivos que dão o mesmo nome de tabela:",
            *[f"  ✗ marts.{n}: {', '.join(fs)}" for n, fs in repetidos.items()],
        )
    return pares


def conferir_refined(con) -> None:
    existentes = {
        n for (n,) in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'refined'"
        ).fetchall()
    }
    faltando = [t for t in TABELAS_REFINED if t not in existentes]
    if faltando:
        encerrar(
            f"Faltam {len(faltando)} tabela(s) em refined:",
            *[f"  ✗ refined.{t}" for t in faltando],
            'Rode antes: "uv run python -m pipeline.transformacao"',
        )


def ler_sql(arquivo: Path) -> str:
    sql = arquivo.read_text(encoding="utf-8").strip()
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    return sql


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pares = listar_arquivos(PASTA_SQL)

    con = conectar()
    try:
        conferir_refined(con)
        resultados = []
        con.execute("BEGIN TRANSACTION")
        try:
            con.execute("DROP SCHEMA IF EXISTS marts CASCADE")
            con.execute("CREATE SCHEMA marts")
            for nome, arquivo in pares:
                try:
                    con.execute(f"CREATE TABLE marts.{nome} AS {ler_sql(arquivo)}")
                except Exception as erro:  # mensagem do DuckDB, com o arquivo
                    con.execute("ROLLBACK")
                    encerrar(f"✗ {arquivo.name}", f"  {erro}", "Schema marts mantido como estava.")
                linhas = con.execute(f"SELECT count(*) FROM marts.{nome}").fetchone()[0]
                if linhas == 0:
                    con.execute("ROLLBACK")
                    encerrar(f"✗ marts.{nome} voltou vazio ({arquivo.name}).",
                             "Schema marts mantido como estava.")
                resultados.append((nome, linhas))
            con.execute("COMMIT")
        except SystemExit:
            raise
        except Exception:
            con.execute("ROLLBACK")
            raise

        for nome, linhas in resultados:
            rotulo = "linha" if linhas == 1 else "linhas"
            print(f"✓ {'marts.' + nome:<32}{milhar(linhas):>7} {rotulo}")
        total = sum(n for _, n in resultados)
        print(f"{len(resultados)} marts{milhar(total):>34} linhas")
    finally:
        con.close()


if __name__ == "__main__":
    main()
