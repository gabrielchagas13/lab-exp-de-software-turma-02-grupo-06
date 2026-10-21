"""Testes da RQ 08: rework rate (issue #74)."""
import json

import pandas as pd
import pytest

from analise.rq08 import PADRAO, comparar_versao, executar, por_repo, tabela_versoes


def repo(nome, rework, cfr_b, freq=1.0, releases=10):
    colunas = {}
    for v in ("v1_semver", "v2_semver_ou_nome", "v3_commits", "v4_combinada"):
        colunas[f"cfr_release_{v}"] = rework
        colunas[f"cfr_entrega_{v}"] = cfr_b
    return {"repo": nome, "releases": releases, "releases_por_semana": freq, **colunas}


def test_diferenca_e_proporcoes_calculadas_a_mao():
    df = pd.DataFrame([repo("a", 0.5, 0.2), repo("b", 0.4, 0.4), repo("c", 0.1, 0.3)])
    r = comparar_versao(df, "v1_semver")
    # diferenças: +0,3 / 0 / -0,2 -> mediana 0
    assert r["mediana_da_diferenca"] == 0.0
    assert r["pct_rework_maior"] == pytest.approx(33.3, abs=0.1)
    assert r["pct_rework_menor"] == pytest.approx(33.3, abs=0.1)
    assert r["rework_mediana"] == 0.4 and r["cfr_b_mediana"] == 0.3


def test_rework_alto_com_cfr_b_zero_aparece_como_diferenca_positiva():
    """Releases mensais: metade são correções, mas nenhuma cai em 7 dias da anterior."""
    df = pd.DataFrame([repo("lento", 0.5, 0.0, freq=0.23), repo("rapido", 0.2, 0.2, freq=3)])
    r = comparar_versao(df, "v1_semver")
    assert r["pct_rework_maior"] == 50.0 and r["mediana_da_diferenca"] == pytest.approx(0.25)   # (0,5 e 0,0) -> 0,25


def test_spearman_entre_rework_e_cfr_b():
    df = pd.DataFrame([repo(str(i), i / 10, i / 10) for i in range(1, 6)])
    assert comparar_versao(df, "v1_semver")["spearman_rework_cfr_b"] == 1.0


def test_sem_variacao_o_spearman_e_indefinido():
    df = pd.DataFrame([repo("a", 0.3, 0.3), repo("b", 0.3, 0.3), repo("c", 0.3, 0.3)])
    assert comparar_versao(df, "v1_semver")["spearman_rework_cfr_b"] is None


def test_repositorio_sem_valor_fica_fora_do_n():
    df = pd.DataFrame([repo("a", 0.5, 0.2), repo("b", None, 0.2), repo("c", 0.1, 0.1)])
    assert comparar_versao(df, "v1_semver")["n"] == 2


def test_tabela_tem_uma_linha_por_versao():
    df = pd.DataFrame([repo("a", 0.5, 0.2), repo("b", 0.1, 0.3), repo("c", 0.2, 0.2)])
    assert list(tabela_versoes(df).versao) == [
        "v1_semver", "v2_semver_ou_nome", "v3_commits", "v4_combinada"]


def test_por_repo_usa_a_versao_padrao():
    df = pd.DataFrame([repo("a", 0.5, 0.2)])
    df[f"cfr_release_{PADRAO}"] = 0.9
    assert por_repo(df).loc[0, "rework"] == 0.9


def test_executar_grava_csvs(tmp_path):
    linhas = [repo("a", 0.5, 0.2), repo("b", 0.1, 0.3), repo("c", 0.2, 0.2)]
    (tmp_path / "metricas.json").write_text(json.dumps(linhas), encoding="utf-8")
    executar(str(tmp_path))
    assert {p.name for p in (tmp_path / "analise").iterdir()} == {
        "rq08_versoes.csv", "rq08_por_repo.csv"}
