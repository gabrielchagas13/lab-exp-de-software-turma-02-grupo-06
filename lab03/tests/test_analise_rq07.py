"""Testes da análise de sensibilidade da RQ 07 (issue #73)."""
import math

import pandas as pd
import pytest

from analise.rq07 import (COMBINACOES, PRE, classificar_combinacao, classificar_todas,
                          comparar, executar, frequencia_com_pre, robustez_rq05,
                          tabela_pares)


def serie(*cats):
    return pd.Series(cats)


def linha(nome, freq, freq_pre, lead_a, lead_b, cfr_a, cfr_b, rec):
    return {"full_name": nome, "releases_por_semana": freq, PRE: freq_pre,
            "lead_time_release_h": lead_a, "lead_time_commit_h": lead_b,
            "cfr_ci": cfr_a, "cfr_entrega_v1_semver": cfr_b,
            "cfr_entrega_v2_semver_ou_nome": cfr_b, "cfr_entrega_v3_commits": cfr_b,
            "cfr_entrega_v4_combinada": cfr_b,
            "cfr_entrega_v5_patch_e_notas": cfr_b, "recovery_median_h": rec}


# ---- concordância ----

def test_classificacoes_identicas_nao_mudam_e_kappa_um():
    a = serie("Elite", "High", "Medium", "Low")
    r = comparar(a, a)
    assert r["pct_mudou"] == 0 and r["kappa_linear"] == 1.0 and r["n"] == 4


def test_troca_para_categoria_vizinha_pesa_menos_que_troca_extrema():
    """Ponderação linear: Elite->High custa 1, Elite->Low custa 3."""
    base = serie("Elite", "Elite", "Low", "Low")
    vizinha = serie("High", "Elite", "Medium", "Low")
    extrema = serie("Low", "Elite", "Elite", "Low")
    assert comparar(base, vizinha)["pct_mudou"] == comparar(base, extrema)["pct_mudou"] == 50
    assert comparar(base, vizinha)["kappa_linear"] > comparar(base, extrema)["kappa_linear"]


def test_kappa_linear_calculado_a_mao():
    """A=(4,4,1,1), B=(3,4,2,1), peso linear w=|i-j|/3.

    D_o = (1/3 + 0 + 1/3 + 0) / 4 = 1/6.
    Marginais: A={4: .5, 1: .5}; B={1,2,3,4: .25 cada}.
    D_e = .5*.25*(1 + 2/3 + 1/3 + 0) + .5*.25*(0 + 1/3 + 2/3 + 1) = .25 + .25 = .5.
    kappa = 1 - D_o/D_e = 1 - (1/6)/.5 = 2/3."""
    r = comparar(serie("Elite", "Elite", "Low", "Low"), serie("High", "Elite", "Medium", "Low"))
    assert r["kappa_linear"] == pytest.approx(2 / 3, abs=1e-3)


def test_direcao_da_mudanca():
    a = serie("Medium", "Medium", "Medium", "Medium")
    b = serie("High", "Low", "Medium", "Elite")
    r = comparar(a, b)
    assert r["pct_subiu"] == 50 and r["pct_desceu"] == 25 and r["pct_mudou"] == 75


def test_so_conta_repositorios_classificados_nas_duas():
    a = serie("Elite", None, "Low")
    b = serie("Elite", "High", None)
    r = comparar(a, b)
    assert r["n"] == 1 and r["pct_mudou"] == 0


def test_sem_nenhum_par_valido_nao_quebra():
    r = comparar(serie(None, None), serie("Elite", "Elite"))
    assert r["n"] == 0 and r["kappa_linear"] is None


def test_kappa_indefinido_quando_so_ha_uma_classe():
    """Sem variação não há o que concordar: indefinido, não zero."""
    a = serie("High", "High", "High")
    assert comparar(a, a)["kappa_linear"] is None


def test_bootstrap_e_reprodutivel_e_contem_o_kappa():
    a = serie(*["Elite", "High", "Medium", "Low"] * 25)
    b = serie(*["Elite", "High", "High", "Low"] * 25)
    r1, r2 = comparar(a, b, replicas=200), comparar(a, b, replicas=200)
    assert r1 == r2
    assert r1["kappa_ic_inf"] <= r1["kappa_linear"] <= r1["kappa_ic_sup"]


# ---- classificação por combinação ----

def test_combinacoes_diferem_so_no_eixo_declarado():
    """C3, C4 e C5 mudam um eixo cada a partir de C1; isso é o que as torna isolantes."""
    c1 = COMBINACOES["C1"]["colunas"]
    for nome, eixo in {"C3": "lead_time", "C4": "change_failure_rate",
                       "C5": "deployment_frequency"}.items():
        c = COMBINACOES[nome]["colunas"]
        assert [k for k in c1 if c[k] != c1[k]] == [eixo]


def test_enunciado_c1_c2_c3_estao_presentes():
    assert {"C1", "C2", "C3"} <= set(COMBINACOES)
    assert len(COMBINACOES) >= 3


def test_classificacao_usa_as_colunas_da_combinacao():
    # lead (a)=300 h -> Medium; lead (b)=10 h -> Elite; CFR (a)=5% Elite; CFR (b)=50% Low
    df = pd.DataFrame([linha("o/r", 3, 3, 300, 10, 0.05, 0.50, 0.5)])
    c = classificar_todas(df)
    assert c["C1"].loc[0, "dora_lead_time"] == "Medium"
    assert c["C3"].loc[0, "dora_lead_time"] == "Elite"
    assert c["C1"].loc[0, "dora_change_failure_rate"] == "Elite"
    assert c["C4"].loc[0, "dora_change_failure_rate"] == "Low"


def test_frequencia_com_pre_muda_categoria():
    # 0,5/sem = Medium só com releases; 1,5/sem = High contando pré-releases
    df = pd.DataFrame([linha("o/r", 0.5, 1.5, 100, 100, 0.1, 0.1, 5)])
    c = classificar_todas(df)
    assert c["C1"].loc[0, "dora_deployment_frequency"] == "Medium"
    assert c["C5"].loc[0, "dora_deployment_frequency"] == "High"


def test_recuperacao_e_igual_em_todas_as_combinacoes():
    df = pd.DataFrame([linha("o/r", 3, 3, 100, 100, 0.1, 0.1, 10)])
    cats = {n: c.loc[0, "dora_recovery_time"] for n, c in classificar_todas(df).items()}
    assert set(cats.values()) == {"High"}


def test_recuperacao_ausente_fica_fora_da_mediana():
    df = pd.DataFrame([linha("o/r", 8, 8, 5, 5, 0.1, 0.1, None)])
    c = classificar_combinacao(df, COMBINACOES["C1"]["colunas"])
    assert c.loc[0, "dora_recovery_time"] is None
    assert c.loc[0, "dora_geral"] == "Elite"      # 3 métricas Elite, sem nota inventada


# ---- frequência release + pré-release ----

def test_frequencia_com_pre_ignora_rascunho_e_fora_da_janela():
    rel = pd.DataFrame({
        "repo": ["a"] * 5,
        "draft": [False, False, True, False, False],
        "in_window": [True, True, True, False, True]})
    f = frequencia_com_pre(rel, "2025-01-01", "2025-01-14")   # 14 dias = 2 semanas
    assert f["a"] == pytest.approx(3 / 2)


def test_frequencia_com_pre_contra_o_dataset_real_fecha_com_releases():
    """Sem pré-releases a contagem tem de reproduzir `releases_por_semana` do dataset."""
    rel = pd.DataFrame({"repo": ["a"] * 6, "draft": [False] * 6, "in_window": [True] * 6})
    f = frequencia_com_pre(rel, "2025-10-01", "2026-09-30")    # 365 dias
    assert f["a"] == pytest.approx(6 / (365 / 7))


# ---- tabelas e execução ----

def test_pares_cobre_todos_os_pares():
    df = pd.DataFrame([linha("o/r", 3, 3, 100, 100, 0.1, 0.1, 5)])
    t = tabela_pares(classificar_todas(df))
    assert len(t) == math.comb(len(COMBINACOES), 2)
    assert {("C1", "C2"), ("C1", "C3"), ("C2", "C3")} <= set(
        zip(t["combinacao_a"], t["combinacao_b"]))


def test_robustez_rq05_detecta_inversao_de_sinal():
    df = pd.DataFrame({"releases_por_semana": [1, 2, 3, 4, 5], PRE: [1, 2, 3, 4, 5],
                       "cfr_ci": [.5, .4, .3, .2, .1],            # cai com a frequência
                       "cfr_entrega_v5_patch_e_notas": [.1, .2, .3, .4, .5]})  # sobe
    r = robustez_rq05(df).set_index("combinacao")
    assert r.loc["C1", "rho"] == -1.0 and r.loc["C4", "rho"] == 1.0


def test_executar_grava_as_saidas(tmp_path):
    (tmp_path / "parquet").mkdir()
    pd.DataFrame({"repo": ["o/a", "o/b"], "draft": [False, False],
                  "in_window": [True, True]}).to_parquet(tmp_path / "parquet" / "releases.parquet")
    pd.DataFrame([linha("o/a", 8, 9, 5, 5, 0.05, 0.05, 0.5),
                  linha("o/b", 0.1, 0.1, 900, 900, 0.9, 0.9, 500)]
                 ).to_csv(tmp_path / "dataset.csv", index=False)
    executar(str(tmp_path), ("2025-10-01", "2026-09-30"))
    nomes = {p.name for p in (tmp_path / "analise").iterdir()}
    assert {"rq07_pares.csv", "rq07_classificacoes.csv", "rq07_distribuicao.csv",
            "rq07_por_metrica.csv", "rq07_heuristica_corretiva.csv",
            "rq07_robustez_rq05.csv"} <= nomes
