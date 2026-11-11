"""Testes do experimento de erro tipo I e do G3 (issue #79)."""
import numpy as np
import pytest
from scipy import stats

from dashboard.graficos import CORES_TESTE, g3_erro_tipo1
from simulacao.experimentos import (ALFAS, REPETICOES, TaxaRejeicao, erro_tipo1,
                                    ic_wilson, p_valores_replicas, poder)
from simulacao.gerador import gerar_grupo, gerar_par
from simulacao.testes import p_valores

# Cenário mínimo, no formato que `erro_tipo1` espera. Evita depender do CSV da
# coleta nos testes que só exercitam a mecânica.
BASE = {"alfa": 0.05, "n_por_grupo": 30, "mu_controle": -0.576, "sigma_comum": 2.245}


# ---- geração vetorizada ---------------------------------------------------

def test_repeticoes_devolve_uma_replica_por_linha():
    rng = np.random.default_rng(0)
    assert gerar_grupo(rng, 30, 0.0, 1.0, repeticoes=500).shape == (500, 30)


def test_sem_repeticoes_o_gerador_nao_muda():
    """Compatibilidade com o código da sprint 1, que chama sem o parâmetro."""
    assert gerar_grupo(np.random.default_rng(1), 30, 0.0, 1.0).shape == (30,)


def test_repeticoes_invalido_e_rejeitado():
    with pytest.raises(ValueError):
        gerar_grupo(np.random.default_rng(0), 10, 0.0, 1.0, repeticoes=0)


def test_replicas_mantem_a_distribuicao():
    """Gerar em lote não pode mudar mu nem sigma da lognormal."""
    lote = gerar_grupo(np.random.default_rng(2), 200, mu_log=1.5, sigma_log=0.8,
                       repeticoes=500)
    log = np.log(lote)
    assert log.mean() == pytest.approx(1.5, abs=0.02)
    assert log.std(ddof=1) == pytest.approx(0.8, abs=0.02)


def test_par_em_lote_respeita_o_efeito():
    controle, tratamento = gerar_par(np.random.default_rng(3), n=50, mu_controle=0.0,
                                     sigma_log=1.0, efeito_log=np.log(4),
                                     repeticoes=400)
    assert controle.shape == tratamento.shape == (400, 50)
    assert np.median(tratamento) / np.median(controle) == pytest.approx(4.0, rel=0.08)


def test_p_valores_em_lote_batem_com_os_individuais():
    """A versão vetorizada precisa dar exatamente o mesmo número da versão
    réplica a réplica — senão o resultado da Q1 não vale nada."""
    rng = np.random.default_rng(5)
    controle, tratamento = gerar_par(rng, n=30, mu_controle=0.0, sigma_log=2.0,
                                     efeito_log=0.0, repeticoes=50)
    ps = p_valores_replicas(np.random.default_rng(5), repeticoes=50, n=30,
                            mu_controle=0.0, sigma_log=2.0, efeito_log=0.0)
    for i in (0, 7, 49):
        welch, mw = p_valores(tratamento[i], controle[i])
        assert ps["welch"][i] == pytest.approx(welch)
        assert ps["mannwhitney"][i] == pytest.approx(mw)


def test_os_dois_testes_veem_as_mesmas_amostras():
    """A comparação é pareada: nenhuma diferença entre os testes pode ser
    atribuída ao acaso do sorteio."""
    ps = p_valores_replicas(np.random.default_rng(6), repeticoes=100, n=30,
                            mu_controle=0.0, sigma_log=2.0, efeito_log=0.0)
    assert ps["welch"].shape == ps["mannwhitney"].shape == (100,)


# ---- intervalo de Wilson --------------------------------------------------

def test_wilson_contem_a_proporcao_observada():
    baixo, alto = ic_wilson(500, 10_000)
    assert baixo < 0.05 < alto


def test_wilson_nao_sai_de_zero_e_um():
    """O intervalo normal simples ficaria negativo com zero sucessos."""
    baixo, alto = ic_wilson(0, 1_000)
    assert baixo == pytest.approx(0.0, abs=1e-12) and 0 < alto < 1
    baixo, alto = ic_wilson(1_000, 1_000)
    assert alto == 1.0 and 0 < baixo < 1


def test_wilson_estreita_com_mais_replicas():
    pequeno = ic_wilson(50, 1_000)
    grande = ic_wilson(500, 10_000)
    assert (grande[1] - grande[0]) < (pequeno[1] - pequeno[0])


def test_wilson_exige_total_positivo():
    with pytest.raises(ValueError):
        ic_wilson(0, 0)


def test_erro_padrao_da_taxa():
    taxa = TaxaRejeicao("x", 10_000, 500, 0.05, 0.0, 1.0)
    assert taxa.erro_padrao == pytest.approx(np.sqrt(0.05 * 0.95 / 10_000))


# ---- Q1 -------------------------------------------------------------------

@pytest.fixture(scope="module")
def q1():
    return erro_tipo1(BASE, repeticoes=REPETICOES, semente=42)


def test_q1_roda_as_10000_replicas(q1):
    """O enunciado pede 10.000 réplicas; é o padrão do módulo."""
    assert REPETICOES == 10_000
    for r in q1.values():
        assert r.taxa.repeticoes == 10_000
        assert r.p_valores.size == 10_000


def test_welch_e_conservador_com_dados_lognormais(q1):
    """Achado central da Q1: com assimetria forte e n = 30 o t de Welch rejeita
    bem menos que os 5% prometidos."""
    welch = q1["welch"]
    assert welch.taxa.taxa < 0.03
    assert welch.taxa.ic_alto < 0.05          # o alfa nominal nem entra no IC
    assert welch.veredito == "conservador"


def test_mann_whitney_fica_calibrado(q1):
    mw = q1["mannwhitney"]
    assert mw.taxa.ic_baixo <= 0.05 <= mw.taxa.ic_alto
    assert mw.veredito == "calibrado"


def test_welch_nao_alcanca_p_pequeno(q1):
    """Em 10.000 réplicas o menor p do Welch não chega nem a 0,001."""
    assert q1["welch"].p_minimo > 0.001
    assert q1["mannwhitney"].p_minimo < 0.001


def test_a_conservadoria_vem_da_assimetria_e_nao_de_um_bug():
    """Controle do experimento: com sigma baixo a lognormal fica quase normal,
    e aí o t de Welch tem que voltar aos 5%. Se ele continuasse conservador
    aqui, o problema estaria no código e não na distribuição."""
    quase_normal = {**BASE, "sigma_comum": 0.1}
    welch = erro_tipo1(quase_normal, repeticoes=REPETICOES, semente=42)["welch"]
    assert welch.taxa.ic_baixo <= 0.05 <= welch.taxa.ic_alto


def test_calibracao_bate_com_a_taxa_no_alfa_do_estudo(q1):
    indice = int(np.where(ALFAS == 0.05)[0][0])
    for r in q1.values():
        assert r.calibracao[indice] == pytest.approx(r.taxa.taxa)


def test_calibracao_cresce_com_alfa(q1):
    """Rejeitar com p < alfa só pode ficar mais frequente quando alfa aumenta."""
    for r in q1.values():
        assert np.all(np.diff(r.calibracao) >= 0)


def test_razao_compara_observado_com_nominal(q1):
    for r in q1.values():
        assert r.razao == pytest.approx(r.taxa.taxa / r.alfa)
    assert q1["welch"].razao < q1["mannwhitney"].razao


def test_mesma_semente_mesma_resposta():
    a = erro_tipo1(BASE, repeticoes=2_000, semente=7)
    b = erro_tipo1(BASE, repeticoes=2_000, semente=7)
    for chave in a:
        assert a[chave].taxa.rejeicoes == b[chave].taxa.rejeicoes
        assert np.array_equal(a[chave].p_valores, b[chave].p_valores)


def test_sementes_diferentes_dao_respostas_proximas():
    """Ruído de simulação: 10.000 réplicas já prendem a estimativa."""
    a = erro_tipo1(BASE, repeticoes=REPETICOES, semente=1)["welch"].taxa.taxa
    b = erro_tipo1(BASE, repeticoes=REPETICOES, semente=2)["welch"].taxa.taxa
    assert abs(a - b) < 0.01


def test_q1_aceita_violacoes_de_pressuposto():
    """Gancho da Q3 (#81): o mesmo experimento com variância desigual e grupos
    de tamanhos diferentes."""
    r = erro_tipo1(BASE, repeticoes=1_000, semente=9,
                   sigma_tratamento=4.0, n_tratamento=10)
    assert r["welch"].p_valores.size == 1_000


def test_q1_usa_o_alfa_do_cenario():
    r = erro_tipo1({**BASE, "alfa": 0.10}, repeticoes=2_000, semente=11)
    for v in r.values():
        assert v.alfa == 0.10
        assert v.taxa.rejeicoes == int((v.p_valores < 0.10).sum())


def test_h0_e_mesmo_verdadeira_nas_replicas():
    """Sem efeito, a mediana dos dois grupos coincide no agregado — é o que
    garante que toda rejeição contada é um falso positivo."""
    controle, tratamento = gerar_par(np.random.default_rng(13), n=30,
                                     mu_controle=BASE["mu_controle"],
                                     sigma_log=BASE["sigma_comum"],
                                     efeito_log=0.0, repeticoes=5_000)
    assert np.median(tratamento) == pytest.approx(np.median(controle), rel=0.05)


def test_ks_detecta_a_nao_uniformidade_do_welch(q1):
    """Sob H0 os p-valores de um teste calibrado são uniformes. O KS rejeita
    isso para o Welch com folga."""
    assert q1["welch"].ks_p < 1e-10
    assert stats.kstest(q1["welch"].p_valores, "uniform").pvalue == pytest.approx(
        q1["welch"].ks_p)


# ---- G3 -------------------------------------------------------------------

def test_g3_usa_as_cores_fixas_de_cada_teste(q1):
    fig = g3_erro_tipo1(q1, 0.05)
    usadas = str(fig.to_plotly_json())
    for cor in CORES_TESTE.values():
        assert cor.lower() in usadas.lower()


def test_g3_tem_os_dois_paineis_e_a_diagonal(q1):
    fig = g3_erro_tipo1(q1, 0.05)
    assert {t.xaxis for t in fig.data} == {"x", "x2"}
    assert any(t.name == "Calibração perfeita" for t in fig.data)


def test_g3_marca_o_alfa_com_intervalo_de_confianca(q1):
    fig = g3_erro_tipo1(q1, 0.05)
    com_erro = [t for t in fig.data
                if getattr(t, "error_y", None) and t.error_y.array is not None]
    assert len(com_erro) == 2
    for traco in com_erro:
        assert traco.error_y.array[0] > 0 and traco.error_y.arrayminus[0] > 0


# ---- Q2 (poder), usado pela conclusão -------------------------------------

def test_poder_e_maior_que_o_erro_tipo1(q1):
    """Com efeito presente os dois testes têm que rejeitar mais do que rejeitam
    sob H0 — se não, há algo errado no sinal do efeito."""
    taxas = poder({**BASE, "razao_medianas_observada": 5.14}, repeticoes=REPETICOES,
                  semente=42)
    for chave in taxas:
        assert taxas[chave].taxa > q1[chave].taxa.taxa


def test_mann_whitney_tem_mais_poder_no_efeito_observado():
    """Achado da Q2: no efeito da coleta o Mann-Whitney detecta em ~3 de 4
    experimentos e o t de Welch em ~1 de 5."""
    taxas = poder({**BASE, "razao_medianas_observada": 5.14}, repeticoes=REPETICOES,
                  semente=42)
    assert taxas["mannwhitney"].taxa > 0.70
    assert taxas["welch"].taxa < 0.25


def test_poder_cresce_com_o_efeito():
    anterior = 0.0
    for efeito in (np.log(1.5), np.log(3.0), np.log(8.0)):
        taxa = poder(BASE, efeito_log=efeito, repeticoes=2_000,
                     semente=3)["mannwhitney"].taxa
        assert taxa > anterior
        anterior = taxa


def test_poder_recusa_efeito_zero():
    """Efeito zero é H0 verdadeira: isso é erro tipo I, não poder."""
    with pytest.raises(ValueError, match="erro_tipo1"):
        poder(BASE, efeito_log=0.0, repeticoes=100)


def test_poder_usa_a_razao_de_medianas_por_padrao():
    """O padrão tem que ser o mesmo efeito que o resto do grupo usa no G4."""
    cenario = {**BASE, "razao_medianas_observada": 5.14}
    assert (poder(cenario, repeticoes=2_000, semente=4)["welch"].taxa ==
            poder(cenario, efeito_log=float(np.log(5.14)), repeticoes=2_000,
                  semente=4)["welch"].taxa)
