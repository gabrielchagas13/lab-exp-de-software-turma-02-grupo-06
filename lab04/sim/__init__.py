"""Simulação Welch × Mann-Whitney para tempo até o merge (horas).

Modelo: lognormal. O efeito é a razão de medianas (com_bot / sem_bot).
Tudo é vetorizado (réplicas nas linhas) e reprodutível via `rng`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05
SEED = 42
DADOS_REAIS = Path(__file__).resolve().parent.parent / "data" / "real.csv"


def carregar_reais(caminho: Path = DADOS_REAIS) -> pd.DataFrame:
    return pd.read_csv(caminho)


@dataclass(frozen=True)
class Ajuste:
    mediana: float  # exp(mu)
    sigma: float  # desvio-padrão de log(x)


def ajustar_lognormal(df: pd.DataFrame) -> dict[str, Ajuste]:
    """Ajuste por máxima verossimilhança (média e dp de log x) por grupo."""
    out = {}
    for g, sub in df.groupby("grupo"):
        lx = np.log(sub["horas_ate_merge"].clip(lower=1e-3))
        out[g] = Ajuste(mediana=float(np.exp(lx.mean())), sigma=float(lx.std(ddof=1)))
    return out


def parametros_base(df: pd.DataFrame | None = None) -> tuple[float, float]:
    """Mediana do grupo sem_bot e sigma combinado (log) dos dois grupos."""
    aj = ajustar_lognormal(carregar_reais() if df is None else df)
    sigma = float(np.sqrt((aj["com_bot"].sigma ** 2 + aj["sem_bot"].sigma ** 2) / 2))
    return aj["sem_bot"].mediana, sigma


# Cenários: "base" respeita o ajuste; os demais violam pressupostos do teste t (Q3).
CENARIOS = {
    "base": {"rotulo": "Base (ajuste real, n=30)", "n": 30, "fator_sigma": 1.0, "outliers": 0.0},
    "sigma_alto": {"rotulo": "Assimetria forte (σ×1,5)", "n": 30, "fator_sigma": 1.5, "outliers": 0.0},
    "outliers": {"rotulo": "Outliers (10% ×20)", "n": 30, "fator_sigma": 1.0, "outliers": 0.10},
    "n_pequeno": {"rotulo": "Amostra pequena (n=10)", "n": 10, "fator_sigma": 1.0, "outliers": 0.0},
}


def gerar_dados(n, efeito, cenario, rng, reps=1, mediana=None, sigma=None):
    """Retorna (a, b) com shape (reps, n): a = sem_bot, b = com_bot.

    `efeito` = razão de medianas b/a (1,0 → H0 verdadeira).
    """
    if mediana is None or sigma is None:
        mediana, sigma = parametros_base()
    c = CENARIOS[cenario]
    s = sigma * c["fator_sigma"]
    a = rng.lognormal(np.log(mediana), s, size=(reps, n))
    b = rng.lognormal(np.log(mediana * efeito), s, size=(reps, n))
    if c["outliers"] > 0:
        for x in (a, b):
            m = rng.random(x.shape) < c["outliers"]
            x[m] *= 20
    return a, b


def aplicar_testes(a, b):
    """p-valores (bicaudais) de Welch e Mann-Whitney, vetorizados por linha."""
    pw = stats.ttest_ind(a, b, axis=-1, equal_var=False).pvalue
    pm = stats.mannwhitneyu(a, b, axis=-1, alternative="two-sided", method="asymptotic").pvalue
    return {"welch": pw, "mann_whitney": pm}


def ic_proporcao(k, n, conf=0.95):
    """IC de Wilson."""
    z = stats.norm.ppf(1 - (1 - conf) / 2)
    p = k / n
    den = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / den
    meia = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return centro - meia, centro + meia


def taxa_rejeicao(efeito, cenario, reps=10_000, rng=None, n=None, mediana=None, sigma=None):
    """Proporção de p<α para cada teste (= erro tipo I se efeito=1, poder caso contrário)."""
    rng = np.random.default_rng(SEED) if rng is None else rng
    n = CENARIOS[cenario]["n"] if n is None else n
    a, b = gerar_dados(n, efeito, cenario, rng, reps, mediana, sigma)
    out = {}
    for teste, p in aplicar_testes(a, b).items():
        k = int((p < ALPHA).sum())
        lo, hi = ic_proporcao(k, reps)
        out[teste] = {"taxa": k / reps, "ic_inf": lo, "ic_sup": hi}
    return out


EFEITOS = [1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]


def simular_tudo(reps=10_000, efeitos=EFEITOS, seed=SEED) -> pd.DataFrame:
    """Q1 (efeito=1), Q2 (efeitos>1) e Q3 (cenários) em uma tabela longa."""
    mediana, sigma = parametros_base()
    linhas = []
    for i, cen in enumerate(CENARIOS):
        for j, ef in enumerate(efeitos):
            rng = np.random.default_rng([seed, i, j])
            for teste, r in taxa_rejeicao(ef, cen, reps, rng, mediana=mediana, sigma=sigma).items():
                linhas.append({"cenario": cen, "efeito": ef, "teste": teste, **r})
    return pd.DataFrame(linhas)


# ---------- Seção 6: dados reais ----------

def cliff_delta(x, y):
    x, y = np.asarray(x), np.asarray(y)
    d = np.sign(x[:, None] - y[None, :])
    return float(d.mean())


def cohen_d(x, y):
    x, y = np.asarray(x), np.asarray(y)
    sp = np.sqrt((x.var(ddof=1) + y.var(ddof=1)) / 2)
    return float((x.mean() - y.mean()) / sp)


def testes_reais(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = carregar_reais() if df is None else df
    x = df.loc[df.grupo == "com_bot", "horas_ate_merge"].to_numpy()
    y = df.loc[df.grupo == "sem_bot", "horas_ate_merge"].to_numpy()
    w = stats.ttest_ind(x, y, equal_var=False)
    m = stats.mannwhitneyu(x, y, alternative="two-sided")
    razao = float(np.median(x) / np.median(y))

    def concl(p):
        return "Rejeita H0" if p < ALPHA else "Não rejeita H0"

    return pd.DataFrame([
        {"teste": "t de Welch", "estatistica": f"t = {w.statistic:.3f} (gl = {w.df:.1f})",
         "p": float(w.pvalue), "efeito": f"Cohen d = {cohen_d(x, y):.2f}", "conclusao": concl(w.pvalue)},
        {"teste": "Mann-Whitney", "estatistica": f"U = {m.statistic:.0f}",
         "p": float(m.pvalue), "efeito": f"Cliff δ = {cliff_delta(x, y):.2f}; razão de medianas = {razao:.2f}",
         "conclusao": concl(m.pvalue)},
    ])


def poder_por_n(ns=(10, 20, 30, 50, 80, 120), efeitos=(1.5, 2.0, 3.0, 4.0, 6.0), reps=10_000, seed=SEED):
    """Poder no cenário base em uma grade n × razão de medianas (discussão de tamanho de amostra)."""
    mediana, sigma = parametros_base()
    linhas = []
    for i, n in enumerate(ns):
        for j, ef in enumerate(efeitos):
            rng = np.random.default_rng([seed, 99, i, j])
            for teste, r in taxa_rejeicao(ef, "base", reps, rng, n=n, mediana=mediana, sigma=sigma).items():
                linhas.append({"n": n, "efeito": ef, "teste": teste, **r})
    return pd.DataFrame(linhas)
