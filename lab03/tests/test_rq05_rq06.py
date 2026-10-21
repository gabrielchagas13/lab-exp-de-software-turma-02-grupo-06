import json

import numpy as np
import pandas as pd
import pytest

from analise.rq05_rq06 import CFRS, METRICAS, cliffs_delta, comparar, epsilon_squared, main


def sintetico(n=150, seed=0):
    rng = np.random.default_rng(seed)
    freq = rng.lognormal(0, 1, n)
    lang = rng.choice(["python", "go", "java", "rust"], n)
    cfr = np.clip(0.3 - 0.05 * np.log(freq) + 0.15 * (lang == "java") + rng.normal(0, 0.03, n), 0, 1)
    df = pd.DataFrame({"releases_por_semana": freq, "language": lang,
                       "stars": rng.integers(100, 5000, n), "contributors": rng.integers(1, 200, n),
                       "age_years": rng.uniform(0.5, 10, n)})
    for c in METRICAS[1:]:          # a primeira é a própria frequência
        df[c] = cfr
    return df


def test_cliffs_delta():
    assert cliffs_delta([5, 6, 7], [1, 2, 3]) == 1.0
    assert cliffs_delta([1, 2, 3], [5, 6, 7]) == -1.0
    assert cliffs_delta([1, 3, 5], [2, 4]) == pytest.approx(0.0)           # 3 vitórias, 3 derrotas
    assert cliffs_delta([2, 3, 6], [1, 4]) == pytest.approx(2 / 6)         # 4 vitórias, 2 derrotas


def test_epsilon_squared_limites():
    assert epsilon_squared(99, 100) == pytest.approx(1.0)   # H máximo = n − 1 (fórmula do enunciado)
    assert epsilon_squared(0, 100) == 0.0


def test_fator_categorico_usa_kruskal():
    r = comparar(sintetico(), "cfr_ci", "language", numerico=False)
    assert r["teste"] == "Kruskal-Wallis" and r["efeito"] == "epsilon2" and r["p_value"] < 0.001


def test_fator_numerico_vira_quartis_e_usa_kruskal():
    r = comparar(sintetico(), "cfr_ci", "stars", numerico=True)
    assert r["teste"] == "Kruskal-Wallis" and r["grupos"] == 4


def test_dois_grupos_usam_mann_whitney():
    df = sintetico()
    df["language"] = np.where(df["stars"] > 2500, "go", "java")
    r = comparar(df, "cfr_ci", "language", numerico=False)
    assert r["teste"] == "Mann-Whitney" and r["grupos"] == 2 and -1 <= r["tamanho_efeito"] <= 1


def test_linguagens_raras_viram_outros():
    df = sintetico()
    df.loc[:4, "language"] = [f"raro{i}" for i in range(5)]
    assert comparar(df, "cfr_ci", "language", numerico=False)["grupos"] == 5   # 4 linguagens + outros


def test_fator_sem_variacao_nao_gera_teste():
    assert comparar(sintetico().assign(language="go"), "cfr_ci", "language", numerico=False) is None


def test_script_de_ponta_a_ponta(tmp_path):
    (tmp_path / "data").mkdir()
    sintetico().to_csv(tmp_path / "data" / "dataset.csv", index=False)
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"data_dir": str(tmp_path / "data")}))
    main(["--config", str(cfg)])
    saida = tmp_path / "data" / "analise"
    rho = pd.read_csv(saida / "rq05_spearman.csv").set_index("cfr")["rho"]
    assert (rho < -0.5).all() and (saida / "rq05_dispersao_cfr_ci.png").exists()
    tabela = pd.read_csv(saida / "rq06_fatores.csv")
    assert len(tabela) == 4 * len(METRICAS) and (tabela["p_holm"] >= tabela["p_value"]).all()
    assert tabela.query("fator == 'language' and metrica == 'cfr_ci'")["significativo"].all()
    assert set(tabela["metrica"]) == set(METRICAS)
