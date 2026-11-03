"""Testes do cenário, do gerador e dos dois testes (issue #77)."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from simulacao import cenario as cen
from simulacao.gerador import (como_dataframe, gerar_contaminado, gerar_grupo,
                               gerar_par)
from simulacao.testes import (aplicar_ambos, cliff_delta, cohen_d, mann_whitney,
                              p_valores, welch)


@pytest.fixture
def rng():
    return np.random.default_rng(42)


# ---- gerador --------------------------------------------------------------

def test_lognormal_so_produz_valores_positivos(rng):
    """Tempo até merge não pode ser <= 0; a lognormal garante isso."""
    assert (gerar_grupo(rng, 500, mu_log=0.0, sigma_log=2.0) > 0).all()


def test_mediana_da_lognormal_e_exp_mu(rng):
    """Na lognormal a mediana é exp(mu) — é o que torna o efeito em log
    interpretável como razão de medianas."""
    amostra = gerar_grupo(rng, 200_000, mu_log=1.5, sigma_log=1.0)
    assert np.median(amostra) == pytest.approx(np.exp(1.5), rel=0.02)


def test_efeito_log_multiplica_a_mediana(rng):
    """efeito_log = ln(3) tem que triplicar a mediana do grupo tratado."""
    controle, tratamento = gerar_par(rng, 100_000, mu_controle=0.0,
                                     sigma_log=1.0, efeito_log=np.log(3))
    razao = np.median(tratamento) / np.median(controle)
    assert razao == pytest.approx(3.0, rel=0.03)


def test_efeito_zero_gera_grupos_da_mesma_distribuicao(rng):
    """É a configuração de H0 verdadeira usada para medir erro tipo I."""
    controle, tratamento = gerar_par(rng, 50_000, mu_controle=0.5,
                                     sigma_log=1.5, efeito_log=0.0)
    assert np.median(tratamento) == pytest.approx(np.median(controle), rel=0.05)
    assert stats.ks_2samp(controle, tratamento).pvalue > 0.01


def test_dados_simulados_sao_assimetricos_como_os_reais(rng):
    """Se o gerador produzisse dados simétricos, os dois testes concordariam
    quase sempre e não haveria o que comparar no laboratório."""
    amostra = gerar_grupo(rng, 5_000, mu_log=-0.58, sigma_log=2.25)
    assert stats.skew(amostra) > 2
    assert abs(stats.skew(np.log(amostra))) < 0.2


def test_sigma_e_n_do_tratamento_podem_diferir(rng):
    """Necessário para a violação de pressupostos da Q3 (sprint 2)."""
    controle, tratamento = gerar_par(rng, 40, mu_controle=0.0, sigma_log=1.0,
                                     efeito_log=0.0, sigma_tratamento=3.0,
                                     n_tratamento=70)
    assert controle.size == 40 and tratamento.size == 70
    assert np.std(np.log(tratamento)) > np.std(np.log(controle))


def test_contaminacao_cria_outliers(rng):
    limpa = gerar_grupo(np.random.default_rng(1), 200, 0.0, 1.0)
    suja = gerar_contaminado(np.random.default_rng(1), 200, 0.0, 1.0,
                             prop_outliers=0.05, fator=50)
    # 5% de 200 = 10 valores multiplicados por 50; o resto fica intacto.
    assert int((suja != limpa).sum()) == 10
    assert suja.max() > limpa.max()
    assert np.median(suja) == pytest.approx(np.median(limpa), rel=0.2)


def test_semente_igual_gera_dados_iguais():
    """Exigência da seção 7 do enunciado: resultado reproduzível."""
    a = gerar_par(np.random.default_rng(7), 50, 0.0, 1.0, 0.5)
    b = gerar_par(np.random.default_rng(7), 50, 0.0, 1.0, 0.5)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_parametros_invalidos_sao_rejeitados(rng):
    with pytest.raises(ValueError):
        gerar_grupo(rng, 0, 0.0, 1.0)
    with pytest.raises(ValueError):
        gerar_grupo(rng, 10, 0.0, 0.0)
    with pytest.raises(ValueError):
        gerar_contaminado(rng, 10, 0.0, 1.0, prop_outliers=1.5)


def test_dataframe_no_formato_dos_dados_reais(rng):
    controle, tratamento = gerar_par(rng, 10, 0.0, 1.0, 0.0)
    df = como_dataframe(controle, tratamento)
    assert set(df.columns) == {"grupo", "horas_ate_merge", "origem"}
    assert set(df.grupo) == {cen.GRUPO_CONTROLE, cen.GRUPO_TRATAMENTO}
    assert len(df) == 20


# ---- tamanhos de efeito ---------------------------------------------------

def test_cohen_d_calculado_a_mao():
    """Grupos com médias 10 e 7 e desvio combinado 2 -> d = 1,5."""
    a = np.array([8.0, 10.0, 12.0])        # média 10, dp 2
    b = np.array([5.0, 7.0, 9.0])          # média 7,  dp 2
    assert cohen_d(a, b) == pytest.approx(1.5)


def test_cohen_d_zero_quando_as_medias_sao_iguais():
    x = np.array([1.0, 2.0, 3.0])
    assert cohen_d(x, x.copy()) == pytest.approx(0.0)


def test_cliff_delta_nos_extremos():
    """Separação total -> +1; U no meio -> 0."""
    assert cliff_delta(u_tratamento=9, n_tratamento=3, n_controle=3) == pytest.approx(1.0)
    assert cliff_delta(u_tratamento=4.5, n_tratamento=3, n_controle=3) == pytest.approx(0.0)
    assert cliff_delta(u_tratamento=0, n_tratamento=3, n_controle=3) == pytest.approx(-1.0)


def test_sinal_positivo_significa_tratamento_maior():
    """Convenção usada no relatório: positivo = com bot demora mais."""
    tratamento = np.array([10.0, 12.0, 14.0, 16.0])
    controle = np.array([1.0, 2.0, 3.0, 4.0])
    r = aplicar_ambos(tratamento, controle)
    assert r["welch"].efeito > 0 and r["mannwhitney"].efeito > 0
    invertido = aplicar_ambos(controle, tratamento)
    assert invertido["welch"].efeito < 0 and invertido["mannwhitney"].efeito < 0


# ---- os dois testes -------------------------------------------------------

def test_welch_confere_com_o_scipy():
    a = np.array([5.0, 7.0, 9.0, 11.0, 13.0])
    b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    esperado = stats.ttest_ind(a, b, equal_var=False)
    r = welch(a, b)
    assert r.estatistica == pytest.approx(esperado.statistic)
    assert r.p_valor == pytest.approx(esperado.pvalue)


def test_mann_whitney_confere_com_o_scipy():
    a = np.array([5.0, 7.0, 9.0, 11.0, 13.0])
    b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    esperado = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = mann_whitney(a, b)
    assert r.estatistica == pytest.approx(esperado.statistic)
    assert r.p_valor == pytest.approx(esperado.pvalue)


def test_mann_whitney_ignora_a_magnitude_dos_outliers():
    """O Mann-Whitney usa só a ordem: esticar o maior valor não muda nada nele,
    mas muda o t de Welch. É a diferença central entre os dois testes."""
    controle = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    tratamento = np.array([6.0, 7.0, 8.0, 9.0, 10.0])
    extremo = tratamento.copy()
    extremo[-1] = 10_000.0

    assert mann_whitney(tratamento, controle).p_valor == pytest.approx(
        mann_whitney(extremo, controle).p_valor)
    assert welch(tratamento, controle).p_valor != pytest.approx(
        welch(extremo, controle).p_valor)


def test_bicaudal_detecta_efeito_nos_dois_sentidos():
    a = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    b = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    assert welch(a, b).p_valor == pytest.approx(welch(b, a).p_valor)
    assert mann_whitney(a, b).p_valor == pytest.approx(mann_whitney(b, a).p_valor)


def test_aplicar_ambos_devolve_os_dois():
    a, b = np.array([3.0, 4.0, 5.0]), np.array([1.0, 2.0, 3.0])
    r = aplicar_ambos(a, b)
    assert set(r) == {"welch", "mannwhitney"}
    assert r["welch"].teste == "t de Welch"
    assert r["mannwhitney"].teste == "Mann-Whitney U"


def test_atalho_de_p_valores_bate_com_a_versao_completa():
    """`p_valores` é o caminho rápido das 10.000 repetições da sprint 2;
    precisa dar exatamente o mesmo número da versão com dataclass."""
    rng = np.random.default_rng(3)
    controle, tratamento = gerar_par(rng, 30, 0.0, 2.0, 0.8)
    rapido = p_valores(tratamento, controle)
    completo = aplicar_ambos(tratamento, controle)
    assert rapido[0] == pytest.approx(completo["welch"].p_valor)
    assert rapido[1] == pytest.approx(completo["mannwhitney"].p_valor)


# ---- cenário --------------------------------------------------------------

@pytest.fixture
def csv_real(tmp_path):
    rng = np.random.default_rng(11)
    linhas = []
    for grupo, mu in ((cen.GRUPO_CONTROLE, -0.5), (cen.GRUPO_TRATAMENTO, 1.5)):
        for h in rng.lognormal(mu, 2.0, 30):
            linhas.append({"grupo": grupo, "horas_ate_merge": h})
    caminho = tmp_path / "real.csv"
    pd.DataFrame(linhas).to_csv(caminho, index=False)
    return str(caminho)


def test_parametros_vem_dos_dados_e_nao_sao_fixos(csv_real):
    c = cen.montar(csv_real)
    reais = cen.carregar_reais(csv_real)
    esperado = float(np.log(reais[cen.GRUPO_CONTROLE]).mean())
    assert c["mu_controle"] == pytest.approx(esperado)
    assert c["n_por_grupo"] == 30


def test_efeito_observado_e_a_diferenca_em_log(csv_real):
    c = cen.montar(csv_real)
    assert c["efeito_observado_log"] == pytest.approx(
        c["mu_tratamento"] - c["mu_controle"])


def test_sigma_comum_fica_entre_os_dois(csv_real):
    c = cen.montar(csv_real)
    assert min(c["sigma_controle"], c["sigma_tratamento"]) <= c["sigma_comum"]
    assert c["sigma_comum"] <= max(c["sigma_controle"], c["sigma_tratamento"])


def test_arquivo_ausente_aborta_com_mensagem_util(tmp_path):
    with pytest.raises(SystemExit, match="coleta"):
        cen.montar(str(tmp_path / "nao_existe.csv"))


def test_tempos_nao_positivos_sao_rejeitados(tmp_path):
    """A lognormal não admite zero; melhor falhar do que gerar log(0)."""
    caminho = tmp_path / "ruim.csv"
    pd.DataFrame([{"grupo": cen.GRUPO_CONTROLE, "horas_ate_merge": 0.0},
                  {"grupo": cen.GRUPO_TRATAMENTO, "horas_ate_merge": 1.0}]
                 ).to_csv(caminho, index=False)
    with pytest.raises(SystemExit, match="lognormal"):
        cen.montar(str(caminho))


def test_hipoteses_sao_distintas_para_cada_teste():
    """Welch compara médias e Mann-Whitney compara postos; enunciar o mesmo H0
    para os dois é o erro conceitual que o laboratório quer evitar."""
    assert cen.HIPOTESES["welch"]["compara"] == "médias"
    assert "postos" in cen.HIPOTESES["mannwhitney"]["compara"]
    assert cen.HIPOTESES["welch"]["h0"] != cen.HIPOTESES["mannwhitney"]["h0"]
