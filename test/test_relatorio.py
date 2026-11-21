from datetime import datetime

import pytest

import painel
import relatorio
from test.test_painel import dados_inventados


def test_relatorio_tem_os_cartoes_e_ids_fixos():
    html = relatorio.montar(dados_inventados(), datetime(2026, 1, 2, 3, 4))
    assert "R$ 100,50" in html
    assert 'id="g01"' in html and 'id="g07"' in html
    assert "Dados de 02/01/2026 03:04" in html


def test_rodar_duas_vezes_muda_so_o_rodape(tmp_path, monkeypatch):
    monkeypatch.setattr(relatorio.painel, "ler", lambda: dados_inventados())
    monkeypatch.setattr(relatorio, "SAIDA", tmp_path / "relatorio.html")
    relatorio.main()
    primeira = (tmp_path / "relatorio.html").read_text(encoding="utf-8").splitlines()
    html = relatorio.montar(dados_inventados(), datetime(1999, 1, 1))
    segunda = html.splitlines()
    diferentes = [a for a, b in zip(primeira, segunda) if a != b]
    assert len(diferentes) == 1 and diferentes[0].startswith("<footer>")


def test_sem_marts_encerra(monkeypatch):
    def falha():
        raise painel.MartsFaltando("Faltam marts: kpis")
    monkeypatch.setattr(relatorio.painel, "ler", falha)
    with pytest.raises(SystemExit):
        relatorio.main()
