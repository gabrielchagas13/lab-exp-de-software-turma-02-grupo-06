"""
Análise estatística de RQ1 (tempo) e RQ2 (defeitos) — issue #47.

Lê `data/trials.csv` (12 trials da Sprint 2) e aplica o teste de Wilcoxon
signed-rank pareado, conforme o desenho within-subject definido na issue #29.
As hipóteses H0/H1 não são redigitadas aqui: vêm de `hypotheses.py` (issue #27),
para que documento, script e relatório não divirjam.

Saídas:
  data/rq01_rq02_descritivas.csv  — mediana/IQR por tratamento
  data/rq01_rq02_pares.csv        — os pares (IA, Manual) por participante
  data/rq01_rq02_testes.csv       — estatística e p-valor de cada teste

Uso:
    python scripts/analyze_rq1_rq2.py
"""

import os
import sys
import warnings

import pandas as pd
from scipy.stats import wilcoxon, mannwhitneyu

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAB02_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(LAB02_DIR, "data")

sys.path.insert(0, SCRIPT_DIR)
from hypotheses import HYPOTHESES  # noqa: E402

TIME_BOX_SECONDS = 2100.0  # 35 min — valor de censura, fixado pelo enunciado
IA, MANUAL = "ia_total", "manual"


def load_trials() -> pd.DataFrame:
    """Carrega os trials e imputa o time-box nos censurados.

    Trial censurado tem `time_to_green_seconds` vazio: o participante não
    chegou ao verde dentro dos 35 min. O enunciado manda registrá-lo como
    censurado em 2100s e NÃO descartá-lo — descartar enviesaria a comparação
    a favor do tratamento com mais falhas, que é justamente o que se quer medir.
    O valor imputado é um piso (o tempo real seria >= 2100s), então a diferença
    entre tratamentos fica subestimada, nunca inflada."""
    df = pd.read_csv(os.path.join(DATA_DIR, "trials.csv"))
    df["censored"] = df["censored"].astype(str).str.lower() == "true"
    df["time_to_green_seconds"] = df["time_to_green_seconds"].fillna(TIME_BOX_SECONDS)
    return df


def check_design(df: pd.DataFrame) -> None:
    """Confere que os dados batem com o desenho antes de testar qualquer coisa."""
    problems = []
    if len(df) != 12:
        problems.append(f"esperados 12 trials, encontrados {len(df)}")

    by_treatment = df["treatment"].value_counts().to_dict()
    if by_treatment.get(IA) != 6 or by_treatment.get(MANUAL) != 6:
        problems.append(f"balanceamento esperado 6/6, encontrado {by_treatment}")

    for person, sub in df.groupby("participant"):
        counts = sub["treatment"].value_counts().to_dict()
        if counts.get(IA) != 2 or counts.get(MANUAL) != 2:
            problems.append(f"{person}: esperado 2 IA + 2 manual, encontrado {counts}")

    if problems:
        raise SystemExit("Dados inconsistentes com o desenho (issue #29):\n  - " + "\n  - ".join(problems))


def describe(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Mediana e IQR por tratamento.

    Mediana e IQR em vez de média e desvio-padrão porque N é pequeno (6 trials
    por tratamento) e há um valor censurado em 2100s que dominaria a média."""
    rows = []
    for treatment in (IA, MANUAL):
        values = df.loc[df["treatment"] == treatment, column]
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        rows.append({
            "metrica": column,
            "tratamento": treatment,
            "n": len(values),
            "mediana": round(values.median(), 2),
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "iqr": round(q3 - q1, 2),
            "min": round(values.min(), 2),
            "max": round(values.max(), 2),
        })
    return pd.DataFrame(rows)


def build_pairs(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Um par (IA, Manual) por participante — a unidade de pareamento.

    Cada integrante fez 2 katas em cada tratamento; a mediana desses 2 resume o
    participante naquele tratamento. É o pareamento definido no
    desenho_experimental.md: 'compara, por participante, a mediana IA vs. Manual
    — não compara kata a kata'. Isso é o que torna o teste within-subject: a
    variação individual de habilidade sai da comparação."""
    pares = (df.pivot_table(index="participant", columns="treatment", values=column, aggfunc="median")
               .reset_index())
    pares["diferenca_ia_menos_manual"] = (pares[IA] - pares[MANUAL]).round(2)
    return pares.round({IA: 2, MANUAL: 2})


def run_wilcoxon(pares: pd.DataFrame, alternative: str) -> dict:
    """Wilcoxon signed-rank pareado sobre os pares por participante."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            stat, p = wilcoxon(pares[IA], pares[MANUAL], alternative=alternative)
        except ValueError as exc:
            # scipy recusa quando todas as diferenças são zero
            return {"estatistica_W": None, "p_valor": 1.0, "observacao": f"teste não aplicável: {exc}"}
    return {"estatistica_W": float(stat), "p_valor": float(p), "observacao": ""}


def min_p_possivel(n_pares: int, alternative: str) -> float:
    """Menor p-valor que o Wilcoxon consegue produzir com n pares.

    Com n pares, existem 2^n combinações de sinais igualmente prováveis sob H0.
    O caso mais extremo (todas as diferenças no mesmo sentido) tem probabilidade
    1/2^n unilateral. Com n=3 isso dá 0,125 — ou seja, mesmo que o efeito seja
    enorme e perfeitamente consistente, o teste NÃO consegue chegar a p < 0,05.
    Reportar isso é obrigatório: sem esse número, um 'p = 0,125, não
    significativo' seria lido como 'não há efeito', quando na verdade significa
    'esta amostra não consegue detectar efeito nenhum'."""
    p = 1 / (2 ** n_pares)
    return p if alternative != "two-sided" else min(1.0, 2 * p)


def main() -> None:
    # O console do Windows abre em cp1252 e quebra em 'α'/'≠'/acentos.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    df = load_trials()
    check_design(df)

    h = {x.rq: x for x in HYPOTHESES}
    linhas_teste = []
    descritivas = []

    print("=" * 78)
    print("ANÁLISE ESTATÍSTICA — RQ1 e RQ2 (issue #47)")
    print("=" * 78)
    print(f"\n{len(df)} trials | {(df['treatment'] == IA).sum()} IA / {(df['treatment'] == MANUAL).sum()} manual "
          f"| {df['participant'].nunique()} participantes")
    censurados = df[df["censored"]]
    if len(censurados):
        print(f"Censurados (imputados em {TIME_BOX_SECONDS:.0f}s): {len(censurados)} — "
              + ", ".join(f"{r.participant}/{r.kata} ({r.treatment})" for r in censurados.itertuples()))

    # ---------------------------------------------------------------- RQ1
    print("\n" + "-" * 78)
    print(f"RQ1 — {h['RQ1'].question}")
    print("-" * 78)
    print(f"H0: {h['RQ1'].h0}")
    print(f"H1: {h['RQ1'].h1}")

    desc1 = describe(df, "time_to_green_seconds")
    descritivas.append(desc1)
    print("\nDescritivas (mediana e IQR, em segundos):")
    print(desc1.to_string(index=False))

    pares1 = build_pairs(df, "time_to_green_seconds")
    print("\nPares por participante (mediana de cada tratamento, em segundos):")
    print(pares1.to_string(index=False))

    # H1 é direcional ('menor no tratamento IA'), então o teste é unilateral.
    res1 = run_wilcoxon(pares1, alternative="less")
    n1 = len(pares1)
    piso1 = min_p_possivel(n1, "less")
    mediana_ia = desc1.loc[desc1.tratamento == IA, "mediana"].iloc[0]
    mediana_manual = desc1.loc[desc1.tratamento == MANUAL, "mediana"].iloc[0]

    print(f"\nWilcoxon signed-rank pareado, unilateral (H1: IA < manual), n = {n1} pares")
    print(f"  W = {res1['estatistica_W']}  |  p = {res1['p_valor']:.4f}")
    print(f"  menor p possível com n={n1}: {piso1:.4f}")
    print(f"  decisão a α=0,05: {'REJEITA H0' if res1['p_valor'] < 0.05 else 'NÃO rejeita H0'}")
    print(f"\n  Mediana IA {mediana_ia:.1f}s vs. manual {mediana_manual:.1f}s "
          f"({mediana_manual / mediana_ia:.1f}x) — todas as {n1} diferenças no mesmo sentido.")
    if piso1 >= 0.05:
        print(f"  ATENÇÃO: com n={n1}, nenhum resultado poderia ser significativo a α=0,05.")
        print("  O não-rejeitar aqui é falta de poder estatístico, não ausência de efeito.")

    linhas_teste.append({
        "rq": "RQ1", "metrica": "time_to_green_seconds", "teste": "Wilcoxon signed-rank pareado",
        "alternativa": "unilateral (IA < manual)", "n_pares": n1,
        "estatistica_W": res1["estatistica_W"], "p_valor": round(res1["p_valor"], 4),
        "menor_p_possivel": round(piso1, 4),
        "rejeita_h0_alpha_005": bool(res1["p_valor"] < 0.05),
        "mediana_ia": mediana_ia, "mediana_manual": mediana_manual,
    })

    # ---------------------------------------------------------------- RQ2
    print("\n" + "-" * 78)
    print(f"RQ2 — {h['RQ2'].question}")
    print("-" * 78)
    print(f"H0: {h['RQ2'].h0}")
    print(f"H1: {h['RQ2'].h1}")

    desc2 = describe(df, "success_rate")
    descritivas.append(desc2)
    print("\nDescritivas (taxa de sucesso = testes passando / total):")
    print(desc2.to_string(index=False))

    pares2 = build_pairs(df, "success_rate")
    print("\nPares por participante:")
    print(pares2.to_string(index=False))

    # H1 aqui não é direcional ('difere'), então o teste é bilateral.
    res2 = run_wilcoxon(pares2, alternative="two-sided")
    n2 = len(pares2)
    n_nao_nulas = int((pares2["diferenca_ia_menos_manual"] != 0).sum())
    piso2 = min_p_possivel(n2, "two-sided")

    print(f"\nWilcoxon signed-rank pareado, bilateral (H1: IA ≠ manual), n = {n2} pares")
    print(f"  W = {res2['estatistica_W']}  |  p = {res2['p_valor']:.4f}")
    if res2["observacao"]:
        print(f"  {res2['observacao']}")
    print(f"  diferenças não nulas: {n_nao_nulas} de {n2} "
          f"(o Wilcoxon descarta empates, então o n efetivo é {n_nao_nulas})")
    print(f"  decisão a α=0,05: {'REJEITA H0' if res2['p_valor'] < 0.05 else 'NÃO rejeita H0'}")

    ia_100 = int(((df.treatment == IA) & (df.success_rate == 1.0)).sum())
    man_100 = int(((df.treatment == MANUAL) & (df.success_rate == 1.0)).sum())
    print(f"\n  Trials com 100% dos testes passando: IA {ia_100}/6, manual {man_100}/6.")
    print("  O único trial abaixo de 100% é o censurado — ou seja, no tratamento manual")
    print("  a falha apareceu como 'não terminou no tempo', não como código errado.")

    linhas_teste.append({
        "rq": "RQ2", "metrica": "success_rate", "teste": "Wilcoxon signed-rank pareado",
        "alternativa": "bilateral (IA ≠ manual)", "n_pares": n2,
        "estatistica_W": res2["estatistica_W"], "p_valor": round(res2["p_valor"], 4),
        "menor_p_possivel": round(piso2, 4),
        "rejeita_h0_alpha_005": bool(res2["p_valor"] < 0.05),
        "mediana_ia": desc2.loc[desc2.tratamento == IA, "mediana"].iloc[0],
        "mediana_manual": desc2.loc[desc2.tratamento == MANUAL, "mediana"].iloc[0],
    })

    # ------------------------------------------------- exploratório (não é o teste primário)
    print("\n" + "-" * 78)
    print("EXPLORATÓRIO — Mann-Whitney por trial (NÃO é o teste primário)")
    print("-" * 78)
    print("O teste pareado acima segue o desenho within-subject e é o que responde as RQs.")
    print("Abaixo, os 12 trials tratados como amostras independentes: ignora o pareamento")
    print("(e portanto a variação individual), mas usa 12 pontos em vez de 3, o que dá")
    print("poder para detectar o efeito. Serve só para mostrar que o não-rejeitar do")
    print("Wilcoxon vem do tamanho da amostra, não da ausência de diferença.")

    t_ia = df.loc[df.treatment == IA, "time_to_green_seconds"]
    t_man = df.loc[df.treatment == MANUAL, "time_to_green_seconds"]
    u_stat, u_p = mannwhitneyu(t_ia, t_man, alternative="less")
    print(f"\n  tempo: U = {u_stat:.1f} | p = {u_p:.4f} (unilateral, 6 vs 6) — "
          f"{'significativo' if u_p < 0.05 else 'não significativo'} a α=0,05")

    linhas_teste.append({
        "rq": "RQ1", "metrica": "time_to_green_seconds", "teste": "Mann-Whitney U (exploratório, não pareado)",
        "alternativa": "unilateral (IA < manual)", "n_pares": len(t_ia) + len(t_man),
        "estatistica_W": float(u_stat), "p_valor": round(float(u_p), 4),
        "menor_p_possivel": None, "rejeita_h0_alpha_005": bool(u_p < 0.05),
        "mediana_ia": mediana_ia, "mediana_manual": mediana_manual,
    })

    # ---------------------------------------------------------------- saídas
    pd.concat(descritivas).to_csv(os.path.join(DATA_DIR, "rq01_rq02_descritivas.csv"), index=False)
    pares1.assign(metrica="time_to_green_seconds").to_csv(
        os.path.join(DATA_DIR, "rq01_rq02_pares.csv"), index=False)
    pd.DataFrame(linhas_teste).to_csv(os.path.join(DATA_DIR, "rq01_rq02_testes.csv"), index=False)

    print("\n" + "=" * 78)
    print("Arquivos gerados em data/: rq01_rq02_descritivas.csv, rq01_rq02_pares.csv, rq01_rq02_testes.csv")
    print("=" * 78)


if __name__ == "__main__":
    main()
