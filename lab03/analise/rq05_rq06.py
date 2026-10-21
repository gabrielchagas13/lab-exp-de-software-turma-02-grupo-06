"""RQ 05 (Spearman: frequência de deploy x CFR) e RQ 06 (fatores associados ao CFR), issue #72.

Lê `data/dataset.csv` e grava em `data/analise/`:
  rq05_spearman.csv           rho, p-valor e n, por variante de CFR
  rq05_dispersao_<cfr>.png    dispersão (x em escala log, y symlog, pois o CFR pode ser 0)
  rq06_fatores.csv            teste, p-valor, p ajustado (Holm) e tamanho de efeito

RQ 06: fatores (linguagem, estrelas, contribuidores, idade) x métricas DORA das RQ 01 a 04. Fatores
numéricos viram quartis (Q1 a Q4); linguagens com menos de MIN_GRUPO repositórios viram "outros".
Kruskal-Wallis com ε² = H / (n − 1); com só 2 grupos, Mann-Whitney e delta de Cliff. Todos os
testes formam uma única família corrigida por Holm.

Uso:
    python -m analise.rq05_rq06 --config config.json
"""
import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import ScalarFormatter  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from statsmodels.stats.multitest import multipletests  # noqa: E402

X = "releases_por_semana"
CFRS = ["cfr_ci", "cfr_entrega_v1_semver", "cfr_entrega_v2_semver_ou_nome",
        "cfr_entrega_v3_commits", "cfr_entrega_v4_combinada"]
METRICAS = ["releases_por_semana", "lead_time_release_h", "lead_time_commit_h", *CFRS, "recovery_median_h"]
CATEGORICOS = ["language"]
NUMERICOS = ["stars", "contributors", "age_years"]
MIN_GRUPO = 10


def epsilon_squared(h, n):
    """ε² do Kruskal-Wallis, como no enunciado: H / (n − 1)."""
    return h / (n - 1)


def cliffs_delta(a, b):
    """δ de Cliff = 2U/(n1·n2) − 1, em [−1, 1]; positivo quando `a` tende a ser maior que `b`."""
    return 2 * stats.mannwhitneyu(a, b).statistic / (len(a) * len(b)) - 1


def rq05(df, out_dir):
    linhas = []
    for cfr in CFRS:
        sub = df[[X, cfr]].dropna()
        rho, p = stats.spearmanr(sub[X], sub[cfr])
        linhas.append({"cfr": cfr, "n": len(sub), "rho": rho, "p_value": p})
        sub = sub[sub[X] > 0]  # log não admite x <= 0
        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.scatter(sub[X], sub[cfr], s=14, alpha=0.6)
        ax.set(xscale="log", yscale="symlog", xlabel="releases por semana (log)",
               ylabel=f"{cfr} (symlog)", ylim=(0, None))
        ax.yaxis.set_major_formatter(ScalarFormatter())
        fig.savefig(os.path.join(out_dir, f"rq05_dispersao_{cfr}.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)
    return pd.DataFrame(linhas)


def comparar(df, metrica, fator, numerico):
    """Testa um fator contra uma métrica; None se sobram menos de 2 grupos."""
    sub = df[[metrica, fator]].dropna().copy()
    if numerico:
        sub[fator] = pd.qcut(sub[fator], 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop")
    else:
        pequenos = sub[fator].value_counts().loc[lambda c: c < MIN_GRUPO].index
        sub[fator] = sub[fator].where(~sub[fator].isin(pequenos), "outros")
    grupos = [g[metrica].to_numpy() for _, g in sub.groupby(fator, observed=True)]
    if len(grupos) < 2:
        return None
    base = {"metrica": metrica, "fator": fator, "n": len(sub), "grupos": len(grupos)}
    if len(grupos) == 2:
        res = stats.mannwhitneyu(*grupos)
        return {**base, "teste": "Mann-Whitney", "p_value": res.pvalue,
                "efeito": "cliffs_delta", "tamanho_efeito": cliffs_delta(*grupos)}
    res = stats.kruskal(*grupos)
    return {**base, "teste": "Kruskal-Wallis", "p_value": res.pvalue,
            "efeito": "epsilon2", "tamanho_efeito": epsilon_squared(res.statistic, len(sub))}


def rq06(df):
    linhas = [comparar(df, metrica, f, numerico)
              for metrica in METRICAS
              for fatores, numerico in ((CATEGORICOS, False), (NUMERICOS, True))
              for f in fatores]
    resultado = pd.DataFrame([r for r in linhas if r])
    resultado["p_holm"] = multipletests(resultado["p_value"], method="holm")[1]
    resultado["significativo"] = resultado["p_holm"] < 0.05
    return resultado


def main(argv=None):
    parser = argparse.ArgumentParser(prog="analise.rq05_rq06", description=__doc__.split("\n")[0])
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]
    out_dir = os.path.join(data_dir, "analise")
    os.makedirs(out_dir, exist_ok=True)

    df = pd.read_csv(os.path.join(data_dir, "dataset.csv"))
    r5, r6 = rq05(df, out_dir), rq06(df)
    r5.to_csv(os.path.join(out_dir, "rq05_spearman.csv"), index=False)
    r6.to_csv(os.path.join(out_dir, "rq06_fatores.csv"), index=False)
    print(r5.to_string(index=False), r6.to_string(index=False), sep="\n\n")


if __name__ == "__main__":
    main()
