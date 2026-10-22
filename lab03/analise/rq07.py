"""RQ 07: sensibilidade da classificação DORA à definição operacional (issue #73).

Pergunta: o quanto a categoria DORA de um repositório depende de *como* cada
métrica foi definida? Cada **combinação** escolhe uma definição para as três
métricas que têm variantes (frequência, lead time, CFR); o tempo de recuperação
sai dos workflow runs, que não têm variante, e é igual em todas as combinações.

| Combinação | Unidade de deploy        | Lead time | CFR                 | Para quê |
|------------|--------------------------|-----------|---------------------|----------|
| C1         | release                  | (a)       | (a) proxy de CI     | referência |
| C2         | release + pré-release    | (b)       | (b) `v2`            | troca tudo (exemplo do enunciado) |
| C3         | release                  | (b)       | (a) proxy de CI     | isola o efeito do lead time |
| C4         | release                  | (a)       | (b) `v2`            | isola o efeito do CFR |
| C5         | release + pré-release    | (a)       | (a) proxy de CI     | isola o efeito da unidade de deploy |

C3, C4 e C5 mudam **um** eixo por vez a partir de C1, então a diferença de C1 para
cada uma delas é atribuível a um único eixo; C2 mostra o efeito acumulado.

**Tag como unidade de deploy não foi usada.** O enunciado cita tags como variante,
mas a API de tags não traz data (o enunciado manda usar a do commit apontado), e a
coleta só buscou commits entre releases publicadas, não entre tags. Datar as tags
exigiria uma nova coleta; fica registrado como limitação no artigo.

Por par de combinações calcula-se a **% de repositórios que mudaram de categoria
geral** e o **kappa de Cohen ponderado linear** (as categorias são ordenadas: Elite→High
pesa menos que Elite→Low), com IC 95% por bootstrap dos repositórios.

Saídas em `data/analise/`:
  rq07_classificacoes.csv       categoria de cada repositório em cada combinação
  rq07_distribuicao.csv         quantos repositórios em cada categoria, por combinação
  rq07_pares.csv                % que mudou, direção e kappa linear, por par (categoria geral)
  rq07_por_metrica.csv          o mesmo por métrica individual (onde a mudança nasce)
  rq07_heuristica_corretiva.csv C1 contra o CFR (b) com cada versão da heurística corretiva
  rq07_robustez_rq05.csv        Spearman entre frequência e CFR em cada combinação

Uso:
    python -m analise.rq07 --config config.json
"""
import argparse
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

from metricas.dora import CATEGORIAS, METRICAS, PONTOS, classificar_repo

SEMENTE = 42
REPLICAS_BOOTSTRAP = 1000

# nome -> descrição curta e colunas usadas. `frequencia` é uma coluna de
# `dataset.csv` ou o marcador PRE para "release + pré-release", calculado a partir
# do Parquet de releases (o dataset só tem a contagem sem pré-releases).
PRE = "__release_mais_pre__"
COMBINACOES = {
    "C1": {"unidade": "release", "lead_time": "(a)", "cfr": "(a)",
           "colunas": {"deployment_frequency": "releases_por_semana",
                       "lead_time": "lead_time_release_h",
                       "change_failure_rate": "cfr_ci"}},
    "C2": {"unidade": "release + pré-release", "lead_time": "(b)", "cfr": "(b) v5",
           "colunas": {"deployment_frequency": PRE,
                       "lead_time": "lead_time_commit_h",
                       "change_failure_rate": "cfr_entrega_v5_patch_e_notas"}},
    "C3": {"unidade": "release", "lead_time": "(b)", "cfr": "(a)",
           "colunas": {"deployment_frequency": "releases_por_semana",
                       "lead_time": "lead_time_commit_h",
                       "change_failure_rate": "cfr_ci"}},
    "C4": {"unidade": "release", "lead_time": "(a)", "cfr": "(b) v5",
           "colunas": {"deployment_frequency": "releases_por_semana",
                       "lead_time": "lead_time_release_h",
                       "change_failure_rate": "cfr_entrega_v5_patch_e_notas"}},
    "C5": {"unidade": "release + pré-release", "lead_time": "(a)", "cfr": "(a)",
           "colunas": {"deployment_frequency": PRE,
                       "lead_time": "lead_time_release_h",
                       "change_failure_rate": "cfr_ci"}},
}
RECUPERACAO = "recovery_median_h"

# Versões da heurística corretiva que o dataset traz para o CFR (b).
VERSOES_CFR_B = {
    "v5_patch_e_notas": "cfr_entrega_v5_patch_e_notas",   # referencia do grupo
    "v1_semver": "cfr_entrega_v1_semver",
    "v2_semver_ou_nome": "cfr_entrega_v2_semver_ou_nome",
    "v3_commits": "cfr_entrega_v3_commits",
    "v4_combinada": "cfr_entrega_v4_combinada",
}

ORDEM = {cat: PONTOS[cat] for cat in CATEGORIAS}   # Elite=4 ... Low=1


# ---------------------------------------------------------------- classificação

def _numero(valor):
    if valor is None:
        return None
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(n) else n


def frequencia_com_pre(releases, inicio, fim):
    """Releases + pré-releases por semana, por repositório.

    Mesma conta da RQ 01 (contagem ÷ semanas da janela); só muda o que conta como
    deploy. Rascunhos nunca contam. Repositórios sem nenhuma release na janela
    aparecem com 0 (nunca acontece na amostra, que exige >= 5)."""
    janela = releases[(~releases["draft"].astype(bool)) & (releases["in_window"].astype(bool))]
    semanas = ((pd.Timestamp(fim) - pd.Timestamp(inicio)).days + 1) / 7
    return janela.groupby("repo").size() / semanas


def classificar_combinacao(df, colunas):
    """Classificação DORA de cada linha de `df` usando as colunas da combinação.

    O tempo de recuperação entra sempre da mesma coluna. Devolve um DataFrame
    indexado como `df`, com `dora_<metrica>` por métrica e `dora_geral`."""
    linhas = []
    for _, row in df.iterrows():
        valores = {nome: _numero(row.get(col)) for nome, col in colunas.items()}
        valores["recovery_time"] = _numero(row.get(RECUPERACAO))
        linhas.append(classificar_repo(valores))
    out = pd.DataFrame(linhas, index=df.index)
    return out.drop(columns=["dora_metricas_validas"])


def classificar_todas(df, combinacoes=None):
    """{combinação: DataFrame de classificações}, uma linha por repositório de `df`."""
    combinacoes = combinacoes or COMBINACOES
    return {nome: classificar_combinacao(df, c["colunas"]) for nome, c in combinacoes.items()}


# ------------------------------------------------------------------ concordância

def _pontos(serie):
    return serie.map(ORDEM)


def comparar(a, b, rotulo_a="A", rotulo_b="B", replicas=0, semente=SEMENTE):
    """Concordância entre duas classificações (Series de categorias, mesmo índice).

    Só entram repositórios classificados nas duas — `n` informa quantos. Devolve
    % que mudou, % que subiu (B melhor que A) e desceu, e o kappa linear. Com
    `replicas` > 0 acrescenta o IC 95% do kappa por bootstrap dos repositórios.

    Kappa vira NaN quando uma das classificações tem uma classe só (não há
    variação para concordar): é indefinido, não zero."""
    ambos = pd.DataFrame({"a": _pontos(a), "b": _pontos(b)}).dropna()
    n = len(ambos)
    if n == 0:
        return {"a": rotulo_a, "b": rotulo_b, "n": 0, "pct_mudou": None, "pct_subiu": None,
                "pct_desceu": None, "kappa_linear": None, "kappa_ic_inf": None,
                "kappa_ic_sup": None}
    ya, yb = ambos["a"].astype(int).to_numpy(), ambos["b"].astype(int).to_numpy()
    linha = {"a": rotulo_a, "b": rotulo_b, "n": n,
             "pct_mudou": round(100 * float((ya != yb).mean()), 1),
             "pct_subiu": round(100 * float((yb > ya).mean()), 1),
             "pct_desceu": round(100 * float((yb < ya).mean()), 1),
             "kappa_linear": _kappa(ya, yb)}
    inf = sup = None
    if replicas:
        rng = np.random.default_rng(semente)
        ks = []
        for _ in range(replicas):
            i = rng.integers(0, n, n)
            k = _kappa(ya[i], yb[i], arredondar=False)
            if k is not None:
                ks.append(k)
        if ks:
            inf, sup = (round(float(x), 3) for x in np.percentile(ks, [2.5, 97.5]))
    linha["kappa_ic_inf"], linha["kappa_ic_sup"] = inf, sup
    return linha


def _kappa(ya, yb, arredondar=True):
    # `labels` fixo mantém a distância Elite-Low = 3 mesmo se uma categoria não
    # aparecer; sem ele a ponderação usaria só as classes presentes.
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore")   # "só uma classe em comum": já tratado abaixo (NaN)
        k = cohen_kappa_score(ya, yb, labels=[1, 2, 3, 4], weights="linear")
    if np.isnan(k):
        return None
    return round(float(k), 3) if arredondar else float(k)


def tabela_pares(classes, coluna="dora_geral", replicas=0):
    """Uma linha por par de combinações, na coluna de classificação dada."""
    linhas = []
    for a, b in itertools.combinations(classes, 2):
        linhas.append(comparar(classes[a][coluna], classes[b][coluna], a, b, replicas))
    return pd.DataFrame(linhas).rename(columns={"a": "combinacao_a", "b": "combinacao_b"})


def tabela_por_metrica(classes):
    """Como `tabela_pares`, mas por métrica: mostra em qual eixo a mudança nasce."""
    quadros = []
    for nome in METRICAS:
        t = tabela_pares(classes, f"dora_{nome}")
        t.insert(0, "metrica", nome)
        quadros.append(t)
    return pd.concat(quadros, ignore_index=True)


def distribuicao(classes):
    linhas = []
    for nome, c in classes.items():
        cont = c["dora_geral"].value_counts()
        linhas.append({"combinacao": nome,
                       **{cat: int(cont.get(cat, 0)) for cat in CATEGORIAS},
                       "sem_classificacao": int(c["dora_geral"].isna().sum())})
    return pd.DataFrame(linhas)


# --------------------------------------------------- CFR (b) e robustez da RQ 05

def heuristica_corretiva(df, c1):
    """C1 contra C1 com o CFR trocado por cada versão da heurística corretiva.

    Mostra o quanto a escolha da versão da heurística (e não só (a) contra (b))
    muda a categoria geral."""
    base = df.copy()
    linhas = []
    cols = COMBINACOES["C1"]["colunas"]
    for versao, coluna in VERSOES_CFR_B.items():
        colunas = {**cols, "change_failure_rate": coluna}
        outra = classificar_combinacao(base, colunas)
        linhas.append({"cfr_b": versao,
                       "mediana_cfr": round(float(pd.to_numeric(base[coluna]).median()), 4),
                       **comparar(c1["dora_geral"], outra["dora_geral"], "C1", f"C1+{versao}")})
    return pd.DataFrame(linhas).drop(columns=["a"]).rename(columns={"b": "comparada"})


def robustez_rq05(df, combinacoes=None):
    """Spearman entre frequência de deploy e CFR sob cada combinação (RQ 05).

    Se o sinal de ρ ou a conclusão de significância mudam entre combinações, a
    resposta da RQ 05 depende da definição escolhida."""
    combinacoes = combinacoes or COMBINACOES
    linhas = []
    for nome, c in combinacoes.items():
        x = pd.to_numeric(df[c["colunas"]["deployment_frequency"]], errors="coerce")
        y = pd.to_numeric(df[c["colunas"]["change_failure_rate"]], errors="coerce")
        ok = x.notna() & y.notna()
        if ok.sum() < 3 or x[ok].nunique() < 2 or y[ok].nunique() < 2:
            rho = p = None
        else:
            res = spearmanr(x[ok], y[ok])
            rho, p = round(float(res.statistic), 3), float(res.pvalue)
        linhas.append({"combinacao": nome, "unidade": c["unidade"], "cfr": c["cfr"],
                       "n": int(ok.sum()), "rho": rho, "p_valor": p})
    return pd.DataFrame(linhas)


# ----------------------------------------------------------------------- execução

def carregar_dataset(data_dir, janela):
    """`dataset.csv` com a coluna da frequência release + pré-release acrescentada."""
    df = pd.read_csv(os.path.join(data_dir, "dataset.csv"))
    releases = pd.read_parquet(os.path.join(data_dir, "parquet", "releases.parquet"),
                               columns=["repo", "draft", "in_window"])
    freq = frequencia_com_pre(releases, *janela)
    df[PRE] = df["full_name"].map(freq).fillna(0.0)
    return df


def executar(data_dir, janela):
    df = carregar_dataset(data_dir, janela)
    classes = classificar_todas(df)
    saida = os.path.join(data_dir, "analise")
    os.makedirs(saida, exist_ok=True)

    por_repo = pd.concat({n: c for n, c in classes.items()}, axis=1)
    por_repo.columns = [f"{n}_{c.replace('dora_', '')}" for n, c in por_repo.columns]
    por_repo.insert(0, "full_name", df["full_name"].to_numpy())
    pares = tabela_pares(classes, replicas=REPLICAS_BOOTSTRAP)
    por_metrica = tabela_por_metrica(classes)
    dist = distribuicao(classes)
    heur = heuristica_corretiva(df, classes["C1"])
    rob = robustez_rq05(df)

    for nome, t in {"classificacoes": por_repo, "distribuicao": dist, "pares": pares,
                    "por_metrica": por_metrica, "heuristica_corretiva": heur,
                    "robustez_rq05": rob}.items():
        t.to_csv(os.path.join(saida, f"rq07_{nome}.csv"), index=False)
    return df, classes, pares, por_metrica, dist, heur, rob


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="analise.rq07", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    df, classes, pares, por_metrica, dist, heur, rob = executar(
        cfg["data_dir"], (cfg["window_start"], cfg["window_end"]))

    print("=" * 78)
    print(f"RQ 07: sensibilidade da classificação DORA — {len(df)} repositórios")
    print("=" * 78)
    print("\nCombinações:")
    for nome, c in COMBINACOES.items():
        print(f"  {nome}: unidade={c['unidade']}, lead time {c['lead_time']}, CFR {c['cfr']}")
    print("\nDistribuição da categoria geral:\n" + dist.to_string(index=False))
    print("\nPares (categoria geral):\n" + pares.to_string(index=False))
    print("\nPor métrica:\n" + por_metrica.to_string(index=False))
    print("\nHeurística corretiva (C1 contra C1 + CFR b):\n" + heur.to_string(index=False))
    print("\nRobustez da RQ 05 (Spearman frequência × CFR):\n" + rob.to_string(index=False))
    print(f"\nSaídas em {os.path.join(cfg['data_dir'], 'analise')}/rq07_*.csv")


if __name__ == "__main__":
    main()
