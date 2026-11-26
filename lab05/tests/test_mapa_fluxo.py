"""Testes do mapeamento do fluxo (issue #90).

Nenhum teste toca a rede: o HTML das telas entra como amostra. O que mais
importa aqui é o último grupo, que trava a regra de ética — o mapeamento não
pode enviar nada.
"""
import json
from pathlib import Path

import pytest

from coleta.mapa_fluxo import (SessaoSomenteLeitura, avanco, cabecalho,
                               campos_formulario, descrever, mapear, titulo)

RAIZ = Path(__file__).resolve().parents[1]

TELA_INICIAL = """
<html><head><title>Solicitar registro de ocorrência</title></head><body>
<legend>MANUAIS BÁSICOS DE ENFRENTAMENTO da Violência Doméstica</legend>
<h2>Seja bem-vindo ao sistema de delegacia virtual</h2>
<a href="/sxgn/ocorrencia/renderAlerta?tipoNatureza=2">Perda de documentos e objetos</a>
<a href="/sxgn/ocorrencia/renderAlerta?tipoNatureza=7">Furto</a>
<form action="/sxgn/ocorrencia/index"><input name="idNatureza"></form>
</body></html>
"""

TELA_IDENTIFICACAO = """
<html><head><title>Identificação inicial</title></head><body>
<h2>Perda de documentos e objetos</h2>
<legend>Identificação inicial</legend>
<div id="captchDiv"><img src="/sxgn/captcha/renderizarImagemCaptcha"></div>
<div id="content-relogio"></div>
<input name="radioInformaFimDaSessao"><input name="radioInformaFimDaSessao">
<input name="botaoFechaDialogo">
<form action="/sxgn/ocorrenciaPerdaDocumentosObjetos/index">
  <input name="nome"><input name="cpf"><input name="cpf">
  <select name="unidadeFederativa"></select><textarea name="email"></textarea>
</form></body></html>
"""


# ---- leitura das telas -----------------------------------------------------

def test_titulo_e_cabecalho_saem_da_tela():
    assert titulo(TELA_INICIAL) == "Solicitar registro de ocorrência"
    assert cabecalho(TELA_INICIAL) == "Seja bem-vindo ao sistema de delegacia virtual"


def test_cabecalho_prefere_o_h2_e_nao_o_banner():
    """Na tela inicial o <legend> rotula um banner de campanha, não a página.
    Se a regra mudasse para 'primeiro legend', o mapa viraria propaganda."""
    assert "MANUAIS" not in cabecalho(TELA_INICIAL)


def test_campos_ignoram_dialogo_de_sessao_e_nao_repetem():
    campos = campos_formulario(TELA_IDENTIFICACAO)
    assert "radioInformaFimDaSessao" not in campos
    assert "botaoFechaDialogo" not in campos
    assert campos.count("cpf") == 1
    assert set(campos) == {"nome", "cpf", "unidadeFederativa", "email"}


def test_captcha_e_relogio_de_sessao_sao_detectados():
    d = descrever(TELA_IDENTIFICACAO)
    assert d["tem_captcha"] == 1
    assert d["tem_relogio_sessao"] == 1
    assert descrever(TELA_INICIAL)["tem_captcha"] == 0


# ---- encadeamento ----------------------------------------------------------

def test_avanco_e_get_quando_a_proxima_tela_esta_linkada():
    url, metodo = avanco(TELA_INICIAL,
                         "https://x/sxgn/ocorrencia/renderAlerta?tipoNatureza=2")
    assert metodo == "GET"
    assert url.endswith("tipoNatureza=2")


def test_avanco_e_post_quando_a_proxima_nao_esta_linkada():
    """É o que acontece na identificação: dali em diante só se avança enviando
    dados. É este resultado que justifica o mapeamento manual das telas 4 e 5."""
    _, metodo = avanco(TELA_IDENTIFICACAO, "https://x/sxgn/alguma/outra")
    assert metodo == "POST"


# ---- a trava de ética ------------------------------------------------------

def test_sessao_recusa_post():
    with pytest.raises(PermissionError):
        SessaoSomenteLeitura().post("https://exemplo.invalido/")


@pytest.mark.parametrize("metodo", ["put", "delete", "patch", "options"])
def test_sessao_recusa_qualquer_metodo_de_escrita(metodo):
    with pytest.raises(PermissionError):
        getattr(SessaoSomenteLeitura(), metodo)("https://exemplo.invalido/")


def test_mapear_so_usa_get():
    """Trava de verdade: se alguém trocar o GET por um POST dentro de mapear(),
    este teste quebra antes de qualquer requisição sair da máquina."""
    chamadas = []

    class Espiao(SessaoSomenteLeitura):
        def request(self, method, url, *a, **kw):
            chamadas.append(method.upper())
            return super().request(method, url, *a, **kw)

        def get(self, url, **kw):  # não sai para a rede
            chamadas.append("GET")

            class R:
                status_code, content, text = 200, b"x", TELA_INICIAL
            return R()

    telas = [{"id": "a", "etapa": 1, "nome": "A", "url": "https://x/1"},
             {"id": "b", "etapa": 2, "nome": "B", "url": "https://x/2",
              "mapeavel": False}]
    linhas = mapear(telas, "ua-de-teste", intervalo=0, sessao=Espiao())
    assert chamadas == ["GET"]          # a tela não mapeável não é requisitada
    assert len(linhas) == 1
    assert linhas[0]["ok"] == 1


# ---- config ----------------------------------------------------------------

def test_config_descreve_o_fluxo_inteiro_inclusive_o_que_nao_da_para_medir():
    cfg = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    fluxo = cfg["fluxo_perda_documento"]
    assert fluxo["natureza"] == 2
    etapas = [t["etapa"] for t in fluxo["telas"]]
    assert etapas == sorted(etapas), "as telas têm de estar na ordem do fluxo"
    nao_mapeaveis = [t for t in fluxo["telas"] if not t.get("mapeavel", True)]
    assert nao_mapeaveis, "o fluxo não termina na identificação; faltam as telas manuais"
    for t in nao_mapeaveis:
        assert t["motivo"], "toda tela não mapeável precisa dizer por quê"


def test_telas_mapeaveis_entram_nas_paginas_medidas():
    """Se a tela está no fluxo e dá para medir, ela tem de estar em `paginas`,
    senão o Lighthouse e a disponibilidade não a enxergam."""
    cfg = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    for tela in cfg["fluxo_perda_documento"]["telas"]:
        if tela.get("mapeavel", True):
            assert cfg["paginas"].get(tela["id"]) == tela["url"]
