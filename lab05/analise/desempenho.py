"""RQ2: o sistema é rápido no celular? (H2: LCP celular > LCP computador)

Descritiva (mediana, IQR) por página e perfil, e Wilcoxon pareado
celular-4G × computador, pareando (página, repetição). Tamanho do efeito:
r = Z / sqrt(n) e delta de Cliff. Também compara 3G × 4G no celular.

    python -m analise.desempenho      # imprime e salva data/lighthouse/resumo_desempenho.csv

Com 5 páginas × 5 repetições temos n = 25 pares; as repetições da mesma
página não são independentes, então o teste é complementado pela comparação
das medianas por página (n = 5, todas na mesma direção ou não).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA = Path(__file__).resolve().parent.parent / "data" / "lighthouse"
LIMIAR_LCP_BOM_MS = 2500  # Core Web Vitals: "bom" <= 2,5 s


def carregar() -> pd.DataFrame:
    df = pd.read_csv(DATA / "resultados.csv")
    df = df[(df["erro"].astype("string").fillna("") == "") & (df["repeticao"] > 0)].copy()
    df["perfil"] = np.where(df["dispositivo"] == "desktop", "desktop", "mobile_" + df["rede"].astype(str))
    return df


def descritiva(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["pagina", "perfil"])
    out = g.agg(n=("lcp_ms", "size"),
                lcp_mediana_ms=("lcp_ms", "median"),
                lcp_q1_ms=("lcp_ms", lambda s: s.quantile(.25)),
                lcp_q3_ms=("lcp_ms", lambda s: s.quantile(.75)),
                perf_mediana=("nota_performance", "median"),
                acess_mediana=("nota_acessibilidade", "median"),
                peso_kb_mediana=("peso_total_kb", "median")).reset_index()
    out["lcp_bom"] = out["lcp_mediana_ms"] <= LIMIAR_LCP_BOM_MS
    return out.round(1)


def cliff_delta(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    maior = (a[:, None] > b[None, :]).sum()
    menor = (a[:, None] < b[None, :]).sum()
    return (maior - menor) / (len(a) * len(b))


def magnitude_cliff(d: float) -> str:
    d = abs(d)
    return "desprezível" if d < .147 else "pequeno" if d < .33 else "médio" if d < .474 else "grande"


def comparar(df: pd.DataFrame, perfil_a: str, perfil_b: str, metrica: str = "lcp_ms") -> dict:
    """Wilcoxon pareado (a > b, unilateral) pareando por (página, repetição)."""
    a = df[df["perfil"] == perfil_a].set_index(["pagina", "repeticao"])[metrica]
    b = df[df["perfil"] == perfil_b].set_index(["pagina", "repeticao"])[metrica]
    pares = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    n = len(pares)
    if n < 2:
        return {"comparacao": f"{perfil_a} × {perfil_b}", "n_pares": n}
    w = stats.wilcoxon(pares["a"], pares["b"], alternative="greater", method="approx")
    z = stats.norm.isf(w.pvalue)
    d = cliff_delta(pares["a"], pares["b"])
    med_pag = pares.groupby(level=0).median()
    return {
        "comparacao": f"{perfil_a} × {perfil_b}", "metrica": metrica, "n_pares": n,
        "mediana_a": round(pares["a"].median(), 1), "mediana_b": round(pares["b"].median(), 1),
        "razao_medianas": round(pares["a"].median() / pares["b"].median(), 2),
        "W": w.statistic, "p_valor": float(f"{w.pvalue:.3g}"),
        "r": round(z / np.sqrt(n), 2), "cliff_delta": round(d, 2), "magnitude": magnitude_cliff(d),
        "paginas_na_direcao": f"{int((med_pag['a'] > med_pag['b']).sum())}/{len(med_pag)}",
    }


def main() -> None:
    df = carregar()
    desc = descritiva(df)
    print(desc.to_string(index=False))
    testes = pd.DataFrame([
        comparar(df, "mobile_4g", "desktop"),
        comparar(df, "mobile_3g", "mobile_4g"),
    ])
    print()
    print(testes.to_string(index=False))
    desc.to_csv(DATA / "resumo_desempenho.csv", index=False)
    testes.to_csv(DATA / "testes_desempenho.csv", index=False)


if __name__ == "__main__":
    main()
