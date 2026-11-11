"""Gera painel/index.html a partir de painel/template.html.

Uso: python -m painel [--reps 10000]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

import sim
from simulacao.cenario import PREVISOES, RECOMENDACAO

AQUI = Path(__file__).resolve().parent


def payload(reps):
    df = sim.carregar_reais()
    aj = sim.ajustar_lognormal(df)
    med, sig = sim.parametros_base(df)
    res = sim.simular_tudo(reps=reps)
    grade = sim.poder_por_n(reps=reps)
    x = df.loc[df.grupo == "com_bot", "horas_ate_merge"].to_numpy()
    y = df.loc[df.grupo == "sem_bot", "horas_ate_merge"].to_numpy()
    w = stats.ttest_ind(x, y, equal_var=False)
    m = stats.mannwhitneyu(x, y, alternative="two-sided")
    reais = sim.testes_reais(df)
    return {
        "reps": reps,
        "previsoes": PREVISOES,
        "recomendacao": RECOMENDACAO,
        "seed": sim.SEED,
        "pontos": df[["grupo", "numero", "autor", "horas_ate_merge", "url"]]
        .rename(columns={"horas_ate_merge": "h"}).to_dict("records"),
        "ajuste": {g: {"mediana": a.mediana, "sigma": a.sigma} for g, a in aj.items()},
        "base": {"mediana": med, "sigma": sig},
        "cenarios": {k: v for k, v in sim.CENARIOS.items()},
        "sim": res.to_dict("records"),
        "grade": grade.to_dict("records"),
        "reais": {
            "welch": {"t": float(w.statistic), "df": float(w.df), "p": float(w.pvalue),
                      "d": sim.cohen_d(x, y)},
            "mw": {"U": float(m.statistic), "p": float(m.pvalue), "delta": sim.cliff_delta(x, y)},
            "razao": float(np.median(x) / np.median(y)),
            "mediana": {"com_bot": float(np.median(x)), "sem_bot": float(np.median(y))},
            "media": {"com_bot": float(x.mean()), "sem_bot": float(y.mean())},
            "tabela": reais.to_dict("records"),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10_000)
    reps = ap.parse_args().reps
    dados = payload(reps)
    tpl = (AQUI / "template.html").read_text(encoding="utf-8")
    html = tpl.replace("/*__DATA__*/null", json.dumps(dados, ensure_ascii=False))
    (AQUI / "index.html").write_text(html, encoding="utf-8")
    import pandas as pd
    pd.DataFrame(dados["sim"]).to_csv(AQUI.parent / "data" / "simulacao.csv", index=False)
    pd.DataFrame(dados["grade"]).to_csv(AQUI.parent / "data" / "poder_por_n.csv", index=False)
    print("ok:", AQUI / "index.html")


if __name__ == "__main__":
    main()
