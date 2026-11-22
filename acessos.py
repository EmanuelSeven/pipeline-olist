"""Contador de acessos do painel, guardado no Supabase (Postgres). Não importa streamlit.

Mesma solução do projeto F1: o Streamlit Community Cloud apaga o disco a cada
reinício, então o total fica numa tabela do Supabase, somado pela função
increment_olist_page_views via API REST (PostgREST). SQL em supabase/contador_acessos.sql.
Tabela e função próprias do Olist: podem morar no mesmo projeto Supabase do F1
sem misturar as contagens.

Sem OLIST_SUPABASE_URL e OLIST_SUPABASE_KEY o contador fica desligado.
Qualquer falha é registrada e ignorada: o painel nunca quebra por causa do contador.
Só biblioteca padrão (urllib): o contador não justifica uma dependência nova.
"""

import json
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 3.0
CAMINHO_RPC = "/rest/v1/rpc/increment_olist_page_views"


def registrar_acesso(url: str | None = None, chave: str | None = None, abrir=urllib.request.urlopen) -> int | None:
    """Soma um acesso e devolve o total atualizado; None se desligado ou em qualquer erro.

    url/chave vêm do ambiente quando não informadas (o Streamlit expõe os Secrets
    da raiz como variáveis de ambiente). `abrir` existe para os testes rodarem sem rede.
    """
    url = url if url is not None else os.environ.get("OLIST_SUPABASE_URL")
    chave = chave if chave is not None else os.environ.get("OLIST_SUPABASE_KEY")
    if not url or not chave:
        return None
    # Só o header apikey: a publishable key (sb_publishable_...) não é um JWT,
    # então não pode ir em Authorization: Bearer.
    pedido = urllib.request.Request(
        url.rstrip("/") + CAMINHO_RPC,
        data=b"{}",
        headers={"apikey": chave, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with abrir(pedido, timeout=TIMEOUT_SEGUNDOS) as resposta:
            total = json.loads(resposta.read())
    except (OSError, ValueError) as erro:  # rede, timeout, HTTP (URLError é OSError), JSON inválido
        logger.warning("acessos_falhou: %s", erro)
        return None
    if isinstance(total, bool) or not isinstance(total, int):
        logger.warning("acessos_falhou: resposta %r", total)
        return None
    return total
