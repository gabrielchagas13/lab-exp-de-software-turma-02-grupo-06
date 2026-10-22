"""Gera as figuras do artigo (PDF, escala de cinza) a partir de data/.

    python artigo/gerar_figuras.py        # rodar dentro de lab03/
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({"font.family": "serif", "font.size": 9})
CATS = ["Elite", "High", "Medium", "Low"]
CINZAS = ["#222222", "#777777", "#b5b5b5", "#e6e6e6"]
NOMES = {"deployment_frequency": "Freq. de deploy", "lead_time": "Lead time (a)",
         "change_failure_rate": "CFR (a)", "recovery_time": "Recuperação", "geral": "Geral (C1)"}

# Figura 1: classificação DORA (C1) por dimensão
dist = pd.read_csv("data/analise/dora_c1_distribuicao.csv")
fig, ax = plt.subplots(figsize=(6.2, 2.6))
for i, r in dist.iterrows():
    total = sum(r[c] for c in CATS)
    esquerda = 0
    for cat, cor in zip(CATS, CINZAS):
        pct = 100 * r[cat] / total
        ax.barh(i, pct, left=esquerda, color=cor, edgecolor="black", linewidth=0.4,
                label=cat if i == 0 else None)
        if pct >= 7:
            ax.text(esquerda + pct / 2, i, f"{int(r[cat])}", ha="center", va="center",
                    color="white" if cat in ("Elite", "High") else "black", fontsize=8)
        esquerda += pct
ax.set_yticks(range(len(dist)), [NOMES[d] for d in dist.dimensao])
ax.invert_yaxis()
ax.set_xlabel("% dos 300 repositórios")
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.22), frameon=False)
fig.tight_layout()
fig.savefig("artigo/fig_dora_c1.pdf")

# Figura 2: frequência de deploy x CFR (a) e (b)
ds = pd.read_csv("data/dataset.csv")
fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.6), sharex=True)
for ax, col, titulo in zip(axs, ["cfr_ci", "cfr_entrega_v5_patch_e_notas"],
                           ["CFR (a), proxy de CI ($\\rho$ = 0,18)", "CFR (b), v5 ($\\rho$ = 0,62)"]):
    ax.scatter(ds.releases_por_semana, ds[col], s=7, color="#444444", alpha=0.5, linewidths=0)
    ax.set_xscale("log")
    ax.set_title(titulo, fontsize=9)
    ax.set_xlabel("releases por semana (escala log)")
    ax.set_ylim(0, None)
axs[0].set_ylabel("taxa de falha")
fig.tight_layout()
fig.savefig("artigo/fig_rq05.pdf")
print("ok")
