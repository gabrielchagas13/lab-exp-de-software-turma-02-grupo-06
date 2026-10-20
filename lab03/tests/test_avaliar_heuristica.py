"""Testes da avaliação da heurística contra o consenso (issue #67).

Os valores esperados de precisão/recall/F1 são contados à mão a partir da
matriz de confusão, não copiados da saída do código.
"""
import pandas as pd
import pytest

from validacao.avaliar_heuristica import avaliar, executar, metricas_binarias


def test_metricas_binarias_a_mao():
    # VP=2 (itens 0,1), FP=1 (item 2), FN=1 (item 3), VN=1 (item 4).
    # precisão = 2/3, recall = 2/3, F1 = 2/3.
    esperado = [True, True, False, True, False]
    previsto = [True, True, True, False, False]
    m = metricas_binarias(esperado, previsto)
    assert (m["vp"], m["fp"], m["fn"], m["vn"]) == (2, 1, 1, 1)
    assert m["precisao"] == pytest.approx(2 / 3)
    assert m["recall"] == pytest.approx(2 / 3)
    assert m["f1"] == pytest.approx(2 / 3)


def test_variante_que_nunca_diz_sim_tem_precisao_none():
    m = metricas_binarias([True, False], [False, False])
    assert m["precisao"] is None and m["recall"] == 0.0 and m["f1"] is None


def test_acertou_nada_tem_f1_zero():
    m = metricas_binarias([True, False], [False, True])
    assert m["precisao"] == 0.0 and m["recall"] == 0.0 and m["f1"] == 0.0


@pytest.fixture
def amostra():
    consenso = pd.DataFrame({
        "full_name": ["o/r"] * 4,
        "tag": ["v1.0.1", "v1.1.0", "v1.2.0", "v1.3.0"],
        "corretiva": ["sim", "sim", "nao", "sem_consenso"]})
    evidencia = pd.DataFrame({
        "full_name": ["o/r"] * 4,
        "tag": ["v1.0.1", "v1.1.0", "v1.2.0", "v1.3.0"],
        "release_nome": ["", "Hotfix", "", ""],
        "commits": ["feat: a", "feat: a", "fix: a | fix: b", "fix: a"]})
    return consenso, evidencia


def test_avaliar_exclui_sem_consenso_e_calcula_por_variante(amostra):
    resumo, itens = avaliar(*amostra)
    assert len(itens) == 3 and "v1.3.0" not in set(itens["tag"])
    por = resumo.set_index("variante")
    # v1_semver: só v1.0.1 é patch -> VP=1, FN=1 (v1.1.0), FP=0.
    assert por.loc["v1_semver", "precisao"] == 1.0
    assert por.loc["v1_semver", "recall"] == 0.5
    # v2: patch ou nome -> acerta v1.0.1 e v1.1.0, não marca v1.2.0. F1 = 1.
    assert por.loc["v2_semver_ou_nome", "f1"] == 1.0
    assert bool(por.loc["v2_semver_ou_nome", "atinge_meta"]) is True
    # v3: só commits -> marca v1.2.0 (FP) e nenhuma das corretivas.
    assert por.loc["v3_commits", "vp"] == 0 and por.loc["v3_commits", "fp"] == 1


def test_executar_sem_consenso_aborta(tmp_path):
    with pytest.raises(SystemExit):
        executar(str(tmp_path))


def test_executar_grava_resumo_e_itens(tmp_path, amostra):
    consenso, evidencia = amostra
    consenso.to_csv(tmp_path / "consenso_corretiva.csv", index=False)
    evidencia.to_csv(tmp_path / "rotulos_releases_gl.csv", index=False)
    resumo, n_sem = executar(str(tmp_path))
    assert n_sem == 1 and len(resumo) == 4
    assert (tmp_path / "avaliacao_heuristica.csv").exists()
    assert (tmp_path / "avaliacao_heuristica_itens.csv").exists()
