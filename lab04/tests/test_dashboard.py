"""Testes do dashboard: curvas sob H0 do G2, gráficos e HTML gerado (issue #78)."""
import os

import numpy as np
import pytest
from scipy import stats

from dashboard.__main__ import gerar
from dashboard.distribuicoes import gl_welch, nulas
from dashboard.graficos import CORES_TESTE, g1_histogramas, g2_nula, g4_poder
from dashboard.pagina import markdown_simples
from simulacao import cenario as cen
from simulacao.gerador import gerar_par
from simulacao.testes import aplicar_ambos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(RAIZ, "config.json")


@pytest.fixture
def amostra():
    rng = np.random.default_rng(42)
    controle, tratamento = gerar_par(rng, 30, mu_controle=-0.58, sigma_log=2.25,
                                     efeito_log=1.0)
    return controle, tratamento


def _area(nula, distancia):
    return float(np.trapezoid(nula.densidade * nula.cauda(distancia), nula.x))


# ---- curvas sob H0 --------------------------------------------------------

def test_gl_welch_igual_ao_do_scipy(amostra):
    controle, tratamento = amostra
    r = stats.ttest_ind(tratamento, controle, equal_var=False)
    assert gl_welch(tratamento, controle) == pytest.approx(r.df)


def test_p_valor_da_curva_e_o_mesmo_do_scipy(amostra):
    """O G2 diz que a área hachurada é o p-valor da tabela: tem que ser."""
    controle, tratamento = amostra
    resultados = aplicar_ambos(tratamento, controle)
    for chave, nula in nulas(tratamento, controle).items():
        assert nula.p_valor == pytest.approx(resultados[chave].p_valor, rel=1e-9)
        assert nula.observado == pytest.approx(resultados[chave].estatistica)


def test_area_hachurada_mede_o_p_valor(amostra):
    controle, tratamento = amostra
    for nula in nulas(tratamento, controle).values():
        assert _area(nula, nula.dist_p) == pytest.approx(nula.p_valor, abs=2e-3)


def test_regiao_de_rejeicao_tem_area_alfa(amostra):
    controle, tratamento = amostra
    for nula in nulas(tratamento, controle, alfa=0.05).values():
        assert _area(nula, nula.dist_critica) == pytest.approx(0.05, abs=2e-3)


def test_rejeita_se_e_so_se_observado_cai_na_regiao(amostra):
    """Ler o gráfico (linha dentro da faixa sólida) dá a mesma decisão da tabela."""
    controle, tratamento = amostra
    resultados = aplicar_ambos(tratamento, controle)
    for chave, nula in nulas(tratamento, controle).items():
        na_regiao = abs(nula.observado - nula.centro) >= nula.dist_critica
        assert na_regiao == resultados[chave].rejeita_h0


def test_grade_cobre_o_observado_mesmo_extremo():
    """Com efeito grande o U observado fica longe; ele precisa aparecer no gráfico."""
    rng = np.random.default_rng(0)
    controle, tratamento = gerar_par(rng, 30, 0.0, 1.0, efeito_log=5.0)
    for nula in nulas(tratamento, controle).values():
        assert nula.x.min() < nula.observado < nula.x.max()


# ---- gráficos -------------------------------------------------------------

def test_cada_teste_usa_sua_cor_fixa(amostra):
    controle, tratamento = amostra
    resultados = aplicar_ambos(tratamento, controle)
    fig = g2_nula(nulas(tratamento, controle), resultados, 0.05)
    curvas = [t for t in fig.data if t.name == "Distribuição sob H0"]
    assert [t.line.color for t in curvas] == [CORES_TESTE["welch"],
                                              CORES_TESTE["mannwhitney"]]


def test_botoes_do_g1_alternam_todos_os_tracos():
    c = cen.montar(os.path.join(RAIZ, "data", "real.csv"))
    reais = cen.carregar_reais(os.path.join(RAIZ, "data", "real.csv"))
    fig = g1_histogramas(reais, reais, c)
    log, lin = (b.args[0]["visible"] for b in fig.layout.updatemenus[0].buttons)
    assert len(log) == len(lin) == len(fig.data)
    assert all(a != b for a, b in zip(log, lin))


def test_markdown_simples_escapa_e_formata():
    assert markdown_simples("**a** e *b* <c>") == \
        "<strong>a</strong> e <em>b</em> &lt;c&gt;"


# ---- página ---------------------------------------------------------------

def test_html_tem_as_sete_secoes_e_e_reproduzivel(tmp_path):
    saida_a, saida_b = tmp_path / "a.html", tmp_path / "b.html"
    gerar(CONFIG, str(saida_a))
    gerar(CONFIG, str(saida_b))
    html = saida_a.read_text(encoding="utf-8")
    assert html == saida_b.read_text(encoding="utf-8")
    for ancora in ("cenario", "nula", "erro-tipo-1", "poder", "violacoes",
                   "dados-reais", "conclusao"):
        assert f'id="{ancora}"' in html
    assert 'id="g1-histogramas"' in html and 'id="g2-nula"' in html
    assert 'id="g4-poder"' in html
    assert html.count("cdn.plot.ly") == 1


# ---- G4 e seção de poder (#80, #83) ----------------------------------------

@pytest.fixture(scope="module")
def simulados():
    import sim
    return sim.simular_tudo(reps=500, seed=42)


def test_g4_tem_uma_curva_por_teste_com_a_cor_fixa(simulados):
    fig = g4_poder(simulados, 0.05, 5.0)
    assert {t.name: t.line.color for t in fig.data} == {
        "t de Welch": CORES_TESTE["welch"],
        "Mann-Whitney U": CORES_TESTE["mannwhitney"]}
    # pelo menos 5 tamanhos de efeito, começando em 1,0 (efeito nulo)
    x = list(fig.data[0].x)
    assert len(x) >= 5 and x[0] == 1.0


def test_g4_so_usa_o_cenario_base(simulados):
    fig = g4_poder(simulados, 0.05)
    base = simulados[(simulados.cenario == "base") & (simulados.teste == "welch")]
    assert list(fig.data[0].y) == list(base.sort_values("efeito").taxa)


def test_secao_poder_cita_o_n_real_e_nao_fica_pendente(simulados):
    import sim
    from dashboard.pagina import secao_poder
    grade = sim.poder_por_n(ns=(10, 30), efeitos=(2.0, 4.0), reps=200)
    c = {"n_por_grupo": 30, "razao_medianas_observada": 3.0}
    html = secao_poder(simulados, grade, 0.05, "<div>G4</div>", c, 500)
    assert "Em construção" not in html and "n = 30" in html
    assert "mais de 30" in html or "n = 10" in html or "n = 30" in html
