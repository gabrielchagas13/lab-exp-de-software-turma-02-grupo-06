"""Testes do confronto previsto × encontrado e da seção 7 (issue #84)."""
import os
import re

import pytest

from dashboard.pagina import CLASSES_VEREDITO, secao_conclusao
from simulacao.cenario import PREVISAO, PREVISOES, RECOMENDACAO
from simulacao.conclusao import VEREDITOS, avaliar, resumo
from simulacao.experimentos import erro_tipo1

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE = {"alfa": 0.05, "n_por_grupo": 30, "mu_controle": -0.576, "sigma_comum": 2.245,
        "recomendacao": RECOMENDACAO}


@pytest.fixture(scope="module")
def q1():
    return erro_tipo1(BASE, repeticoes=10_000, semente=42)


# ---- as previsões ---------------------------------------------------------

def test_toda_previsao_tem_um_avaliador():
    """Se alguém acrescentar uma previsão sem avaliador, a conclusão quebraria
    na hora de gerar o dashboard; melhor quebrar aqui."""
    from simulacao.conclusao import AVALIADORES
    assert {p["id"] for p in PREVISOES} == set(AVALIADORES)


def test_toda_previsao_aponta_a_issue_que_a_decide():
    for p in PREVISOES:
        assert isinstance(p["issue"], int)
        assert p["decide"]


def test_a_previsao_em_prosa_e_a_itemizada_falam_do_mesmo():
    """As duas formas convivem; esta é a checagem mínima de que não
    descolaram."""
    for termo in ("poder", "erro tipo I", "5%"):
        assert termo in PREVISAO or termo.lower() in PREVISAO.lower()
    assert len(PREVISOES) == 3


# ---- avaliação ------------------------------------------------------------

def test_sem_resultados_tudo_fica_pendente():
    avaliacoes = avaliar(BASE)
    assert all(a.veredito == "pendente" for a in avaliacoes)
    assert all(not a.resolvida for a in avaliacoes)
    assert all(a.issue for a in avaliacoes)


def test_q1_resolve_as_duas_previsoes_de_erro_tipo1(q1):
    por_id = {a.id: a for a in avaliar(BASE, erros_tipo1=q1)}
    assert por_id["erro_welch"].resolvida
    assert por_id["erro_mannwhitney"].resolvida
    assert not por_id["poder"].resolvida       # depende da Q2 (#80)


def test_previsao_do_welch_sai_parcial_por_nao_dizer_a_direcao(q1):
    """O Welch ficou longe de 5% como previsto, mas para o lado conservador —
    o oposto do risco que normalmente se teme. A previsão não dizia a direção,
    então o veredito honesto é parcial, não confirmada."""
    a = {x.id: x for x in avaliar(BASE, erros_tipo1=q1)}["erro_welch"]
    assert a.veredito == "parcial"
    assert "conservador" in a.encontrado


def test_previsao_do_mann_whitney_confirmada(q1):
    a = {x.id: x for x in avaliar(BASE, erros_tipo1=q1)}["erro_mannwhitney"]
    assert a.veredito == "confirmada"
    assert "4,74%" in a.encontrado


def test_welch_calibrado_refutaria_a_previsao():
    """Se o Welch ficasse nos 5%, a previsão estaria errada e o veredito tem
    que dizer isso. Cenário quase normal: sigma baixo."""
    a = {x.id: x for x in avaliar({**BASE, "sigma_comum": 0.1},
                                  erros_tipo1=erro_tipo1({**BASE, "sigma_comum": 0.1},
                                                         repeticoes=10_000,
                                                         semente=42))}["erro_welch"]
    assert a.veredito == "refutada"


def test_poder_confirmado_quando_mann_whitney_vence():
    a = {x.id: x for x in avaliar(BASE, poder={"welch": 0.42,
                                               "mannwhitney": 0.88})}["poder"]
    assert a.veredito == "confirmada"
    assert "88,00%" in a.encontrado and "42,00%" in a.encontrado


def test_poder_refutado_quando_welch_vence():
    a = {x.id: x for x in avaliar(BASE, poder={"welch": 0.90,
                                               "mannwhitney": 0.50})}["poder"]
    assert a.veredito == "refutada"


def test_todo_veredito_tem_explicacao():
    for a in avaliar(BASE, erros_tipo1=None):
        assert a.veredito in VEREDITOS


def test_resumo_conta_todos_os_vereditos(q1):
    avaliacoes = avaliar(BASE, erros_tipo1=q1)
    contagem = resumo(avaliacoes)
    assert sum(contagem.values()) == len(avaliacoes)
    assert contagem["pendente"] == 1


# ---- seção 7 --------------------------------------------------------------

def _texto(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def test_secao_mostra_numero_e_veredito_de_cada_previsao(q1):
    avaliacoes = avaliar(BASE, erros_tipo1=q1)
    html = secao_conclusao(BASE, avaliacoes, resumo(avaliacoes), "http://exemplo")
    texto = _texto(html)
    assert "1,68%" in texto and "4,74%" in texto
    for veredito in ("parcial", "confirmada", "pendente"):
        assert veredito in texto


def test_previsao_pendente_linka_a_issue_que_falta(q1):
    avaliacoes = avaliar(BASE, erros_tipo1=q1)
    html = secao_conclusao(BASE, avaliacoes, resumo(avaliacoes), "http://exemplo")
    assert 'href="http://exemplo/issues/80"' in html


def test_secao_traz_a_recomendacao_e_os_limites(q1):
    avaliacoes = avaliar(BASE, erros_tipo1=q1)
    texto = _texto(secao_conclusao(BASE, avaliacoes, resumo(avaliacoes), ""))
    assert "Mann-Whitney" in texto and "delta de Cliff" in texto
    assert "Nada aqui é causal" in texto
    assert "não universal" in texto


def test_todo_veredito_tem_classe_css():
    assert set(CLASSES_VEREDITO) == set(VEREDITOS)


# ---- navegação ------------------------------------------------------------

def test_nav_marca_so_as_secoes_que_faltam(q1):
    """A barra do topo tem que concordar com o corpo da página: a seção 7 só
    pode aparecer como pendente se a conclusão de fato não foi montada."""
    from dashboard.__main__ import gerar
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        destino = os.path.join(tmp, "index.html")
        gerar(os.path.join(RAIZ, "config.json"), destino)
        html = open(destino, encoding="utf-8").read()

    nav = re.search(r"<nav>(.*?)</nav>", html, re.S).group(1)
    for ancora in ("cenario", "nula", "erro-tipo-1", "violacoes",
                   "dados-reais", "conclusao"):
        assert f'href="#{ancora}" class=""' in nav
    # A seção 4 (Q2) ainda não existe no dashboard: o G4 vive no painel (#80).
    assert 'href="#poder" class="nav-pendente"' in nav
    assert "1 seção em construção" in nav
    # E o corpo da seção 7 não pode conter o aviso de "Em construção".
    corpo = re.search(r'<section id="conclusao">(.*?)</section>', html, re.S).group(1)
    assert "Em construção" not in corpo
    assert "Previsto" in corpo
