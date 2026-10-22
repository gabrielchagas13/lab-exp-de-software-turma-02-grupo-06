"""Gera `docs/index.html`: o relatório do Lab03 numa página só, a partir dos dados.

Todo número da página vem de `data/` (funil, dataset, descritivas, classificação C1
e RQ 07), então a página nunca fica desatualizada em relação à coleta: depois de
rodar o pipeline e as análises, basta rodar este script de novo. O texto é fixo;
o que ainda não existe (discussão, ameaças finais e replicação) aparece
marcado como **pendente**, sem números inventados.

Uso:
    python -m scripts.gerar_relatorio_html --config config.json
"""
import argparse
import html
import json
import os

import pandas as pd

ORDEM_PTS = {"Elite": 4, "High": 3, "Medium": 2, "Low": 1}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIAS = ("Elite", "High", "Medium", "Low")
NOMES_DIM = {"deployment_frequency": "Frequência de deploy", "lead_time": "Lead time (a)",
             "change_failure_rate": "CFR (a)", "recovery_time": "Tempo de recuperação",
             "geral": "Geral (C1)"}


def n(valor, casas=1):
    """Número no formato pt-BR."""
    if valor is None or pd.isna(valor):
        return "–"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(prop, casas=1):
    return n(100 * prop, casas) + "%"


def esc(x):
    return html.escape(str(x))


def tabela(cabecalho, linhas, classes=""):
    th = "".join(f"<th>{esc(c)}</th>" for c in cabecalho)
    corpo = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas)
    return (f'<div class="tabela"><table class="{classes}"><thead><tr>{th}</tr></thead>'
            f"<tbody>{corpo}</tbody></table></div>")


def barras_dora(dist):
    """Barras empilhadas Elite/High/Medium/Low por dimensão (CSS puro, sem biblioteca)."""
    linhas = []
    for _, r in dist.iterrows():
        total = sum(int(r[c]) for c in CATEGORIAS)
        segs = "".join(
            f'<span class="seg {c.lower()}" style="width:{100 * int(r[c]) / total:.2f}%" '
            f'title="{c}: {int(r[c])}">{int(r[c]) if int(r[c]) / total > .05 else ""}</span>'
            for c in CATEGORIAS)
        linhas.append(f'<div class="barra"><span class="rotulo">{esc(NOMES_DIM[r["dimensao"]])}'
                      f'</span><div class="trilho">{segs}</div></div>')
    legenda = "".join(f'<span><i class="seg {c.lower()}"></i>{c}</span>' for c in CATEGORIAS)
    return f'<div class="barras">{"".join(linhas)}<div class="legenda">{legenda}</div></div>'


def contar(serie, bordas):
    """Quantos valores caem em cada faixa [b0,b1), [b1,b2)... (primeira e última abertas)."""
    v = pd.to_numeric(serie, errors="coerce").dropna()
    cortes = [-float("inf"), *bordas, float("inf")]
    return [int(((v >= a) & (v < b)).sum()) for a, b in zip(cortes, cortes[1:])]


def dados_graficos(ds, dist, r7, d):
    """Tudo que os gráficos desenham, já agregado (vai embutido na página como JSON)."""
    cl = pd.read_csv(os.path.join(d, "analise", "rq07_classificacoes.csv"))
    ordem = list(CATEGORIAS)
    matriz = [[int(((cl.C1_geral == a) & (cl.C2_geral == b)).sum()) for b in ordem] for a in ordem]
    pares = r7["pares"]
    ponto = lambda x, y: [{"x": round(float(a), 4), "y": round(float(b), 4)}
                          for a, b in zip(x, y) if pd.notna(a) and pd.notna(b)]
    pm = r7["por_metrica"]
    eixo = lambda m: float(pm[(pm.metrica == m) & (pm.combinacao_a == "C1")].pct_mudou.max())
    pts = lambda c: c.map(ORDEM_PTS)
    eixos = ["deployment_frequency", "lead_time", "change_failure_rate", "recovery_time"]
    media = lambda pref: [round(float(pts(cl[f"{pref}_{e}"]).mean()), 2) for e in eixos]
    top = ds.language.value_counts().head(4).index.tolist()
    por_lang = {}
    for lg in top:
        sub = ds[ds.language == lg]
        por_lang[lg] = {"n": len(sub),
                        "v": [round(float(pts(sub[f"dora_{e}"]).mean()), 2) for e in eixos]}
    repos = sorted(
        [{"n": r.full_name, "l": r.language if isinstance(r.language, str) else "—",
          "s": int(r.stars), "g": r.dora_geral if isinstance(r.dora_geral, str) else "—",
          "v": [None if not isinstance(getattr(r, f"dora_{e}"), str)
                else ORDEM_PTS[getattr(r, f"dora_{e}")] for e in eixos]}
         for r in ds.itertuples()], key=lambda x: -x["s"])
    kap = pd.read_csv(os.path.join(d, "validacao", "concordancia.csv"))
    av = pd.read_csv(os.path.join(d, "validacao", "avaliacao_heuristica.csv"))
    nomes_dim = {"tipo_projeto": "Tipo do projeto", "releases_sao_entregas": "Releases são entregas",
                 "corretiva": "Release corretiva"}
    r8 = pd.read_csv(os.path.join(d, "analise", "rq08_versoes.csv"))
    r8p = pd.read_csv(os.path.join(d, "analise", "rq08_por_repo.csv"))
    pt8 = lambda x, y: [{"x": round(float(a), 4), "y": round(float(b), 4)}
                        for a, b in zip(x, y) if pd.notna(a) and pd.notna(b)]
    return {
        "val": {"dims": [nomes_dim[x] for x in kap.dimensao], "kappa": [float(x) for x in kap.kappa],
                "variantes": [x.replace("_", " ") for x in av.variante],
                "precisao": [float(x) for x in av.precisao], "recall": [float(x) for x in av.recall],
                "f1": [float(x) for x in av.f1]},
        "r8": {"versoes": ["v1 semver", "v2 semver ou nome", "v3 commits", "v4 combinada"],
               "rework": [float(x) * 100 for x in r8.rework_mediana],
               "cfr_b": [float(x) * 100 for x in r8.cfr_b_mediana],
               "rho_cfr": [float(x) for x in r8.spearman_freq_cfr_b],
               "rho_rework": [float(x) for x in r8.spearman_freq_rework],
               "disp": pt8(r8p.cfr_b, r8p.rework)},
        "radar_eixos": ["Frequência", "Lead time", "CFR", "Recuperação"],
        "radar_perfil": {"C1": media("C1"), "C2": media("C2")},
        "radar_lang": por_lang,
        "repos": repos,
        "dora": {r.dimensao: [int(getattr(r, c)) for c in CATEGORIAS] for r in dist.itertuples()},
        "dim_nomes": NOMES_DIM,
        "freq": {"rotulos": ["< 1/mês", "1/mês–0,5/sem", "0,5–1/sem", "1–2/sem", "2–7/sem", "≥ 7/sem"],
                 "n": contar(ds.releases_por_semana, [12 / 52.1, 0.5, 1, 2, 7])},
        "lead": {"rotulos": ["< 1 dia", "1–3 d", "3–7 d", "1–2 sem", "2–4 sem", "1–3 meses", "> 3 meses"],
                 "a": contar(ds.lead_time_release_h, [24, 72, 168, 336, 720, 2160]),
                 "b": contar(ds.lead_time_commit_h, [24, 72, 168, 336, 720, 2160])},
        "cfr": {"rotulos": ["0–5%", "5–15%", "15–30%", "30–45%", "45–60%", "60–80%", "80–100%"],
                "a": contar(ds.cfr_ci, [.05, .15, .30, .45, .60, .80]),
                "b": contar(ds.cfr_entrega_v5_patch_e_notas, [.05, .15, .30, .45, .60, .80])},
        "rec": {"rotulos": ["< 1 h", "1–6 h", "6–24 h", "1–3 d", "3–7 d", "≥ 7 d"],
                "n": contar(ds.recovery_median_h, [1, 6, 24, 72, 168])},
        "disp_a": ponto(ds.releases_por_semana, ds.cfr_ci),
        "disp_b": ponto(ds.releases_por_semana, ds.cfr_entrega_v5_patch_e_notas),
        "r7_dist": {r.combinacao: [int(getattr(r, c)) for c in CATEGORIAS]
                    for r in r7["distribuicao"].itertuples()},
        "r7_pares": {"rotulos": [f"{r.combinacao_a} × {r.combinacao_b}" for r in pares.itertuples()],
                     "mudou": [float(x) for x in pares.pct_mudou],
                     "kappa": [float(x) for x in pares.kappa_linear]},
        "r7_eixos": {"rotulos": ["Unidade de deploy", "Lead time (a→b)", "CFR (a→b)", "Recuperação"],
                     "mudou": [eixo("deployment_frequency"), eixo("lead_time"),
                               eixo("change_failure_rate"), 0.0]},
        "matriz": {"ordem": ordem, "v": matriz},
        "kpis": [["Repositórios", str(len(ds))],
                 ["Releases por semana (mediana)", n(ds.releases_por_semana.median(), 2)],
                 ["Lead time (mediana)", n(ds.lead_time_release_h.median() / 24) + " dias"],
                 ["CFR proxy de CI (mediana)", pct(ds.cfr_ci.median())],
                 ["CFR proxy de entrega (mediana)", pct(ds.cfr_entrega_v5_patch_e_notas.median())],
                 ["Mudam de categoria (C1 × C2)", n(float(pares.pct_mudou.iloc[0]), 0) + "%"]],
    }


def pendente(texto):
    return f'<p class="pendente"><strong>Pendente.</strong> {texto}</p>'


def montar(cfg):
    d = os.path.join(RAIZ, cfg["data_dir"])
    funil = pd.read_csv(os.path.join(d, "selecao", "funil.csv"))
    ds = pd.read_csv(os.path.join(d, "dataset.csv"))
    desc = pd.read_csv(os.path.join(d, "analise", "rq01_rq04_descritivas.csv")).set_index("metrica")
    dist = pd.read_csv(os.path.join(d, "analise", "dora_c1_distribuicao.csv"))
    r7 = {k: pd.read_csv(os.path.join(d, "analise", f"rq07_{k}.csv"))
          for k in ("pares", "distribuicao", "por_metrica", "heuristica_corretiva",
                    "robustez_rq05")}
    inicio, fim = cfg["window_start"], cfg["window_end"]
    N = len(ds)

    def m(col, campo="mediana"):
        return desc.loc[col, campo]

    # ---- metodologia: funil
    t_funil = tabela(
        ["Etapa", "Critério", "Restantes", "Descartados"],
        [[f"<code>{esc(r.etapa)}</code>", esc(r.motivo) if isinstance(r.motivo, str) else "",
          n(r.restantes, 0), n(r.descartados, 0)] for r in funil.itertuples()], "num")

    # ---- RQ 01 a 04
    freq, ltr, ltc = m("releases_por_semana"), m("lead_time_release_h"), m("lead_time_commit_h")
    cfr_a, rec = m("cfr_ci"), m("recovery_median_h")
    g = dist.set_index("dimensao")
    elite_freq = int(g.loc["deployment_frequency", "Elite"])
    low_freq = int(g.loc["deployment_frequency", "Low"])
    t_desc = tabela(
        ["Métrica", "n", "Mediana", "IQR (Q1 – Q3)", "Mín", "Máx"],
        [[lbl, n(desc.loc[c, "n"], 0), f"<strong>{n(desc.loc[c, 'mediana'], cs)}</strong> {u}",
          f"{n(desc.loc[c, 'q1'], cs)} – {n(desc.loc[c, 'q3'], cs)}",
          n(desc.loc[c, "min"], cs), n(desc.loc[c, "max"], cs)]
         for c, lbl, u, cs in [
            ("releases_por_semana", "RQ 01 — releases por semana", "", 2),
            ("lead_time_release_h", "RQ 02 (a) — lead time por release", "h", 1),
            ("lead_time_commit_h", "RQ 02 (b) — lead time por commit", "h", 1),
            ("cfr_ci", "RQ 03 (a) — CFR, proxy de CI", "", 3),
            ("recovery_median_h", "RQ 04 — tempo de recuperação", "h", 2)]], "num")
    cfr_b = {v: ds[c].median() for v, c in [
        ("v5 (patch e notas) - referencia", "cfr_entrega_v5_patch_e_notas"),
        ("v1 (semver)", "cfr_entrega_v1_semver"), ("v2 (semver ou nome)", "cfr_entrega_v2_semver_ou_nome"),
        ("v3 (commits)", "cfr_entrega_v3_commits"), ("v4 (combinada)", "cfr_entrega_v4_combinada")]}
    t_cfrb = tabela(["CFR (b) — heurística corretiva", "Mediana"],
                    [[k, pct(v)] for k, v in cfr_b.items()], "num")
    elite_cfr = int(g.loc["change_failure_rate", "Elite"])
    sem_rec = int(g.loc["recovery_time", "sem_classificacao"])

    # ---- RQ 07
    p = r7["pares"].set_index(["combinacao_a", "combinacao_b"])
    def par(a, b, c):
        return p.loc[(a, b), c]
    t_pares = tabela(
        ["Par", "% que mudou", "Subiu / desceu", "Kappa linear", "IC 95%"],
        [[f"{a} × {b}", n(par(a, b, "pct_mudou")),
          f"{n(par(a, b, 'pct_subiu'))} / {n(par(a, b, 'pct_desceu'))}",
          f"<strong>{n(par(a, b, 'kappa_linear'), 3)}</strong>",
          f"{n(par(a, b, 'kappa_ic_inf'), 3)} – {n(par(a, b, 'kappa_ic_sup'), 3)}"]
         for a, b in [("C1", "C2"), ("C1", "C3"), ("C2", "C3"), ("C1", "C4"), ("C1", "C5")]], "num")
    pm = r7["por_metrica"]
    def eixo(metrica):
        r = pm[(pm.metrica == metrica) & (pm.combinacao_a == "C1")]
        r = r[r.pct_mudou > 0].iloc[0] if (r.pct_mudou > 0).any() else r.iloc[0]
        return r
    t_eixos = tabela(
        ["Eixo", "Troca", "% que mudou de categoria", "Kappa linear"],
        [["Unidade de deploy", "release → release + pré-release",
          n(eixo("deployment_frequency").pct_mudou), n(eixo("deployment_frequency").kappa_linear, 3)],
         ["Lead time", "(a) → (b)", n(eixo("lead_time").pct_mudou),
          n(eixo("lead_time").kappa_linear, 3)],
         ["CFR", "(a) → (b)", n(eixo("change_failure_rate").pct_mudou),
          n(eixo("change_failure_rate").kappa_linear, 3)],
         ["Recuperação", "sem variante", "0,0", "1,000"]], "num")
    t_dist7 = tabela(["Combinação", *CATEGORIAS],
                     [[r.combinacao, *[n(getattr(r, c), 0) for c in CATEGORIAS]]
                      for r in r7["distribuicao"].itertuples()], "num")
    t_heur = tabela(
        ["Heurística (C1 + CFR b)", "Mediana do CFR", "% que mudou", "Kappa linear"],
        [[esc(r.cfr_b), pct(r.mediana_cfr), n(r.pct_mudou), n(r.kappa_linear, 3)]
         for r in r7["heuristica_corretiva"].itertuples()], "num")
    t_rho = tabela(
        ["Combinação", "Unidade", "CFR", "ρ de Spearman", "p"],
        [[r.combinacao, esc(r.unidade), esc(r.cfr), n(r.rho, 3),
          "&lt; 0,001" if r.p_valor < 0.001 else n(r.p_valor, 3)]
         for r in r7["robustez_rq05"].itertuples()], "num")

    r8 = pd.read_csv(os.path.join(d, "analise", "rq08_versoes.csv"))
    t_r8 = tabela(
        ["Heurística", "Rework (mediana)", "IQR", "CFR (b) (mediana)", "% com rework > CFR (b)",
         "ρ freq.: rework", "ρ freq.: CFR (b)"],
        [[esc(r.versao), f"<strong>{pct(r.rework_mediana)}</strong>",
          f"{pct(r.rework_q1)} – {pct(r.rework_q3)}", pct(r.cfr_b_mediana), n(r.pct_rework_maior),
          n(r.spearman_freq_rework, 3), n(r.spearman_freq_cfr_b, 3)] for r in r8.itertuples()], "num")
    v2 = r8[r8.versao == "v5_patch_e_notas"].iloc[0]
    kap = pd.read_csv(os.path.join(d, "validacao", "concordancia.csv"))
    av = pd.read_csv(os.path.join(d, "validacao", "avaliacao_heuristica.csv"))
    nomes_dim = {"tipo_projeto": "Tipo do projeto", "releases_sao_entregas": "Releases são entregas",
                 "corretiva": "Release corretiva"}
    t_kappa = tabela(["Dimensão", "Itens", "Kappa de Fleiss", "Interpretação (Landis & Koch)"],
                     [[nomes_dim[r.dimensao], n(r.n_itens, 0), f"<strong>{n(r.kappa, 3)}</strong>",
                       esc(r.interpretacao)] for r in kap.itertuples()], "num")
    t_f1 = tabela(["Heurística", "n", "Precisão", "Recall", "F1", "Meta F1 ≥ 0,70"],
                  [[esc(r.variante), n(r.n, 0), n(r.precisao, 3), n(r.recall, 3),
                    f"<strong>{n(r.f1, 3)}</strong>", "atinge" if r.atinge_meta else "não atinge"]
                   for r in av.itertuples()], "num")
    melhor = av.sort_values("f1", ascending=False).iloc[0]
    atingem = av[av.atinge_meta]

    r5 = pd.read_csv(os.path.join(d, "analise", "rq05_spearman.csv"))
    r6 = pd.read_csv(os.path.join(d, "analise", "rq06_fatores.csv"))
    nome_cfr = {"cfr_ci": "CFR (a), proxy de CI",
                "cfr_entrega_v5_patch_e_notas": "CFR (b) v5 patch e notas (referência)",
                "cfr_entrega_v1_semver": "CFR (b) v1 semver",
                "cfr_entrega_v2_semver_ou_nome": "CFR (b) v2 semver ou nome",
                "cfr_entrega_v3_commits": "CFR (b) v3 commits",
                "cfr_entrega_v4_combinada": "CFR (b) v4 combinada"}
    nome_met = {**nome_cfr, "releases_por_semana": "Frequência de deploy",
                "lead_time_release_h": "Lead time (a)", "lead_time_commit_h": "Lead time (b)",
                "recovery_median_h": "Tempo de recuperação"}
    nome_fator = {"language": "Linguagem", "stars": "Estrelas", "contributors": "Contribuidores",
                  "age_years": "Idade"}
    fmt_p = lambda p: "&lt; 0,001" if p < 0.001 else n(p, 3)
    t_r5 = tabela(["CFR", "n", "ρ de Spearman", "p-valor"],
                  [[nome_cfr[r.cfr], n(r.n, 0), f"<strong>{n(r.rho, 3)}</strong>", fmt_p(r.p_value)]
                   for r in r5.itertuples()], "num")
    sig = r6[r6.significativo]
    t_r6 = tabela(["Métrica", "Fator", "p (Holm)", "ε²"],
                  [[nome_met[r.metrica], nome_fator[r.fator], fmt_p(r.p_holm), n(r.tamanho_efeito, 2)]
                   for r in sig.itertuples()], "num")
    rho_b = r5[r5.cfr.str.startswith("cfr_entrega")].rho
    rho_a = float(r5[r5.cfr == "cfr_ci"].rho.iloc[0])
    quartis = ds.groupby(pd.qcut(ds.age_years, 4, labels=False), observed=True)[
        ["releases_por_semana", "lead_time_release_h", "cfr_entrega_v4_combinada"]].median()
    contrib = ds.groupby(pd.qcut(ds.contributors, 4, labels=False), observed=True)[
        "lead_time_release_h"].median()
    dados = json.dumps(dados_graficos(ds, dist, r7, d), ensure_ascii=False)
    SECAO_R8 = f'''<section id="rq08">
<h2>5. Bônus: rework rate (RQ 08)</h2>
<p>O <em>rework rate</em> é a proporção de releases <strong>corretivas</strong> sobre o total de releases do
repositório, a métrica que o DORA acrescentou em 2024. Usa a mesma heurística do CFR (b), nas quatro versões.</p>
{t_r8}
<p>Com as versões semver, a mediana é de <strong>{pct(v2.rework_mediana, 0)} das releases</strong> classificadas como
corretivas (a versão por commits dá {pct(r8.rework_mediana.min(), 0)}). O rework é maior que o CFR (b) em
<strong>{n(v2.pct_rework_maior, 0)}%</strong> dos repositórios.</p>
<div class="grid">
<div class="card"><h4>Rework × CFR (b), mediana por heurística</h4><p class="desc">As duas partem do mesmo rótulo de release corretiva, mas contam coisas diferentes.</p><div class="chart" style="height:280px"><canvas id="c-r8-med"></canvas></div></div>
<div class="card"><h4>Correlação com a frequência de releases</h4><p class="desc">Spearman. O CFR (b) acompanha a frequência; o rework quase não.</p><div class="chart" style="height:280px"><canvas id="c-r8-rho"></canvas></div></div>
</div>
<div class="card"><h4>Rework × CFR (b), um ponto por repositório (v2)</h4><p class="desc">Acima da diagonal, o rework é maior que o CFR (b).</p><div class="chart" style="height:320px"><canvas id="c-r8-disp"></canvas></div></div>
<h3>Em que difere do CFR (b)</h3>
{tabela(["", "CFR (b)", "Rework rate"],
  [["Quem é contado", "a release que <strong>falhou</strong> (foi seguida de uma corretiva)", "a release que <strong>é</strong> corretiva"],
   ["Janela", "só vale se a correção veio em até 7 dias", "qualquer prazo"],
   ["Censura", "os últimos 7 dias da janela saem do denominador", "nada é censurado"],
   ["Depende do ritmo de releases", "<strong>sim</strong>", "quase não"]])}
<p>Um projeto que publica uma release por mês pode ter metade delas como correções e ainda assim um CFR (b)
perto de zero, porque nenhuma correção cai a 7 dias da release anterior. O CFR (b) tem correlação forte com a
frequência de releases (ρ ≈ 0,7) e o rework tem correlação fraca (ρ ≈ 0,15 a 0,26): isso é coerente com a
hipótese de que a correlação positiva entre frequência e CFR (b) da RQ 05 seja em parte <strong>mecânica</strong>.
Não é prova, mas pede cautela ao interpretar a RQ 05 pelo CFR (b).</p>
<p class="pendente"><strong>Ressalva.</strong> A heurística corretiva foi validada contra a amostra-ouro e só a v5
atinge F1 ≥ 0,70, de forma otimista (F1 = {n(melhor.f1, 3)}; ver seção 2). As versões usadas aqui (v1 a v4) ficam entre
{n(av.f1.iloc[:4].min(), 2)} e {n(av.f1.iloc[:4].max(), 2)}. Os números acima são o que cada versão produz, não a taxa real de retrabalho.</p>
</section>

'''
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lab 03 — Métricas DORA</title>
<style>{CSS}</style>
</head>
<body>
<header class="topo">
  <p class="sobre">Laboratório de Experimentação de Software · Lab03 · Grupo 06 · PUC Minas</p>
  <h1>Métricas DORA em repositórios populares do GitHub</h1>
  <p class="autores">Gabriel Chagas · Guilherme Lana · Marcus Vinicius</p>
  <p class="meta">PUC Minas, Engenharia de Software · Belo Horizonte, MG</p>
  <p class="meta">{N} repositórios · janela de {esc(inicio)} a {esc(fim)} ·
  <span class="selo">versão de trabalho</span></p>
</header>

<div class="kpi-row" id="kpis"></div>
<nav class="indice" aria-label="Seções">
  <a href="#resumo">Resumo</a><a href="#introducao">Introdução</a>
  <a href="#metodologia">Metodologia</a><a href="#resultados">Resultados</a>
  <a href="#sensibilidade">Sensibilidade (RQ 07)</a><a href="#rq08">Bônus (RQ 08)</a><a href="#discussao">Discussão</a>
  <a href="#ameacas">Ameaças</a><a href="#replicacao">Replicação</a><a href="#conclusao">Conclusão</a>
  <a href="#referencias">Referências</a>
</nav>

<main>
<section id="resumo">
<h2>Resumo</h2>
<p>Minerou-se as métricas DORA de <strong>{N} repositórios open source</strong> do GitHub que usam
GitHub Actions, numa janela de 12 meses. A amostra tem perfil de projetos <strong>estáveis e lentos</strong>:
a mediana é de {n(freq, 2)} releases por semana e de {n(ltr / 24)} dias de lead time, enquanto
{pct(g.loc['change_failure_rate', 'pct_elite_ou_high'] / 100)} dos repositórios ficam em Elite ou High na taxa de falha
medida pelo CI. A classificação, porém, <strong>não é robusta à definição operacional</strong>: trocar as
definições de referência (C1) por outras igualmente plausíveis muda a categoria geral de
{n(par('C1', 'C2', 'pct_mudou'), 1)}% dos repositórios (kappa linear {n(par('C1', 'C2', 'kappa_linear'), 2)}),
e a taxa de falha é o eixo que mais pesa: a mediana do CFR é {pct(ds.cfr_ci.median())} medida pelo CI e
{pct(ds.cfr_entrega_v5_patch_e_notas.median())} medida pela entrega (release seguida de uma corretiva). A validação manual
mostrou que "release corretiva" é um critério ambíguo (kappa de Fleiss = {n(kap[kap.dimensao == "corretiva"].kappa.iloc[0], 2)}).</p>
<p>Velocidade e estabilidade <strong>não andam juntas</strong> nesta amostra: a frequência de deploy tem correlação
positiva com o CFR (a) (ρ = {n(rho_a, 2)}) e forte com o CFR (b) (ρ de {n(rho_b.min(), 2)} a {n(rho_b.max(), 2)}), o oposto
do que o DORA sugere (RQ 05). A <strong>idade</strong> do repositório é o fator mais associado ao desempenho: {len(sig)} dos
{len(r6)} testes da RQ 06 são significativos depois da correção de Holm, a maioria envolvendo idade, contribuidores e
linguagem no lead time (RQ 06).</p>
</section>

<section id="introducao">
<h2>1. Introdução</h2>
<p>As métricas DORA (<em>DevOps Research and Assessment</em>) tornaram-se o padrão de mercado para medir o
desempenho de entrega de software <a href="#r1">[1]</a>: frequência de deploy, lead time para mudanças, taxa
de falha das mudanças (CFR) e tempo de recuperação. Neste trabalho elas são <strong>mineradas</strong>, isto é,
calculadas automaticamente a partir de dados públicos, o que obriga a trabalhar com <strong>aproximações</strong>:
uma <em>release publicada</em> representa um deploy, e um workflow de CI vermelho representa uma falha.
Por isso o trabalho tem dois objetivos: medir as métricas e medir <strong>o quanto as conclusões mudam quando a
definição da métrica muda</strong> (RQ 07).</p>
<h3>Questões de pesquisa</h3>
<ol class="rqs">
<li><strong>RQ 01.</strong> Qual a frequência de deploys dos repositórios populares que usam CI/CD?</li>
<li><strong>RQ 02.</strong> Qual o tempo entre um commit e seu respectivo deploy?</li>
<li><strong>RQ 03.</strong> Qual a taxa de falha das mudanças entregues?</li>
<li><strong>RQ 04.</strong> Qual o tempo de recuperação após uma execução de CI/CD com falha?</li>
<li><strong>RQ 05.</strong> Repositórios com maior frequência de deploy têm maior ou menor taxa de falha?</li>
<li><strong>RQ 06.</strong> Que características dos repositórios se associam a melhor desempenho DORA?</li>
<li><strong>RQ 07.</strong> O quanto a classificação DORA depende da definição operacional escolhida?</li>
<li><strong>RQ 08 (bônus).</strong> Qual a <em>rework rate</em> e em que ela difere do CFR (b)?</li>
</ol>
{pendente("hipóteses informais por RQ (issue #62, fechada): o texto não está no repositório; colar aqui.")}
</section>

<section id="metodologia">
<h2>2. Metodologia</h2>
<h3>Fonte de dados</h3>
<p>Os dados vêm da API REST do GitHub, acessada por um cliente próprio, sem bibliotecas de terceiros. Toda
resposta é guardada em cache, e a coleta pode ser interrompida e retomada. O cliente respeita o limite por
hora e a proteção contra rajadas. Por repositório coletam-se: metadados e contribuidores; <em>workflow runs</em>
disparados por <code>push</code> no <em>default branch</em>; releases não-rascunho e tags; e os commits entre
releases consecutivas, obtidos por clone local (sem o teto de commits do <code>compare</code>).</p>
<h3>Seleção e funil</h3>
<p>Os candidatos vêm de buscas por faixa de estrelas (a API limita cada busca a 1.000 resultados), são unidos,
ordenados e embaralhados com semente fixa (42) e avaliados até completar {N} repositórios. Cada candidato sai no
primeiro filtro que falha, do mais barato ao mais caro em chamadas à API.</p>
{t_funil}
<h3>Janela e definições operacionais</h3>
<p>Janela fixa de 12 meses ({esc(inicio)} a {esc(fim)}). Deploy = release publicada que não é rascunho nem
pré-release. A data de um commit é a de autoria (<code>author_date</code>). A métrica por repositório é a
<strong>mediana</strong> dos valores individuais, porque as distribuições de tempo têm cauda longa.</p>
<ul>
<li><strong>Frequência:</strong> releases na janela ÷ semanas da janela.</li>
<li><strong>Lead time (a):</strong> mediana, entre as releases, de publicação − commit mais antigo que ela entrega.
<strong>(b):</strong> mediana sobre todos os commits de todas as releases de publicação − data do commit.</li>
<li><strong>CFR (a), proxy de CI:</strong> falhas ÷ (falhas + sucessos) dos runs de push; falha = <code>failure</code>,
<code>timed_out</code>, <code>startup_failure</code>; <code>cancelled</code>, <code>skipped</code>,
<code>neutral</code>, <code>action_required</code>, <code>stale</code> e vazio são ignorados.
<strong>(b), proxy de entrega:</strong> uma release falhou se foi seguida em até 7 dias por uma release
<em>corretiva</em>, classificada por heurística em cinco versões (semver; semver ou nome; commits; combinada; patch e release notes).
Releases dos últimos 7 dias da janela ficam fora do denominador (censura).</li>
<li><strong>Tempo de recuperação:</strong> por workflow, da primeira falha após um sucesso até o sucesso seguinte.
Episódios sem sucesso posterior na janela são <strong>censurados</strong>, não descartados.</li>
<li><strong>Classificação DORA:</strong> cortes fixos da disciplina; categoria geral = mediana das notas
(Elite = 4 … Low = 1) das quatro métricas, arredondada para baixo.</li>
</ul>
<h3>Validação manual</h3>
<p>Uma heurística automática pode errar, e a forma de medir o erro é compará-la com o julgamento humano. Sorteou-se
uma amostra-ouro de 60 repositórios e até 5 releases de cada (300), rotulada de forma independente pelos três
integrantes (tipo de projeto, releases como entregas reais, release corretiva). A concordância é medida pelo kappa
de Fleiss, e o consenso (maioria simples) é a referência para precisão, recall e F1 da heurística.</p>
<h4>Concordância entre avaliadores</h4>
{t_kappa}
<p>O tipo do projeto tem concordância quase perfeita. As outras duas dimensões ficam só em <strong>razoável</strong>
(≈ 0,3), o que indica que os critérios "release corretiva" e "releases são entregas reais" são ambíguos. A divergência
vem sobretudo de <strong>um avaliador</strong>: o "gl" marcou 235 das 300 releases como corretivas, contra 101 (gc) e
110 (mv). A concordância simples entre gc e mv é de 93,7%, e a do gl com cada um dos dois é de 52% e 53%.</p>
<p><strong>Correção nos dados.</strong> Numa primeira versão, 33 releases ficaram fora do kappa e do F1 porque o editor
de planilhas alterou as tags da planilha do avaliador "mv" (por exemplo, <code>22.1.0</code> virou <code>22.1.2000</code>).
As tags foram realinhadas pela URL de cada release, e os números desta seção já usam as 300 releases.</p>
<h4>Precisão, recall e F1 da heurística contra o consenso</h4>
{t_f1}
<p>As quatro primeiras versões não atingem a meta de F1 ≥ 0,70 (de {n(av.f1.iloc[:4].min(), 2)} a {n(av.f1.iloc[:4].max(), 2)}). As
baseadas em semver (v1, v2, v4) têm recall alto e precisão baixa: cerca de metade das releases que marcam como corretivas
não o são segundo o consenso, porque tratam todo incremento de <em>patch</em> como correção. A v3, baseada em commits,
inverte o perfil. A <strong>v5</strong> refina a v1 exigindo também que as release notes citem correção
e chega a F1 = {n(melhor.f1, 3)} (precisão {n(melhor.precisao, 2)}, recall {n(melhor.recall, 2)}).
O valor é <strong>otimista</strong>: a v5 foi escolhida olhando parte da própria amostra. Nas 33 releases que
não participaram da escolha o F1 foi 0,65, e o IC 95% do F1 sobre as 300 vai de 0,63 a 0,80. Detalhes e refinamentos
descartados em <code>docs/heuristica_corretiva.md</code>.</p>
<div class="grid">
<div class="card"><h4>Kappa de Fleiss por dimensão</h4><p class="desc">0,41–0,60 moderada; 0,61–0,80 substancial; acima de 0,80 quase perfeita.</p><div class="chart" style="height:260px"><canvas id="c-kappa"></canvas></div></div>
<div class="card"><h4>Precisão, recall e F1 por heurística</h4><p class="desc">Contra o rótulo de consenso. A meta de F1 é 0,70.</p><div class="chart" style="height:260px"><canvas id="c-f1"></canvas></div></div>
</div>
<h3>Reprodutibilidade</h3>
<p>A coleta roda com <code>python -m pipeline --config config.json</code>, as análises com
<code>python -m analise.rq01_rq04</code> e <code>python -m analise.rq07</code>, <code>python -m analise.rq08</code>, e esta página com
<code>python -m scripts.gerar_relatorio_html</code>. Os dados brutos são versionados em Parquet e os testes rodam no CI.</p>
</section>

<section id="resultados">
<h2>3. Resultados</h2>
<p>Todas as métricas em <strong>mediana e IQR</strong>: as distribuições são muito assimétricas (o maior lead time da
amostra é de {n(m('lead_time_release_h', 'max'), 0)} h contra mediana de {n(ltr, 0)} h).</p>
{t_desc}
<h3>RQ 01 — Frequência de deploy</h3>
<p>A mediana é de <strong>{n(freq, 2)} releases por semana</strong>, ou uma a cada {n(1 / freq, 1)} semanas. Só
<strong>{elite_freq} repositórios ({pct(elite_freq / N, 0)})</strong> atingem o corte Elite (≥ 7 por semana) e
{low_freq} ({pct(low_freq / N, 0)}) ficam em Low (menos de uma por mês).</p>
<h3>RQ 02 — Lead time</h3>
<p>Mediana de <strong>{n(ltr, 1)} h ({n(ltr / 24, 1)} dias)</strong> por release e de
<strong>{n(ltc, 1)} h ({n(ltc / 24, 1)} dias)</strong> por commit. As variantes divergem porque (a) usa o commit
<em>mais antigo</em> de cada release, um máximo, enquanto (b) dilui esse commit entre todos os outros.</p>
<h3>RQ 03 — Taxa de falha</h3>
<p>Pelo proxy de CI a mediana é de <strong>{pct(cfr_a)}</strong>, bem dentro do Elite
(≤ 15%); pelo proxy de entrega, entre {pct(min(cfr_b.values()))} e
{pct(max(cfr_b.values()))} conforme a heurística. As duas variantes medem o mesmo conceito e discordam em quase
uma ordem de grandeza: o CFR (a) mede falha de pipeline no default branch (que costuma ser corrigida antes do merge);
o CFR (b) mede falha que chegou ao usuário e exigiu nova release.</p>
{t_cfrb}
<h3>RQ 04 — Tempo de recuperação</h3>
<p>Mediana de <strong>{n(rec, 2)} h</strong> (IQR {n(m('recovery_median_h', 'q1'), 2)} – {n(m('recovery_median_h', 'q3'), 2)} h).
{sem_rec} repositórios não tiveram nenhum episódio de falha e entram na classificação com três métricas, em vez de
receber um valor arbitrário. A censura é quase nula na mediana, mas alguns repositórios têm falhas nunca corrigidas
até o fim da janela.</p>
<div class="grid"><div class="card"><h4>RQ 01 — releases por semana</h4><p class="desc">Número de repositórios por faixa; cortes alinhados à tabela DORA.</p><div class="chart" style="height:260px"><canvas id="c-freq"></canvas></div></div><div class="card"><h4>RQ 04 — tempo de recuperação</h4><p class="desc">Mediana por repositório (276 com ao menos um episódio de falha).</p><div class="chart" style="height:260px"><canvas id="c-rec"></canvas></div></div></div>
<div class="grid"><div class="card"><h4>RQ 02 — lead time: (a) por release × (b) por commit</h4><p class="desc">Mesmo conceito, duas definições: a distribuição se desloca.</p><div class="chart" style="height:260px"><canvas id="c-lead"></canvas></div></div><div class="card"><h4>RQ 03 — CFR: (a) proxy de CI × (b) proxy de entrega</h4><p class="desc">O proxy de CI concentra tudo à esquerda; o de entrega se espalha.</p><div class="chart" style="height:260px"><canvas id="c-cfr"></canvas></div></div></div>
<h3>Classificação DORA de referência (C1)</h3>
<p>C1 = release | lead time (a) | CFR (a).</p>
<div class="card"><h4>Categoria DORA por métrica (C1)</h4><div class="chart"><canvas id="c-dora"></canvas></div></div>
<div class="grid">
<div class="card"><h4>Perfil médio da amostra</h4><p class="desc">Nota média por métrica (Elite = 4 … Low = 1). C1 contra C2: o perfil "estável e lento" encolhe quando o CFR muda.</p><div class="chart" style="height:300px"><canvas id="c-rad-perfil"></canvas></div></div>
<div class="card"><h4>Perfil por linguagem (C1)</h4><p class="desc">Nota média por métrica nas 4 linguagens mais comuns da amostra.</p><div class="chart" style="height:300px"><canvas id="c-rad-lang"></canvas></div></div>
</div>
<div class="card carta-wrap"><h4>Carta do repositório</h4><p class="desc">Escolha um repositório; os quatro atributos são as notas DORA (C1) numa escala de 0 a 100.</p>
<div class="carta"><div class="carta-lado"><select id="sel-repo" aria-label="Repositório"></select><div id="carta-info"></div></div><div class="chart" style="height:300px"><canvas id="c-rad-repo"></canvas></div></div></div>
<p>O perfil é de projetos <strong>estáveis e lentos</strong>: {elite_cfr} de {N} ({pct(elite_cfr / N, 0)}) são Elite
no CFR (a), mas só {pct(g.loc['deployment_frequency', 'pct_elite_ou_high'] / 100, 0)} são Elite ou High em frequência.
Essa nota alta em estabilidade vem do proxy mais otimista; a RQ 07 mostra o quanto ela se desfaz.</p>
<h3>RQ 05: frequência de deploy × CFR (Spearman)</h3>
{t_r5}
<p>Não há a relação negativa que o DORA sugere. Com o CFR (a) a correlação é positiva e fraca; com o CFR (b) é positiva e
<strong>forte</strong>. Parte disso pode ser <strong>mecânica</strong>: o CFR (b) conta a release que é seguida, em até 7 dias,
por uma corretiva, e quem publica com frequência tem mais chance de ter a próxima release dentro desse prazo (e a
heurística conta todo <em>patch</em> como correção). Os gráficos de dispersão estão em
<a href="resultados_rq05_rq06.html">resultados_rq05_rq06.html</a>.</p>
<h3>RQ 06: fatores associados às métricas DORA</h3>
<p>Quatro fatores (linguagem; estrelas, contribuidores e idade em quartis) contra nove métricas, 36 testes de
Kruskal-Wallis com correção de Holm. São significativos {len(sig)}:</p>
{t_r6}
<ul>
<li><strong>Idade:</strong> repositórios mais velhos publicam menos ({n(quartis.releases_por_semana.iloc[0], 2)} releases por
semana no primeiro quartil contra {n(quartis.releases_por_semana.iloc[3], 2)} no último), têm lead time muito maior
({n(quartis.lead_time_release_h.iloc[0], 0)} h contra {n(quartis.lead_time_release_h.iloc[3], 0)} h) e CFR (b) menor
({n(quartis.cfr_entrega_v4_combinada.iloc[0], 2)} contra {n(quartis.cfr_entrega_v4_combinada.iloc[3], 2)} na v4).</li>
<li><strong>Contribuidores:</strong> mais contribuidores, maior lead time ({n(contrib.iloc[0], 0)} h no primeiro quartil
contra {n(contrib.iloc[3], 0)} h no último).</li>
<li><strong>Sem efeito:</strong> estrelas; e nenhum fator para o tempo de recuperação nem para o CFR (a).</li>
</ul>
<p>Idade é um fator de confusão natural: repositórios mais velhos acumulam commits antigos, o que alonga o lead time (a),
que usa o commit mais antigo da release. O tipo do projeto (consenso da amostra-ouro) ainda não entrou como fator.</p>
</section>

<section id="sensibilidade">
<h2>4. Sensibilidade à definição operacional (RQ 07)</h2>
<p>Cinco combinações de definições. C1 é a referência; C2 troca os três eixos; C3, C4 e C5 mudam <strong>um</strong>
eixo cada a partir de C1, o que permite atribuir a diferença a um eixo só.</p>
{tabela(["Combinação", "Unidade de deploy", "Lead time", "CFR"],
        [["C1 (referência)", "release", "(a)", "(a) CI"],
         ["C2", "release + pré-release", "(b)", "(b) v2"], ["C3", "release", "(b)", "(a) CI"],
         ["C4", "release", "(a)", "(b) v2"], ["C5", "release + pré-release", "(a)", "(a) CI"]])}
<h3>Categoria geral por combinação</h3>
{t_dist7}
<div class="grid"><div class="card"><h4>Categoria geral em cada combinação</h4><p class="desc">Contagem de repositórios; o Elite encolhe e o Low cresce quando o CFR passa a ser (b).</p><div class="chart" style="height:260px"><canvas id="c-r7dist"></canvas></div></div><div class="card"><h4>% que mudou de categoria, por eixo</h4><p class="desc">Cada eixo isolado a partir de C1.</p><div class="chart" style="height:260px"><canvas id="c-r7eixo"></canvas></div></div></div>
<div class="grid"><div class="card"><h4>% que mudou, por par de combinações</h4><p class="desc">Quanto maior, menos robusta a classificação.</p><div class="chart" style="height:260px"><canvas id="c-r7par"></canvas></div></div><div class="card"><h4>Kappa linear ponderado, por par</h4><p class="desc">1 = concordância total; 0 = nada além do acaso.</p><div class="chart" style="height:260px"><canvas id="c-r7kappa"></canvas></div></div></div>
<div class="card"><h4>Transição C1 → C2 (categoria geral)</h4><p class="desc">Linhas: categoria em C1; colunas: categoria em C2. A diagonal são os que não mudaram.</p><div id="matriz"></div></div>
<h3>Concordância entre combinações</h3>
<p>Kappa de Cohen com ponderação linear (as categorias são ordenadas) e IC 95% por bootstrap dos repositórios.</p>
{t_pares}
<p>Entre a referência e a troca completa (C1 × C2) a concordância é apenas moderada: cerca de
<strong>{n(par('C1', 'C2', 'pct_mudou'), 0)} em cada 100 repositórios mudam de categoria</strong>, quase todos para pior.</p>
<h3>De onde vem a mudança</h3>
{t_eixos}
<p>A <strong>unidade de deploy quase não importa</strong>. O <strong>lead time</strong> pesa de forma moderada, nos
dois sentidos. O <strong>CFR domina</strong>: entre (a) e (b) o kappa fica próximo de zero, ou seja, não há
concordância além do acaso.</p>
<h3>A versão da heurística corretiva também importa</h3>
{t_heur}
<h3>Robustez da RQ 05 (Spearman, frequência × CFR)</h3>
{t_rho}
<div class="grid"><div class="card"><h4>Frequência × CFR (a), proxy de CI</h4><p class="desc">Cada ponto é um repositório; eixo x em escala log.</p><div class="chart" style="height:300px"><canvas id="c-da"></canvas></div></div><div class="card"><h4>Frequência × CFR (b), proxy de entrega</h4><p class="desc">Mesmos repositórios: a nuvem sobe e fica mais inclinada.</p><div class="chart" style="height:300px"><canvas id="c-db"></canvas></div></div></div>
<p>O sinal é positivo em todas as combinações, mas a força vai de fraca (ρ ≈ 0,18) a forte (ρ ≈ 0,7) conforme o CFR.
Parte da correlação com o CFR (b) pode ser mecânica (mais releases implicam mais releases de patch, e a heurística
semver as trata como correção); isto é uma hipótese não testada.</p>
</section>

{SECAO_R8}<section id="discussao">
<h2>6. Discussão</h2>
<p><strong>Os proxies discordam, e isso muda a conclusão.</strong> O CFR é a métrica em que a escolha da definição mais
pesa: o mesmo repositório é "Elite" pelo CI e "Medium" pela entrega. Isso reforça a leitura de que os proxies medem
fenômenos diferentes (falha de pipeline contra correção que chegou ao usuário) e de que resultados em categorias DORA
só fazem sentido acompanhados da definição usada.</p>
<p><strong>Velocidade e estabilidade não andam juntas, mas parte disso é efeito da definição.</strong> O DORA afirma que
as equipes de melhor desempenho vão bem nas duas dimensões. Aqui a frequência de deploy tem correlação positiva com a
taxa de falha. Duas leituras convivem. A primeira é substantiva: projetos que publicam muito podem mudar mais e quebrar
mais. A segunda é mecânica: o CFR (b) conta a release seguida de uma corretiva em até 7 dias, e quem publica com
frequência tem mais chance de ter a próxima release dentro desse prazo, e a heurística conta todo <em>patch</em> como
correção. O rework, que não depende do ritmo de releases, correlaciona pouco com a frequência, o que favorece a leitura
mecânica. Correlação, de qualquer forma, não implica causalidade.</p>
<p><strong>Idade é o fator mais associado, e é também um fator de confusão.</strong> Projetos mais novos publicam mais,
têm lead time menor e mais releases corretivas. Projetos antigos publicam menos e acumulam commits antigos, o que
alonga o lead time (a), que usa o commit mais antigo da release.</p>
<p><strong>O critério de "corretiva" é ambíguo.</strong> O kappa de {n(kap[kap.dimensao == "corretiva"].kappa.iloc[0], 2)} e a
divergência de um avaliador mostram que a própria definição precisa de refinamento antes de ser automatizada. Isso
limita o F1 alcançável.</p>
<h3>Robustez por questão de pesquisa</h3>
<ul>
<li><strong>RQ 01:</strong> a conclusão é robusta; contar pré-releases move poucas categorias de frequência.</li>
<li><strong>RQ 02:</strong> o lead time de dias, não de horas, vale nas duas variantes, mas a categoria muda para
parte dos repositórios conforme (a) ou (b).</li>
<li><strong>RQ 03:</strong> depende totalmente da definição. Resultados de estabilidade devem apresentar as duas
variantes de CFR lado a lado, nunca só uma.</li>
<li><strong>RQ 05:</strong> o sinal (positivo) é robusto, a magnitude não.</li>
<li><strong>Em geral:</strong> a classificação DORA não é robusta à definição operacional, e toda categoria deve ser
reportada junto com a combinação que a produziu.</li>
</ul>
{pendente("comparação com as hipóteses informais do grupo (o que se esperava, o que surpreendeu e por quê): depende das hipóteses originais da issue #62.")}
</section>

<section id="ameacas">
<h2>7. Ameaças à validade</h2>
<p>Rascunho; a seção final é dos três integrantes.</p>
<ul>
<li><strong>Construto:</strong> release publicada não é deploy, e CI vermelho não é falha em produção: o segundo proxy
subestima sistematicamente a instabilidade. A <code>author_date</code> é distorcida por rebase e squash merge, e commits
com data posterior à release contam como 0 h. A heurística corretiva tem erro relevante: nenhuma versão v1 a v4 atinge
F1 de 0,70, a v5 (F1 = {n(melhor.f1, 3)}) foi escolhida olhando a própria amostra (nas 33 releases fora da escolha o F1 foi
0,65), e o CFR (b) pode estar correlacionado com a frequência de deploy por construção. Tags não foram usadas como
unidade de deploy (a API não traz data e não foram coletados commits entre tags).</li>
<li><strong>Interna:</strong> repositórios mais antigos acumulam mais releases e commits antigos, e a idade se associa a
várias métricas (RQ 06). O tipo do projeto, que seria um quinto fator, não entrou na análise.</li>
<li><strong>Externa:</strong> repositórios populares com Actions e releases regulares; não representa projetos privados
nem os que publicam sem releases do GitHub. A janela é de 12 meses, e os repositórios seguem recebendo commits, o que
afeta a replicação.</li>
<li><strong>Conclusão:</strong> são 36 testes no RQ 06, corrigidos por Holm, e alguns grupos têm poucos repositórios
(linguagens raras). A amostra-ouro tem 300 releases de 60 repositórios, e o kappa de Fleiss é razoável (≈ 0,3) em duas
das três dimensões, com um avaliador bem mais permissivo que os outros dois (que concordam entre si em 93,7%). A censura
foi tratada (releases dos últimos 7 dias ficam fora do CFR (b)), mas episódios de falha sem recuperação reduzem o tempo de
recuperação medido.</li>
</ul>
</section>

<section id="replicacao">
<h2>8. Replicação cruzada</h2>
{pendente("execução do pipeline de outro grupo, comparação com o CSV original e resposta às Issues recebidas (entrega final).")}
</section>

<section id="conclusao">
<h2>9. Conclusão</h2>
<p>Medimos as métricas DORA em {N} repositórios populares e mostramos que o valor da métrica depende mais da definição
operacional do que se poderia esperar. A taxa de falha varia quase uma ordem de grandeza entre os dois proxies, e
{n(par('C1', 'C2', 'pct_mudou'), 1)}% dos repositórios mudam de categoria quando as definições mudam. A frequência de deploy
não se associa a menos falhas, e a idade é o fator mais ligado ao desempenho. A validação manual mostrou que a
classificação de release corretiva é ambígua e que a heurística automática tem desempenho limitado. Como trabalho futuro:
refinar o critério de "release corretiva" com mais avaliadores, usar tags como unidade de deploy e aplicar a v5 ao
conjunto de dados.</p>
<p>Código, dados e resultados: <a href="https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06">repositório do grupo</a>;
processo: <a href="https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/projects">GitHub Projects</a>.</p>
</section>

<section id="referencias">
<h2>Referências</h2>
<ol class="refs">
<li id="r1">Forsgren, N.; Humble, J.; Kim, G. <em>Accelerate: The Science of Lean Software and DevOps</em>. IT Revolution, 2018.</li>
<li id="r2">DORA. <em>DORA's software delivery metrics: the four keys</em>. <a href="https://dora.dev/guides/dora-metrics-four-keys/">dora.dev/guides/dora-metrics-four-keys</a>.</li>
<li id="r3">Wohlin, C. et al. <em>Experimentation in Software Engineering</em>. Springer, 2012.</li>
<li id="r4">Romano, J.; Kromrey, J. D.; Coraggio, J.; Skowronek, J. Appropriate statistics for ordinal level data. 2006.</li>
<li id="r5">Landis, J. R.; Koch, G. G. The measurement of observer agreement for categorical data. <em>Biometrics</em>, 33(1):159–174, 1977.</li>
<li id="r6">Preston-Werner, T. <em>Versionamento Semântico 2.0.0</em>. <a href="https://semver.org/lang/pt-BR/">semver.org</a>.</li>
</ol>
</section>
</main>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script>const DATA = {dados};
{JS}</script>
<footer>Gerado por <code>scripts/gerar_relatorio_html.py</code> a partir de <code>data/</code>.</footer>
</body>
</html>
"""


CSS = """
:root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#fff;--page-plane:#f4f3ef;--text-primary:#0b0b0b;
--text-secondary:#52514e;--text-muted:#898781;--gridline:#e1e0d9;--border:rgba(11,11,11,.10);--acc:#2a78d6;
--series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;
--elite:#184f9e;--high:#2a78d6;--medium:#7fb0ea;--low:#c9def7;
--warn:#fff4d6;--warnb:#e1a93b;--shadow:0 1px 2px rgba(11,11,11,.04),0 8px 24px rgba(11,11,11,.05)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--surface-1:#17181a;
--surface-2:#1e1f22;--page-plane:#0c0d0e;--text-primary:#fff;--text-secondary:#c3c2b7;--gridline:#2c2c2a;
--border:rgba(255,255,255,.10);--acc:#4a92f0;--series-1:#4a92f0;--series-2:#f2793b;--series-3:#24c98a;
--elite:#b3d4fa;--high:#5a9df2;--medium:#3a78cc;--low:#2f5a9e;--warn:#2e2812;--warnb:#a88326;
--shadow:0 1px 2px rgba(0,0,0,.3),0 12px 28px rgba(0,0,0,.35)}}
*{box-sizing:border-box}
body{margin:0;background:var(--page-plane);color:var(--text-primary);
font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}
.topo,main,.indice,footer,.kpi-row{max-width:980px;margin:0 auto;padding-left:16px;padding-right:16px}
.topo{padding-top:40px}
.sobre{margin:0;color:var(--text-muted);font-size:.8rem;letter-spacing:.05em;text-transform:uppercase}
h1{font-size:2rem;line-height:1.2;margin:.3em 0 .2em;letter-spacing:-.01em}
.autores{margin:0;font-weight:600}.meta{color:var(--text-secondary);margin:.3em 0 0}
.selo{background:var(--warn);border:1px solid var(--warnb);border-radius:99px;padding:1px 10px;font-size:.8rem}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;padding-top:22px;padding-bottom:6px}
.kpi{background:var(--surface-2);border:1px solid var(--border);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);
transition:transform .15s}.kpi:hover{transform:translateY(-2px)}
.kpi .label{font-size:11px;color:var(--text-secondary);margin-bottom:6px;text-transform:uppercase;letter-spacing:.03em}
.kpi .value{font-size:24px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.indice{display:flex;flex-wrap:wrap;gap:6px 14px;padding-top:14px;padding-bottom:12px;position:sticky;top:0;
background:var(--page-plane);z-index:2;font-size:.88rem;border-bottom:1px solid var(--border)}
.indice a{color:var(--acc);text-decoration:none}.indice a:hover{text-decoration:underline}
main>section{background:var(--surface-1);border:1px solid var(--border);border-radius:16px;padding:6px 24px 20px;margin:18px 0}
h2{margin:1.1em 0 .4em;font-size:1.4rem;letter-spacing:-.01em}h3{margin:1.6em 0 .3em;font-size:1.08rem}
code{background:var(--page-plane);border-radius:4px;padding:1px 5px;font-size:.88em}
.tabela{overflow-x:auto;margin:1em 0}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{padding:7px 10px;border-bottom:1px solid var(--gridline);text-align:left;vertical-align:top}
th{background:var(--page-plane);font-weight:600;white-space:nowrap}
table.num td{font-variant-numeric:tabular-nums}
.rqs li{margin:.3em 0}
.pendente{background:var(--warn);border-left:4px solid var(--warnb);padding:8px 14px;border-radius:6px;font-size:.92rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px;margin:14px 0}
.card{background:var(--surface-2);border:1px solid var(--border);border-radius:14px;padding:16px 18px;
box-shadow:var(--shadow);margin:14px 0}.grid .card{margin:0}
.card h4{font-size:.95rem;margin:0 0 3px}.card .desc{font-size:.78rem;color:var(--text-muted);margin:0 0 10px;line-height:1.4}
.chart{position:relative;height:280px}
.matriz{width:100%;border-collapse:separate;border-spacing:3px;text-align:center;font-variant-numeric:tabular-nums}
.matriz th{background:none;text-align:center;font-size:.8rem;color:var(--text-secondary)}
.matriz td{border-radius:6px;padding:12px 6px;font-weight:600;border:0}
.carta{display:grid;grid-template-columns:minmax(220px,1fr) 1.2fr;gap:18px;align-items:center}
.carta select{width:100%;padding:8px 10px;border-radius:8px;border:1px solid var(--border);background:var(--surface-1);color:var(--text-primary);font:inherit;font-size:.85rem}
.carta .geral{font-size:3.2rem;font-weight:800;line-height:1;margin:14px 0 2px;letter-spacing:-.02em;color:var(--series-1)}
.carta .sub{color:var(--text-secondary);font-size:.85rem}
.carta ul{list-style:none;padding:0;margin:12px 0 0}.carta li{display:flex;justify-content:space-between;border-bottom:1px solid var(--gridline);padding:4px 0;font-size:.85rem}
.carta li b{font-variant-numeric:tabular-nums}
@media (max-width:700px){.carta{grid-template-columns:1fr}}
a{color:var(--acc)}.refs li{margin:.4em 0}
footer{padding:20px 16px 50px;color:var(--text-muted);font-size:.82rem}
@media (max-width:600px){h1{font-size:1.6rem}main>section{padding:4px 14px 14px}.grid{grid-template-columns:1fr}}
"""

JS = """
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const cat = () => [css('--elite'), css('--high'), css('--medium'), css('--low')];
const txt = css('--text-secondary'), grid = css('--gridline');
Chart.defaults.font.family = 'system-ui,-apple-system,"Segoe UI",sans-serif';
Chart.defaults.color = txt; Chart.defaults.animation = {duration: 700, easing: 'easeOutQuart'};
const NOMES = ['Elite', 'High', 'Medium', 'Low'];
const ESC = {y: {beginAtZero: true, grid: {color: grid}, border: {display: false}}, x: {grid: {display: false}}};
const leg = {position: 'bottom', labels: {boxWidth: 10, font: {size: 11}}};

document.getElementById('kpis').innerHTML = DATA.kpis.map(([l, v]) =>
  `<div class="kpi"><div class="label">${l}</div><div class="value">${v}</div></div>`).join('');

function barras(id, rotulos, series, opc = {}) {
  new Chart(document.getElementById(id), {type: 'bar',
    data: {labels: rotulos, datasets: series.map(s => ({borderRadius: 6, borderSkipped: false, maxBarThickness: 46, ...s}))},
    options: {responsive: true, maintainAspectRatio: false, indexAxis: opc.h ? 'y' : 'x',
      plugins: {legend: series.length > 1 ? leg : {display: false}},
      scales: opc.h ? {x: {beginAtZero: true, grid: {color: grid}, border: {display: false}, max: opc.max},
                       y: {grid: {display: false}}} : ESC}});
}

// DORA C1: barras horizontais empilhadas, uma por métrica (categorias ordenadas = uma só cor, do escuro ao claro)
const dims = Object.keys(DATA.dora);
new Chart(document.getElementById('c-dora'), {type: 'bar',
  data: {labels: dims.map(d => DATA.dim_nomes[d]),
    datasets: NOMES.map((c, i) => ({label: c, data: dims.map(d => DATA.dora[d][i]),
      backgroundColor: cat()[i], borderColor: css('--surface-2'), borderWidth: 2, borderRadius: 4}))},
  options: {responsive: true, maintainAspectRatio: false, indexAxis: 'y',
    plugins: {legend: leg}, scales: {x: {stacked: true, grid: {color: grid}, border: {display: false}},
      y: {stacked: true, grid: {display: false}}}}});

barras('c-freq', DATA.freq.rotulos, [{label: 'repositórios', data: DATA.freq.n, backgroundColor: css('--series-1')}]);
barras('c-rec', DATA.rec.rotulos, [{label: 'repositórios', data: DATA.rec.n, backgroundColor: css('--series-3')}]);
barras('c-lead', DATA.lead.rotulos, [
  {label: '(a) por release', data: DATA.lead.a, backgroundColor: css('--series-1')},
  {label: '(b) por commit', data: DATA.lead.b, backgroundColor: css('--series-2')}]);
barras('c-cfr', DATA.cfr.rotulos, [
  {label: '(a) proxy de CI', data: DATA.cfr.a, backgroundColor: css('--series-1')},
  {label: '(b) proxy de entrega', data: DATA.cfr.b, backgroundColor: css('--series-2')}]);

// RQ 07
const comb = Object.keys(DATA.r7_dist);
new Chart(document.getElementById('c-r7dist'), {type: 'bar',
  data: {labels: comb, datasets: NOMES.map((c, i) => ({label: c, data: comb.map(k => DATA.r7_dist[k][i]),
    backgroundColor: cat()[i], borderColor: css('--surface-2'), borderWidth: 2, borderRadius: 4}))},
  options: {responsive: true, maintainAspectRatio: false, plugins: {legend: leg},
    scales: {x: {stacked: true, grid: {display: false}}, y: {stacked: true, grid: {color: grid}, border: {display: false}}}}});
barras('c-r7eixo', DATA.r7_eixos.rotulos, [{label: '% que mudou', data: DATA.r7_eixos.mudou,
  backgroundColor: css('--series-2')}], {h: true, max: 100});
barras('c-r7par', DATA.r7_pares.rotulos, [{label: '% que mudou', data: DATA.r7_pares.mudou,
  backgroundColor: css('--series-2')}], {h: true, max: 100});
barras('c-r7kappa', DATA.r7_pares.rotulos, [{label: 'kappa linear', data: DATA.r7_pares.kappa,
  backgroundColor: css('--series-1')}], {h: true, max: 1});

// matriz de transição C1 -> C2 (intensidade = nº de repositórios)
(() => {
  const v = DATA.matriz.v, max = Math.max(...v.flat());
  const rgb = css('--series-1');
  let h = '<table class="matriz"><tr><th>C1 ↓ · C2 →</th>' + NOMES.map(n => `<th>${n}</th>`).join('') + '</tr>';
  v.forEach((l, i) => {
    h += `<tr><th>${NOMES[i]}</th>` + l.map((x, j) => {
      const a = x ? .12 + .78 * x / max : 0;
      return `<td style="background:color-mix(in srgb, ${rgb} ${Math.round(a * 100)}%, transparent);` +
        `${i === j ? 'outline:2px solid ' + css('--text-muted') + ';outline-offset:-2px;' : ''}">${x}</td>`;
    }).join('') + '</tr>';
  });
  document.getElementById('matriz').innerHTML = h + '</table>';
})();

// dispersão frequência x CFR (log no x)
function dispersao(id, pts, cor) {
  new Chart(document.getElementById(id), {type: 'scatter',
    data: {datasets: [{data: pts, backgroundColor: cor + '99', borderColor: cor, pointRadius: 3, pointHoverRadius: 5}]},
    options: {responsive: true, maintainAspectRatio: false,
      plugins: {legend: {display: false}, tooltip: {callbacks: {label: c =>
        `${c.parsed.x.toFixed(2)} releases/sem · CFR ${(c.parsed.y * 100).toFixed(1)}%`}}},
      scales: {x: {type: 'logarithmic', title: {display: true, text: 'releases por semana (log)'}, grid: {color: grid}},
               y: {min: 0, max: 1, title: {display: true, text: 'CFR'}, grid: {color: grid},
                   ticks: {callback: v => (v * 100) + '%'}}}}});
}

// radares (estilo carta): 4 eixos, escala 0-4
const radOpc = (max, min = 0) => ({responsive: true, maintainAspectRatio: false,
  plugins: {legend: leg}, scales: {r: {min, max, ticks: {display: false, stepSize: max / 4},
    grid: {color: grid}, angleLines: {color: grid}, pointLabels: {font: {size: 12, weight: '600'}, color: txt}}}});
const serieRad = (label, data, cor) => ({label, data, borderColor: cor, backgroundColor: cor + '2e',
  pointBackgroundColor: cor, borderWidth: 2, pointRadius: 3});
new Chart(document.getElementById('c-rad-perfil'), {type: 'radar',
  data: {labels: DATA.radar_eixos, datasets: [
    serieRad('C1 (referência)', DATA.radar_perfil.C1, css('--series-1')),
    serieRad('C2 (lead time b, CFR b, + pré-release)', DATA.radar_perfil.C2, css('--series-2'))]},
  options: radOpc(4, 1)});
const corLang = [css('--series-1'), css('--series-2'), css('--series-3'), '#8b5cf6'];
new Chart(document.getElementById('c-rad-lang'), {type: 'radar',
  data: {labels: DATA.radar_eixos, datasets: Object.entries(DATA.radar_lang).map(([k, o], i) =>
    serieRad(`${k} (n=${o.n})`, o.v, corLang[i]))},
  options: radOpc(4, 1)});

const sel = document.getElementById('sel-repo');
sel.innerHTML = DATA.repos.map((r, i) => `<option value="${i}">${r.n}</option>`).join('');
const radRepo = new Chart(document.getElementById('c-rad-repo'), {type: 'radar',
  data: {labels: DATA.radar_eixos, datasets: [serieRad('', [0, 0, 0, 0], css('--series-1'))]},
  options: {...radOpc(100), plugins: {legend: {display: false}}}});
function carta() {
  const r = DATA.repos[sel.value];
  radRepo.data.datasets[0].data = r.v.map(x => x === null ? null : x * 25);
  radRepo.update();
  document.getElementById('carta-info').innerHTML =
    `<div class="geral">${r.g}</div><div class="sub">${r.l} · ${r.s.toLocaleString('pt-BR')} estrelas</div><ul>` +
    DATA.radar_eixos.map((e, i) => `<li><span>${e}</span><b>${r.v[i] === null ? '—' : r.v[i] * 25}</b></li>`).join('') + '</ul>';
}
sel.addEventListener('change', carta); carta();

// validação manual
barras('c-kappa', DATA.val.dims, [{label: 'kappa de Fleiss', data: DATA.val.kappa, backgroundColor: css('--series-1')}],
  {h: true, max: 1});
barras('c-f1', DATA.val.variantes, [
  {label: 'Precisão', data: DATA.val.precisao, backgroundColor: css('--series-1')},
  {label: 'Recall', data: DATA.val.recall, backgroundColor: css('--series-3')},
  {label: 'F1', data: DATA.val.f1, backgroundColor: css('--series-2')}]);

// RQ 08
barras('c-r8-med', DATA.r8.versoes, [
  {label: 'Rework rate', data: DATA.r8.rework, backgroundColor: css('--series-1')},
  {label: 'CFR (b)', data: DATA.r8.cfr_b, backgroundColor: css('--series-2')}]);
barras('c-r8-rho', DATA.r8.versoes, [
  {label: 'rework × frequência', data: DATA.r8.rho_rework, backgroundColor: css('--series-1')},
  {label: 'CFR (b) × frequência', data: DATA.r8.rho_cfr, backgroundColor: css('--series-2')}]);
new Chart(document.getElementById('c-r8-disp'), {type: 'scatter',
  data: {datasets: [
    {data: DATA.r8.disp.map(p => ({x: p.x * 100, y: p.y * 100})), backgroundColor: css('--series-1') + '99',
     borderColor: css('--series-1'), pointRadius: 3, pointHoverRadius: 5},
    {data: [{x: 0, y: 0}, {x: 100, y: 100}], type: 'line', borderColor: css('--text-muted'), borderDash: [6, 4],
     borderWidth: 1, pointRadius: 0}]},
  options: {responsive: true, maintainAspectRatio: false,
    plugins: {legend: {display: false}, tooltip: {callbacks: {label: c =>
      `CFR (b) ${c.parsed.x.toFixed(1)}% · rework ${c.parsed.y.toFixed(1)}%`}}},
    scales: {x: {min: 0, max: 100, title: {display: true, text: 'CFR (b) %'}, grid: {color: grid}},
             y: {min: 0, max: 100, title: {display: true, text: 'rework rate %'}, grid: {color: grid}}}}});

dispersao('c-da', DATA.disp_a, css('--series-1'));
dispersao('c-db', DATA.disp_b, css('--series-2'));
"""


def main(argv=None):
    parser = argparse.ArgumentParser(prog="scripts.gerar_relatorio_html", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=os.path.join(RAIZ, "config.json"))
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    pagina = montar(cfg)
    caminho = os.path.join(RAIZ, "docs", "index.html")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(pagina)
    print(f"relatório -> {caminho}")


if __name__ == "__main__":
    main()
