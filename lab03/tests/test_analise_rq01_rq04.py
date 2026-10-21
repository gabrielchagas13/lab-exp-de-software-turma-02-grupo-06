"""Testes da análise das RQ 01 a RQ 04 e da classificação C1 (issue #71)."""
import json

import pandas as pd
import pytest

from analise.rq01_rq04 import (EXTRAS, METRICAS_C1, classificar_c1, descritivas,
                               distribuicao, executar)


def repo(nome, freq, lead, cfr, rec, **extra):
    return {"repo": nome, "releases_por_semana": freq, "lead_time_release_h": lead,
            "cfr_ci": cfr, "recovery_median_h": rec,
            "lead_time_commit_h": extra.get("lead_commit", lead),
            "recovery_censored_ratio": extra.get("censurados", 0.0)}


@pytest.fixture
def data_dir(tmp_path):
    linhas = [
        repo("o/elite", 10, 5, 0.05, 0.5),      # (4,4,4,4) -> Elite
        repo("o/high", 3, 30, 0.2, 10),         # (3,3,3,3) -> High
        repo("o/medium", 0.5, 200, 0.4, 100),   # (2,2,2,2) -> Medium
        repo("o/low", 0.1, 1000, 0.8, 300),     # (1,1,1,1) -> Low
    ]
    (tmp_path / "metricas.json").write_text(json.dumps(linhas), encoding="utf-8")
    return str(tmp_path)


# ---- descritivas ----

def test_usa_mediana_e_iqr_nao_media():
    """A media seria dominada pelos extremos; o enunciado exige mediana e IQR."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 1000]})
    d = descritivas(df, {"x": ("unid", "desc")}).iloc[0]
    assert d["mediana"] == 3            # media seria 202
    assert d["q1"] == 2 and d["q3"] == 4 and d["iqr"] == 2


def test_ausentes_sao_contados_e_nao_zerados():
    """Repositorio sem episodio de falha nao tem tempo de recuperacao.

    Tratar como zero faria ele parecer perfeito em vez de nao medido."""
    df = pd.DataFrame({"x": [10, None, 20, None]})
    d = descritivas(df, {"x": ("h", "desc")}).iloc[0]
    assert d["n"] == 2 and d["ausentes"] == 2
    assert d["mediana"] == 15           # seria 5 se os None virassem 0


def test_coluna_toda_vazia_nao_quebra():
    df = pd.DataFrame({"x": [None, None]})
    d = descritivas(df, {"x": ("h", "desc")}).iloc[0]
    assert d["n"] == 0 and d["mediana"] is None


# ---- classificacao C1 ----

def test_c1_usa_lead_time_a_e_cfr_de_ci():
    """C1 (referencia da RQ 07) = release | lead time (a) | CFR (a)."""
    assert METRICAS_C1["lead_time"][0] == "lead_time_release_h"
    assert METRICAS_C1["change_failure_rate"][0] == "cfr_ci"


def test_classifica_cada_repositorio(data_dir):
    import json as _j
    df = pd.DataFrame(_j.load(open(f"{data_dir}/metricas.json", encoding="utf-8")))
    c1 = classificar_c1(df).set_index("repo")
    assert c1.loc["o/elite", "dora_geral"] == "Elite"
    assert c1.loc["o/high", "dora_geral"] == "High"
    assert c1.loc["o/medium", "dora_geral"] == "Medium"
    assert c1.loc["o/low", "dora_geral"] == "Low"


def test_mantem_os_valores_junto_da_categoria(data_dir):
    """A tabela do artigo precisa do valor ao lado da categoria, para auditoria."""
    import json as _j
    df = pd.DataFrame(_j.load(open(f"{data_dir}/metricas.json", encoding="utf-8")))
    c1 = classificar_c1(df).set_index("repo")
    assert c1.loc["o/elite", "valor_deployment_frequency"] == 10
    assert c1.loc["o/elite", "valor_recovery_time"] == 0.5


def test_metrica_ausente_reduz_metricas_validas():
    df = pd.DataFrame([repo("o/r", 10, 5, 0.05, None)])
    c1 = classificar_c1(df).iloc[0]
    assert c1["dora_metricas_validas"] == 3
    assert c1["dora_recovery_time"] is None
    assert c1["dora_geral"] == "Elite"


# ---- distribuicao ----

def test_distribuicao_conta_por_categoria(data_dir):
    import json as _j
    df = pd.DataFrame(_j.load(open(f"{data_dir}/metricas.json", encoding="utf-8")))
    dist = distribuicao(classificar_c1(df)).set_index("dimensao")
    linha = dist.loc["geral"]
    assert (linha["Elite"], linha["High"], linha["Medium"], linha["Low"]) == (1, 1, 1, 1)
    assert linha["pct_elite_ou_high"] == 50.0


# ---- execucao completa ----

def test_executar_gera_os_tres_csvs(data_dir):
    import os
    df, desc, c1, dist = executar(data_dir)
    assert len(df) == 4 and len(c1) == 4
    for nome in ("rq01_rq04_descritivas.csv", "dora_c1.csv", "dora_c1_distribuicao.csv"):
        assert os.path.exists(os.path.join(data_dir, "analise", nome)), nome


def test_descritivas_cobrem_as_quatro_rqs_e_as_variantes(data_dir):
    _, desc, _, _ = executar(data_dir)
    metricas = set(desc["metrica"])
    for coluna, _, _ in METRICAS_C1.values():
        assert coluna in metricas, coluna
    for coluna in EXTRAS:
        assert coluna in metricas, coluna


def test_metricas_json_vazio_aborta(tmp_path):
    (tmp_path / "metricas.json").write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit):
        executar(str(tmp_path))
