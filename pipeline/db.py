"""Conexão com o banco do projeto.

Um lugar só sabe onde o banco mora. Todas as etapas (ingestão,
transformação, marts) abrem o banco por aqui.
"""

from pathlib import Path

import duckdb

# Raiz do projeto = pasta acima de pipeline/
RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ / "olist.duckdb"


def conectar(caminho: Path | str = CAMINHO_BANCO) -> duckdb.DuckDBPyConnection:
    """Abre (ou cria) o olist.duckdb na raiz do projeto."""
    return duckdb.connect(str(caminho))


def criar_schema(con: duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria o schema se ainda não existir. Rodar de novo não faz nada."""
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {nome}")
