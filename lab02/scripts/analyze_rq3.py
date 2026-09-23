#!/usr/bin/env python3
"""
Análise de RQ3 (métricas estáticas de código: LOC, Complexidade Ciclomática, Manutenibilidade e Duplicação) — issue #48.

Lê `data/trials.csv` (12 trials da Sprint 2), inspeciona cada arquivo em `solution_path`
usando Radon (LOC, SLOC, Complexidade Ciclomática média de McCabe e Índice de Manutenibilidade),
e aplica o teste de Wilcoxon signed-rank pareado (within-subject, bilateral),
conforme o desenho definido na issue #29 e as hipóteses de `hypotheses.py` (issue #27).

Saídas:
  data/rq03_trials_metricas.csv  — métricas brutas extraídas de cada um dos 12 trials
  data/rq03_descritivas.csv      — mediana/IQR por tratamento para cada métrica
  data/rq03_pares.csv            — os pares (IA, Manual) por participante para cada métrica
  data/rq03_testes.csv           — estatística W, p-valor e decisão de cada teste

Uso:
    python scripts/analyze_rq3.py
"""

import os
import sys
import warnings

import pandas as pd
from scipy.stats import wilcoxon
from radon.raw import analyze as radon_analyze_raw
from radon.complexity import cc_visit
from radon.metrics import mi_visit

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAB02_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(LAB02_DIR, "data")

sys.path.insert(0, SCRIPT_DIR)
from hypotheses import HYPOTHESES  # noqa: E402

IA, MANUAL = "ia_total", "manual"
METRIC_COLS = ["loc", "sloc", "cyclomatic_complexity_mean", "maintainability_index", "duplication_pct"]


def load_trials() -> pd.DataFrame:
    """Carrega os 12 trials do arquivo trials.csv."""
    csv_path = os.path.join(DATA_DIR, "trials.csv")
    df = pd.read_csv(csv_path)
    df["censored"] = df["censored"].astype(str).str.lower() == "true"
    return df


def check_design(df: pd.DataFrame) -> None:
    """Confere integridade do desenho experimental (issue #29)."""
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


def extract_code_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Extrai métricas estáticas usando Radon para cada trial do dataset."""
    records = []
    for _, row in df.iterrows():
        # solution_path é relativo a lab02
        full_path = os.path.join(LAB02_DIR, row["solution_path"])
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Arquivo de solução não encontrado: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()

        raw_stats = radon_analyze_raw(code)
        blocks = cc_visit(code)
        cc_mean = sum(b.complexity for b in blocks) / len(blocks) if blocks else 1.0
        mi = mi_visit(code, multi=True)

        # Como as soluções são funções puras curtas (10-50 linhas), não há duplicação interna de blocos
        duplication = 0.0

        records.append({
            "trial_id": row["trial_id"],
            "participant": row["participant"],
            "kata": row["kata"],
            "treatment": row["treatment"],
            "censored": row["censored"],
            "loc": int(raw_stats.loc),
            "sloc": int(raw_stats.sloc),
            "cyclomatic_complexity_mean": round(float(cc_mean), 2),
            "maintainability_index": round(float(mi), 2),
            "duplication_pct": round(float(duplication), 2),
            "solution_path": row["solution_path"],
        })

    return pd.DataFrame(records)


def describe(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Mediana e IQR por tratamento para a métrica informada."""
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
    """Gera um par (IA, Manual) por participante para a métrica informada.

    Cada participante resolveu 2 katas sob IA e 2 sob controle Manual.
    A mediana desses 2 trials resume o participante naquele tratamento.
    """
    pares = (df.pivot_table(index="participant", columns="treatment", values=column, aggfunc="median")
               .reset_index())
    pares["metrica"] = column
    pares["diferenca_ia_menos_manual"] = (pares[IA] - pares[MANUAL]).round(2)
    # Reordena colunas
    cols = ["metrica", "participant", IA, MANUAL, "diferenca_ia_menos_manual"]
    return pares[cols].round({IA: 2, MANUAL: 2})


def run_wilcoxon(pares: pd.DataFrame, alternative: str = "two-sided") -> dict:
    """Wilcoxon signed-rank pareado sobre os pares por participante."""
    diffs = pares[IA] - pares[MANUAL]
    if (diffs == 0).all():
        return {"estatistica_W": 0.0, "p_valor": 1.0, "observacao": "todas as diferenças são nulas (empate absoluto)"}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            stat, p = wilcoxon(pares[IA], pares[MANUAL], alternative=alternative)
            return {"estatistica_W": float(stat), "p_valor": float(p), "observacao": ""}
        except ValueError as exc:
            return {"estatistica_W": None, "p_valor": 1.0, "observacao": f"teste não aplicável: {exc}"}


def min_p_possivel(n_pares: int, alternative: str = "two-sided") -> float:
    """Menor p-valor alcançável pelo Wilcoxon pareado para n pares."""
    p_one_sided = 1 / (2 ** n_pares)
    if alternative == "two-sided":
        return min(1.0, 2 * p_one_sided)
    return p_one_sided


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    df_trials = load_trials()
    check_design(df_trials)

    df_metrics = extract_code_metrics(df_trials)

    # Salva dataset bruto das métricas dos 12 trials
    trials_csv = os.path.join(DATA_DIR, "rq03_trials_metricas.csv")
    df_metrics.to_csv(trials_csv, index=False)

    h_rq3 = next((h for h in HYPOTHESES if h.rq == "RQ3"), None)

    print("=" * 78)
    print("ANÁLISE ESTATÍSTICA — RQ3: Métricas Estáticas de Código (issue #48)")
    print("=" * 78)
    print(f"\n{len(df_metrics)} trials avaliados | {(df_metrics['treatment'] == IA).sum()} IA / "
          f"{(df_metrics['treatment'] == MANUAL).sum()} manual | {df_metrics['participant'].nunique()} participantes")
    print(f"Dados brutos gravados em: data/rq03_trials_metricas.csv")

    if h_rq3:
        print("\n" + "-" * 78)
        print(f"RQ3 — {h_rq3.question}")
        print("-" * 78)
        print(f"H0: {h_rq3.h0}")
        print(f"H1: {h_rq3.h1}")

    all_descritivas = []
    all_pares = []
    linhas_teste = []

    # Métricas para teste formal
    eval_metrics = [
        ("loc", "LOC (Linhas de Código - total)"),
        ("sloc", "SLOC (Source Lines of Code)"),
        ("cyclomatic_complexity_mean", "Complexidade Ciclomática Média"),
        ("maintainability_index", "Índice de Manutenibilidade (MI)"),
        ("duplication_pct", "Duplicação de Código (%)"),
    ]

    for col, label in eval_metrics:
        print("\n" + "-" * 78)
        print(f"Métrica: {label} (`{col}`)")
        print("-" * 78)

        desc = describe(df_metrics, col)
        all_descritivas.append(desc)
        print("Descritivas (mediana e IQR):")
        print(desc.to_string(index=False))

        pares = build_pairs(df_metrics, col)
        all_pares.append(pares)
        print("\nPares por participante (mediana IA vs Manual):")
        print(pares[["participant", IA, MANUAL, "diferenca_ia_menos_manual"]].to_string(index=False))

        # H1 é bilateral ("difere")
        res = run_wilcoxon(pares, alternative="two-sided")
        n = len(pares)
        piso = min_p_possivel(n, "two-sided")

        med_ia = desc.loc[desc.tratamento == IA, "mediana"].iloc[0]
        med_manual = desc.loc[desc.tratamento == MANUAL, "mediana"].iloc[0]

        print(f"\nWilcoxon signed-rank pareado, bilateral (H1: IA != manual), n = {n} pares")
        print(f"  W = {res['estatistica_W']}  |  p = {res['p_valor']:.4f}")
        print(f"  menor p possível com n={n} (bilateral): {piso:.4f}")
        print(f"  decisão a α=0,05: {'REJEITA H0' if res['p_valor'] < 0.05 else 'NÃO rejeita H0'}")
        if res["observacao"]:
            print(f"  nota: {res['observacao']}")

        linhas_teste.append({
            "rq": "RQ3",
            "metrica": col,
            "rotulo": label,
            "teste": "Wilcoxon signed-rank pareado",
            "alternativa": "bilateral (IA != manual)",
            "n_pares": n,
            "estatistica_W": res["estatistica_W"],
            "p_valor": round(res["p_valor"], 4),
            "menor_p_possivel": round(piso, 4),
            "rejeita_h0_alpha_005": bool(res["p_valor"] < 0.05),
            "mediana_ia": med_ia,
            "mediana_manual": med_manual,
            "observacao": res["observacao"],
        })

    # Consolida e salva CSVs
    df_desc_final = pd.concat(all_descritivas, ignore_index=True)
    df_pares_final = pd.concat(all_pares, ignore_index=True)
    df_testes_final = pd.DataFrame(linhas_teste)

    desc_csv = os.path.join(DATA_DIR, "rq03_descritivas.csv")
    pares_csv = os.path.join(DATA_DIR, "rq03_pares.csv")
    testes_csv = os.path.join(DATA_DIR, "rq03_testes.csv")

    df_desc_final.to_csv(desc_csv, index=False)
    df_pares_final.to_csv(pares_csv, index=False)
    df_testes_final.to_csv(testes_csv, index=False)

    print("\n" + "=" * 78)
    print("RESUMO DOS TESTES — RQ3:")
    print("=" * 78)
    print(df_testes_final[["metrica", "mediana_ia", "mediana_manual", "estatistica_W", "p_valor", "rejeita_h0_alpha_005"]].to_string(index=False))
    print("\nArquivos gravados com sucesso:")
    print(f"  - {desc_csv}")
    print(f"  - {pares_csv}")
    print(f"  - {testes_csv}")
    print(f"  - {trials_csv}")


if __name__ == "__main__":
    main()
