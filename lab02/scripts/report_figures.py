"""
Figuras do Relatorio Final do Lab02 (secao 4.2).

Le os CSVs gerados pela coleta (data/trials.csv) e pelas analises da Sprint 3
(analyze_rq1_rq2.py, analyze_rq3.py) e grava PNGs em docs/img/. Nao recalcula
nenhum teste estatistico: os numeros vem dos CSVs ja versionados.

Uso (a partir de lab02/):
    python scripts/report_figures.py
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

LAB02_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(LAB02_DIR, "data")
IMG_DIR = os.path.join(LAB02_DIR, "docs", "img")

TIME_BOX_SECONDS = 2100
IA, MANUAL = "ia_total", "manual"
LABEL = {IA: "Geração integral por IA", MANUAL: "Manual"}
COLOR = {IA: "#2a78d6", MANUAL: "#eb6834"}
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SHORT = {"gabrielchagas13": "Gabriel", "gguilhermelana": "Guilherme", "marcusvv12": "Marcus"}
KATA_LABEL = {
    "01_gastos_semanais": "01 Gastos\nsemanais",
    "02_normalizador_tags": "02 Normalizador\nde tags",
    "03_escalonador_tarefas": "03 Escalonador\nde tarefas",
    "04_clusters_anagramas": "04 Clusters de\nanagramas",
}

# Deslocamento vertical (pt) dos rotulos de participantes que ficariam sobrepostos.
LABEL_NUDGE = {"marcusvv12": 5, "gguilhermelana": -5}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "legend.frameon": False,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "figure.facecolor": "white",
})


def load_trials() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "trials.csv"))
    df["censored"] = df["censored"].astype(str).str.lower() == "true"
    # Mesma regra de analyze_rq1_rq2.py: censurado entra como 2100s, nao e descartado.
    df["time"] = df["time_to_green_seconds"].fillna(TIME_BOX_SECONDS)
    df.loc[df["censored"], "time"] = TIME_BOX_SECONDS
    return df


def fmt_seconds(value: float) -> str:
    return f"{value:,.1f} s".replace(",", "X").replace(".", ",").replace("X", ".")


def fig_rq1(df: pd.DataFrame) -> None:
    pairs = pd.read_csv(os.path.join(DATA_DIR, "rq01_rq02_pares.csv"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1.1, 1]})

    for x, treatment in enumerate((IA, MANUAL)):
        sub = df[df["treatment"] == treatment].sort_values("time")
        offsets = [(-0.12, -0.04, 0.04, 0.12, -0.08, 0.08)[i % 6] for i in range(len(sub))]
        for off, (_, row) in zip(offsets, sub.iterrows()):
            ax1.scatter(x + off, row["time"], s=48, zorder=3,
                        facecolor="white" if row["censored"] else COLOR[treatment],
                        edgecolor=COLOR[treatment], linewidth=1.6)
        median = sub["time"].median()
        ax1.hlines(median, x - 0.28, x + 0.28, color=INK, linewidth=2, zorder=4)
        ax1.annotate(f"mediana {fmt_seconds(median)}", (x + 0.3, median), va="center",
                     fontsize=9, color=INK)
    censored = df[df["censored"]].iloc[0]
    ax1.annotate("censurado no time-box\n(real ≥ 2.100 s)", (1 - 0.12, censored["time"]),
                 xytext=(-0.05, 1300), fontsize=8.5, color=INK_2,
                 arrowprops={"arrowstyle": "-", "color": INK_2, "linewidth": 0.8})
    ax1.set_yscale("log")
    ax1.set_xticks([0, 1], [LABEL[IA], LABEL[MANUAL]])
    ax1.set_xlim(-0.5, 1.9)
    ax1.set_ylabel("Time-to-green (segundos, escala log)")
    ax1.set_title("(a) Os 12 trials")
    ax1.grid(axis="x", visible=False)

    for _, row in pairs.iterrows():
        ax2.plot([0, 1], [row["ia_total"], row["manual"]], color=INK_2, linewidth=1.5, zorder=2)
        ax2.scatter([0], [row["ia_total"]], s=60, color=COLOR[IA], edgecolor="white", linewidth=2, zorder=3)
        ax2.scatter([1], [row["manual"]], s=60, color=COLOR[MANUAL], edgecolor="white", linewidth=2, zorder=3)
        ax2.annotate(SHORT[row["participant"]], (1.04, row["manual"]), va="center", fontsize=9, color=INK,
                     xytext=(0, LABEL_NUDGE.get(row["participant"], 0)), textcoords="offset points")
    ax2.set_yscale("log")
    ax2.set_xticks([0, 1], ["IA", "Manual"])
    ax2.set_xlim(-0.3, 1.45)
    ax2.set_ylabel("Mediana do participante (s, log)")
    ax2.set_title("(b) Pares within-subject (n = 3)")
    ax2.grid(axis="x", visible=False)

    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "rq1_tempo.png"))
    plt.close(fig)


def fig_rq2(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 2.6))
    for y, treatment in enumerate((MANUAL, IA)):
        sub = df[df["treatment"] == treatment]
        passing, total = int(sub["n_tests_passing"].sum()), int(sub["n_tests_total"].sum())
        full = int((sub["success_rate"] == 1.0).sum())
        ax.barh(y, passing / total * 100, height=0.5, color=COLOR[treatment])
        ax.barh(y, 100 - passing / total * 100, left=passing / total * 100, height=0.5,
                color="white", edgecolor=COLOR[treatment], hatch="////", linewidth=1)
        ax.annotate(f"{passing}/{total} testes ({passing / total:.0%}) · {full}/{len(sub)} trials com 100%",
                    (2, y), va="center", fontsize=9.5, color="white", fontweight="bold")
    ax.set_yticks([0, 1], [LABEL[MANUAL], LABEL[IA]])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% dos testes de aceitação passando ao fim do trial (hachurado = falhando)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Taxa de sucesso agregada por tratamento", loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "rq2_sucesso.png"))
    plt.close(fig)


def fig_rq3() -> None:
    pairs = pd.read_csv(os.path.join(DATA_DIR, "rq03_pares.csv"))
    metrics = [
        ("loc", "LOC (linhas totais)"),
        ("cyclomatic_complexity_mean", "Complexidade ciclomática média"),
        ("maintainability_index", "Índice de Manutenibilidade (0–100)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    for ax, (metric, title) in zip(axes, metrics):
        sub = pairs[pairs["metrica"] == metric]
        for _, row in sub.iterrows():
            ax.plot([0, 1], [row["ia_total"], row["manual"]], color=INK_2, linewidth=1.5, zorder=2)
            ax.scatter([0], [row["ia_total"]], s=60, color=COLOR[IA], edgecolor="white", linewidth=2, zorder=3)
            ax.scatter([1], [row["manual"]], s=60, color=COLOR[MANUAL], edgecolor="white", linewidth=2, zorder=3)
            ax.annotate(SHORT[row["participant"]], (1.06, row["manual"]), va="center", fontsize=8.5, color=INK)
        ax.set_xticks([0, 1], ["IA", "Manual"])
        ax.set_xlim(-0.3, 1.55)
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Mediana do participante")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "rq3_metricas.png"))
    plt.close(fig)


def fig_time_by_kata(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    katas = list(KATA_LABEL)
    for treatment, shift in ((IA, -0.12), (MANUAL, 0.12)):
        sub = df[df["treatment"] == treatment]
        for _, row in sub.iterrows():
            x = katas.index(row["kata"]) + shift
            same = sub[sub["kata"] == row["kata"]].sort_values("time")
            nudge = 0 if len(same) == 1 else (-5 if row["trial_id"] == same.iloc[0]["trial_id"] else 5)
            ax.scatter(x, row["time"], s=55, zorder=3,
                       facecolor="white" if row["censored"] else COLOR[treatment],
                       edgecolor=COLOR[treatment], linewidth=1.6,
                       label=LABEL[treatment])
            ax.annotate(SHORT[row["participant"]], (x + (-0.05 if shift < 0 else 0.05), row["time"]),
                        ha="right" if shift < 0 else "left", va="center", fontsize=8, color=INK_2,
                        xytext=(-4 if shift < 0 else 4, nudge), textcoords="offset points")
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), loc="upper left", ncols=2)
    ax.set_yscale("log")
    ax.set_ylim(5, 5000)
    ax.set_xticks(range(len(katas)), [KATA_LABEL[k] for k in katas])
    ax.set_xlim(-0.6, len(katas) - 0.4)
    ax.set_ylabel("Time-to-green (s, escala log)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "tempo_por_kata.png"))
    plt.close(fig)


def fig_p_floor() -> None:
    n = list(range(2, 11))
    one_sided = [1 / 2 ** k for k in n]
    two_sided = [min(1.0, 2 / 2 ** k) for k in n]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(n, one_sided, color=COLOR[IA], linewidth=2, marker="o", markersize=6, label="Unilateral (RQ1)")
    ax.plot(n, two_sided, color=COLOR[MANUAL], linewidth=2, marker="s", markersize=6, label="Bilateral (RQ2, RQ3)")
    ax.axhline(0.05, color=INK, linewidth=1, linestyle="--")
    ax.annotate("α = 0,05", (10, 0.05), xytext=(0, 4), textcoords="offset points", ha="right", fontsize=9, color=INK)
    ax.axvline(3, color=INK_2, linewidth=1, linestyle=":")
    ax.annotate("este experimento (n = 3):\np mínimo 0,125 / 0,25", (3, 0.5), xytext=(8, 0),
                textcoords="offset points", fontsize=9, color=INK)
    ax.set_yscale("log")
    ax.set_xticks(n)
    ax.set_xlabel("Número de pares (participantes)")
    ax.set_ylabel("Menor p-valor possível (log)")
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "piso_p_valor.png"))
    plt.close(fig)


def main() -> None:
    os.makedirs(IMG_DIR, exist_ok=True)
    df = load_trials()
    fig_rq1(df)
    fig_rq2(df)
    fig_rq3()
    fig_time_by_kata(df)
    fig_p_floor()
    print(f"Figuras gravadas em {IMG_DIR}")


if __name__ == "__main__":
    main()
