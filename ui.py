"""Abre o notebook SQL do DuckDB no navegador (localhost:4213).

Uso:  uv run python ui.py      ·  Ctrl+C para encerrar.

Atenção: enquanto ele estiver de pé, o olist.duckdb fica travado e o
pipeline não consegue escrever ("Could not set lock on file").
Servidor para olhar, terminal para escrever — nunca os dois ao mesmo tempo.
"""

import time

from pipeline.db import conectar

con = conectar()
con.execute("CALL start_ui()")
print("Notebook do DuckDB em http://localhost:4213  ·  Ctrl+C para encerrar")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    con.close()
    print("Servidor encerrado.")
