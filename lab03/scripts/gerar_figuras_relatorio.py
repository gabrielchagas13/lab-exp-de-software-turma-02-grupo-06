"""Gera uma figura por questão de pesquisa para o relatório (docs/img/).

O template do relatório pede ao menos uma visualização por RQ, com a pergunta
enunciada antes do gráfico e o tipo adequado ao tipo de dado. Aqui:

- distribuição de uma métrica -> histograma ou boxplot;
- comparação entre categorias -> barras ordenadas por valor;
- relação entre duas numéricas -> dispersão com eixo log.

Eixo logarítmico onde a distribuição é muito assimétrica (frequência, lead time
e recuperação variam por ordens de grandeza), senão a mediana some junto à
origem e o gráfico só mostra os extremos.

Uso:
    python -m scripts.gerar_figuras_relatorio --config config.json
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

CINZA = "#444444"
DESTAQUE = "#1f6feb"
plt.rcParams.update({"font.size": 8, "figure.dpi": 150, "savefig.bbox": "tight",
                     "axes.spines.top": False, "axes.spines.right": False})

CFR_B = "cfr_entrega_v5_patch_e_notas"


def _salvar(fig, destino, nome):
    caminho = os.path.join(destino, nome)
    fig.savefig(caminho)
    plt.close(fig)
    return nome


def rq01(ds, destino):
    fig, ax = plt.subplots(figsize=(5.4, 2.4))
    ax.hist(ds.releases_por_semana, bins=40, color=CINZA)
    ax.set_xscale("log")
    ax.axvline(ds.releases_por_semana.median(), color=DESTAQUE, lw=1.6,
               label=f"mediana = {ds.releases_por_semana.median():.2f}")
    ax.axvline(7, color="#aa0000", lw=1.2, ls="--", label="corte Elite (7/semana)")
    ax.set_xlabel("Releases por semana (escala log)")
    ax.set_ylabel("Repositórios")
    ax.legend(frameon=False, fontsize=7)
    return _salvar(fig, destino, "rq01_frequencia.png")


def rq02(ds, destino):
    fig, ax = plt.subplots(figsize=(5.4, 2.2))
    dados = [ds.lead_time_release_h.dropna(), ds.lead_time_commit_h.dropna()]
    ax.boxplot(dados, orientation='horizontal', tick_labels=["(a) por release", "(b) por commit"],
               widths=0.5, flierprops={"marker": ".", "markersize": 3, "alpha": 0.4})
    ax.set_xscale("log")
    ax.set_xlabel("Lead time em horas (escala log)")
    for i, serie in enumerate(dados, start=1):
        ax.text(serie.median(), i + 0.28, f"mediana {serie.median():.0f} h",
                fontsize=7, color=DESTAQUE, ha="center")
    return _salvar(fig, destino, "rq02_lead_time.png")


def rq03(ds, destino):
    colunas = [("cfr_ci", "(a) proxy de CI"), (CFR_B, "(b) v5 (referência)"),
               ("cfr_entrega_v2_semver_ou_nome", "(b) v2"),
               ("cfr_entrega_v3_commits", "(b) v3")]
    fig, ax = plt.subplots(figsize=(5.4, 2.4))
    dados = [ds[c].dropna() * 100 for c, _ in colunas]
    ax.boxplot(dados, orientation='horizontal', tick_labels=[r for _, r in colunas], widths=0.55,
               flierprops={"marker": ".", "markersize": 3, "alpha": 0.4})
    for faixa, cor in ((15, "#2da44e"), (30, "#bf8700"), (45, "#aa0000")):
        ax.axvline(faixa, color=cor, lw=0.9, ls="--", alpha=0.7)
    ax.set_xlabel("Change failure rate (%) — linhas: cortes Elite/High/Medium")
    return _salvar(fig, destino, "rq03_cfr.png")


def rq04(ds, destino):
    serie = ds.recovery_median_h.dropna()
    fig, ax = plt.subplots(figsize=(5.4, 2.4))
    ax.hist(serie, bins=40, color=CINZA)
    ax.set_xscale("log")
    ax.axvline(serie.median(), color=DESTAQUE, lw=1.6,
               label=f"mediana = {serie.median():.2f} h")
    ax.axvline(1, color="#2da44e", lw=1.2, ls="--", label="corte Elite (1 h)")
    ax.set_xlabel("Tempo de recuperação em horas (escala log)")
    ax.set_ylabel(f"Repositórios (n = {len(serie)})")
    ax.legend(frameon=False, fontsize=7)
    return _salvar(fig, destino, "rq04_recuperacao.png")


def rq05(ds, destino):
    fig, axs = plt.subplots(1, 2, figsize=(5.8, 2.4), sharey=True)
    for ax, col, titulo in zip(axs, ["cfr_ci", CFR_B],
                               ["CFR (a), proxy de CI\nρ = 0,18",
                                "CFR (b), v5\nρ = 0,62"]):
        ax.scatter(ds.releases_por_semana, ds[col] * 100, s=6, color=CINZA,
                   alpha=0.5, linewidths=0)
        ax.set_xscale("log")
        ax.set_title(titulo, fontsize=8)
        ax.set_xlabel("Releases por semana (log)")
    axs[0].set_ylabel("Taxa de falha (%)")
    return _salvar(fig, destino, "rq05_dispersao.png")


def rq06(data_dir, destino):
    r6 = pd.read_csv(os.path.join(data_dir, "analise", "rq06_fatores.csv"))
    sig = r6[r6.significativo].groupby("fator").size().sort_values()
    fig, ax = plt.subplots(figsize=(5.4, 2.0))
    cores = [DESTAQUE if f == "age_years" else CINZA for f in sig.index]
    nomes = {"age_years": "Idade", "contributors": "Contribuidores",
             "language": "Linguagem", "stars": "Estrelas"}
    ax.barh([nomes.get(f, f) for f in sig.index], sig.values, color=cores)
    for i, v in enumerate(sig.values):
        ax.text(v + 0.1, i, str(v), va="center", fontsize=7)
    ax.set_xlabel("Testes significativos após correção de Holm (de 40)")
    return _salvar(fig, destino, "rq06_fatores.png")


def rq07(data_dir, destino):
    pares = pd.read_csv(os.path.join(data_dir, "analise", "rq07_pares.csv"))
    alvo = pares[(pares.combinacao_a == "C1")].sort_values("pct_mudou")
    rotulo = {"C2": "C2 (tudo muda)", "C3": "C3 (só lead time)",
              "C4": "C4 (só CFR)", "C5": "C5 (só unidade)"}
    fig, ax = plt.subplots(figsize=(5.4, 2.0))
    ax.barh([rotulo.get(c, c) for c in alvo.combinacao_b], alvo.pct_mudou, color=CINZA)
    for i, (v, k) in enumerate(zip(alvo.pct_mudou, alvo.kappa_linear)):
        ax.text(v + 0.5, i, f"{v:.1f}%  (κ = {k:.2f})", va="center", fontsize=7)
    ax.set_xlim(0, max(alvo.pct_mudou) * 1.45)
    ax.set_xlabel("Repositórios que mudam de categoria DORA em relação ao C1 (%)")
    return _salvar(fig, destino, "rq07_sensibilidade.png")


def rq08(data_dir, destino):
    r8 = pd.read_csv(os.path.join(data_dir, "analise", "rq08_versoes.csv"))
    r8 = r8.set_index("versao")
    fig, ax = plt.subplots(figsize=(5.4, 2.2))
    x = range(len(r8))
    ax.bar([i - 0.2 for i in x], r8.spearman_freq_cfr_b, width=0.4,
           color=CINZA, label="CFR (b) × frequência")
    ax.bar([i + 0.2 for i in x], r8.spearman_freq_rework, width=0.4,
           color=DESTAQUE, label="rework rate × frequência")
    ax.set_xticks(list(x))
    ax.set_xticklabels([v.replace("_", "\n") for v in r8.index], fontsize=6)
    ax.set_ylabel("ρ de Spearman")
    ax.axhline(0, color="black", lw=0.6)
    ax.legend(frameon=False, fontsize=7)
    return _salvar(fig, destino, "rq08_artefato.png")


def dora(data_dir, destino):
    dist = pd.read_csv(os.path.join(data_dir, "analise", "dora_c1_distribuicao.csv"))
    dist = dist.set_index("dimensao")
    nomes = {"deployment_frequency": "Frequência", "lead_time": "Lead time",
             "change_failure_rate": "Taxa de falha", "recovery_time": "Recuperação",
             "geral": "GERAL (C1)"}
    cores = {"Elite": "#2da44e", "High": "#7ac142", "Medium": "#bf8700", "Low": "#aa0000"}
    fig, ax = plt.subplots(figsize=(5.6, 2.4))
    base = [0] * len(dist)
    for cat, cor in cores.items():
        ax.barh([nomes.get(i, i) for i in dist.index], dist[cat], left=base,
                color=cor, label=cat)
        base = [b + v for b, v in zip(base, dist[cat])]
    ax.set_xlabel("Repositórios (300)")
    # Legenda acima do eixo: dentro do gráfico ela cobre as barras, que vão de
    # ponta a ponta porque toda linha soma 300 repositórios.
    ax.legend(frameon=False, fontsize=7, ncol=4,
              loc="lower center", bbox_to_anchor=(0.5, 1.02))
    return _salvar(fig, destino, "dora_c1.png")


def gerar(data_dir, destino):
    os.makedirs(destino, exist_ok=True)
    ds = pd.read_csv(os.path.join(data_dir, "dataset.csv"))
    return [rq01(ds, destino), rq02(ds, destino), rq03(ds, destino), rq04(ds, destino),
            rq05(ds, destino), rq06(data_dir, destino), rq07(data_dir, destino),
            rq08(data_dir, destino), dora(data_dir, destino)]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="scripts.gerar_figuras_relatorio")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--destino", default=os.path.join("docs", "img"))
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]
    for nome in gerar(data_dir, args.destino):
        print(f"  {os.path.join(args.destino, nome)}")


if __name__ == "__main__":
    main()
