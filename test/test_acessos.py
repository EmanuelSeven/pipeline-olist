"""Contador de acessos, sem rede: `abrir` falso no lugar do urlopen."""

import io
import urllib.error

import acessos

URL = "https://xyz.supabase.co/"
CHAVE = "sb_publishable_teste"


def abrir_respondendo(corpo: bytes, guardar: list | None = None):
    def abrir(pedido, timeout):
        if guardar is not None:
            guardar.append((pedido, timeout))
        return io.BytesIO(corpo)
    return abrir


def abrir_com_erro(erro: Exception):
    def abrir(pedido, timeout):
        raise erro
    return abrir


def test_devolve_o_total_e_chama_a_funcao_certa():
    chamadas = []
    assert acessos.registrar_acesso(URL, CHAVE, abrir_respondendo(b"1234", chamadas)) == 1234
    pedido, timeout = chamadas[0]
    assert pedido.full_url == "https://xyz.supabase.co/rest/v1/rpc/increment_olist_page_views"
    assert pedido.get_method() == "POST"
    assert pedido.get_header("Apikey") == CHAVE
    assert pedido.get_header("Authorization") is None  # publishable key não é JWT
    assert timeout == acessos.TIMEOUT_SEGUNDOS


def test_desligado_sem_url_ou_chave(monkeypatch):
    monkeypatch.delenv("OLIST_SUPABASE_URL", raising=False)
    monkeypatch.delenv("OLIST_SUPABASE_KEY", raising=False)
    nao_pode_chamar = abrir_com_erro(AssertionError("não deveria chamar a rede"))
    assert acessos.registrar_acesso(abrir=nao_pode_chamar) is None
    assert acessos.registrar_acesso(URL, "", nao_pode_chamar) is None


def test_le_url_e_chave_do_ambiente(monkeypatch):
    monkeypatch.setenv("OLIST_SUPABASE_URL", URL)
    monkeypatch.setenv("OLIST_SUPABASE_KEY", CHAVE)
    assert acessos.registrar_acesso(abrir=abrir_respondendo(b"7")) == 7


def test_falhas_viram_none():
    for erro in (urllib.error.URLError("sem rede"), TimeoutError("lento")):
        assert acessos.registrar_acesso(URL, CHAVE, abrir_com_erro(erro)) is None
    for corpo in (b"isso nao e json", b'"12"', b"true", b"null"):
        assert acessos.registrar_acesso(URL, CHAVE, abrir_respondendo(corpo)) is None
