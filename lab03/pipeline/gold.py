"""Amostra-ouro (seção 6): sorteio, planilhas de rotulagem, kappa de Fleiss, consenso e F1.

Uso (a partir de `lab03/`):
    python -m pipeline.gold sortear --config config.json --raters ana,bia,caio
    python -m pipeline.gold kappa   --config config.json --raters ana,bia,caio
    python -m pipeline.gold avaliar --config config.json --versao v2
"""
import argparse
import csv
import json
import os
import random
from collections import Counter

SEED = 42
N_REPOS = 60
N_RELEASES = 5
TIPOS = ("biblioteca/framework", "aplicacao/servico", "cli", "outro")
SIM_NAO = ("sim", "nao", "incerto")

REPO_FIELDS = ("full_name", "html_url", "tipo_projeto", "releases_reais")
RELEASE_FIELDS = ("full_name", "tag", "url", "corretiva")


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sample_repos(full_names, n=N_REPOS, seed=SEED):
    """Sorteio reproduzível: ordena os nomes e usa `random.Random(seed)`."""
    names = sorted(full_names)
    return sorted(random.Random(seed).sample(names, min(n, len(names))))


def sample_releases(tags, n=N_RELEASES, seed=SEED, repo=""):
    """Até `n` releases do repositório; a semente depende do repositório (ordem estável)."""
    tags = sorted(tags)
    return sorted(random.Random(f"{seed}:{repo}").sample(tags, min(n, len(tags))))


def release_url(repo, tag):
    return f"https://github.com/{repo}/releases/tag/{tag}"


def build_sheets(repos_csv, commits_dir, out_dir, raters, n=N_REPOS, seed=SEED):
    """Gera `amostra_repos.csv` e uma planilha vazia por avaliador (sem saída da heurística)."""
    names = sample_repos([r["full_name"] for r in _read_csv(repos_csv)], n, seed)
    by_name = {r["full_name"]: r for r in _read_csv(repos_csv)}
    repo_rows, release_rows = [], []
    for name in names:
        repo_rows.append({"full_name": name, "html_url": by_name[name]["html_url"],
                          "tipo_projeto": "", "releases_reais": ""})
        path = os.path.join(commits_dir, name.replace("/", "__") + ".json")
        tags = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                tags = [r["tag"] for r in json.load(f)["releases"]]
        for tag in sample_releases(tags, N_RELEASES, seed, name):
            release_rows.append({"full_name": name, "tag": tag,
                                 "url": release_url(name, tag), "corretiva": ""})
    _write_csv(os.path.join(out_dir, "amostra_repos.csv"), REPO_FIELDS, repo_rows)
    _write_csv(os.path.join(out_dir, "amostra_releases.csv"), RELEASE_FIELDS, release_rows)
    for rater in raters:
        _write_csv(os.path.join(out_dir, f"rotulos_repos_{rater}.csv"), REPO_FIELDS, repo_rows)
        _write_csv(os.path.join(out_dir, f"rotulos_releases_{rater}.csv"), RELEASE_FIELDS,
                   release_rows)
    return repo_rows, release_rows


def fleiss(ratings):
    """Kappa de Fleiss. `ratings`: lista de itens, cada um com os rótulos dos avaliadores.

    Retorna None se não há itens ou se todos os rótulos são iguais (kappa indefinido).
    """
    from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa
    if not ratings or len({label for item in ratings for label in item}) < 2:
        return None
    table, _ = aggregate_raters(ratings)
    return float(fleiss_kappa(table, method="fleiss"))


def landis_koch(kappa):
    """Interpretação usual (Landis & Koch, 1977)."""
    if kappa is None:
        return "indefinido"
    for limit, label in ((0, "pobre"), (0.20, "leve"), (0.40, "razoável"), (0.60, "moderada"),
                         (0.80, "substancial")):
        if kappa < 0 if limit == 0 else kappa <= limit:
            return label
    return "quase perfeita"


def consensus(labels):
    """Maioria simples; sem maioria (ex.: 1-1-1) devolve None, a decidir em reunião."""
    top = Counter(labels).most_common(2)
    if len(top) == 1 or top[0][1] > top[1][1]:
        return top[0][0]
    return None


def _load_labels(out_dir, prefix, key, raters):
    """Itens e, por avaliador, `{item: linha}` de `rotulos_<prefix>_<rater>.csv`."""
    per_rater = [{tuple(row[k] for k in key): row for row in
                  _read_csv(os.path.join(out_dir, f"rotulos_{prefix}_{r}.csv"))} for r in raters]
    return list(per_rater[0]), per_rater


def agreement(out_dir, raters):
    """Kappa e consenso por dimensão. Linhas ainda não rotuladas por todos são ignoradas."""
    dims = (("repos", ("full_name",), "tipo_projeto"),
            ("repos", ("full_name",), "releases_reais"),
            ("releases", ("full_name", "tag"), "corretiva"))
    result = {}
    for prefix, key, col in dims:
        items, per_rater = _load_labels(out_dir, prefix, key, raters)
        ratings, cons = [], {}
        for item in items:
            labels = [rows[item][col].strip().lower() for rows in per_rater]
            if not all(labels):
                continue
            ratings.append(labels)
            cons[item] = consensus(labels)
        kappa = fleiss(ratings)
        result[col] = {"n": len(ratings), "kappa": kappa, "nivel": landis_koch(kappa),
                       "consenso": cons}
    return result


def evaluate_heuristic(consenso, predicted):
    """Precisão, recall e F1 da classe `sim` (corretiva) contra o consenso."""
    from sklearn.metrics import precision_recall_fscore_support
    items = [i for i, v in consenso.items() if v in ("sim", "nao") and i in predicted]
    y_true = [consenso[i] == "sim" for i in items]
    y_pred = [bool(predicted[i]) for i in items]
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary",
                                                  pos_label=True, zero_division=0)
    return {"n": len(items), "precisao": float(p), "recall": float(r), "f1": float(f1)}


def heuristic_predictions(commits_dir, version):
    """{(repo, tag): bool} da heurística para todas as releases coletadas."""
    from metricas.corretiva import is_corrective
    out = {}
    for name in os.listdir(commits_dir):
        with open(os.path.join(commits_dir, name), encoding="utf-8") as f:
            data = json.load(f)
        for rel in data["releases"]:
            out[(data["repo"], rel["tag"])] = is_corrective(rel, version)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline.gold")
    parser.add_argument("comando", choices=("sortear", "kappa", "avaliar"))
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--raters", default="")
    parser.add_argument("--versao", default="v2")
    args = parser.parse_args(argv)

    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]
    out_dir = os.path.join(data_dir, "gold")
    raters = [r for r in args.raters.split(",") if r]
    commits_dir = os.path.join(data_dir, "commits")

    if args.comando == "sortear":
        build_sheets(os.path.join(data_dir, "selecao", "repos.csv"), commits_dir, out_dir, raters)
        print(f"Planilhas em {out_dir}/ (cada integrante rotula a sua, sem consultar os demais)")
        return
    result = agreement(out_dir, raters)
    if args.comando == "kappa":
        for col, info in result.items():
            print(f"{col}: n={info['n']} kappa={info['kappa']} ({info['nivel']})")
        rows = [{"full_name": i[0], "tag": i[1] if len(i) > 1 else "",
                 "dimensao": col, "consenso": v or ""}
                for col, info in result.items() for i, v in info["consenso"].items()]
        _write_csv(os.path.join(out_dir, "consenso.csv"),
                   ("full_name", "tag", "dimensao", "consenso"), rows)
        print(f"Consenso em {out_dir}/consenso.csv (vazio = sem maioria, decidir em reunião)")
    else:
        consenso = result["corretiva"]["consenso"]
        decided = os.path.join(out_dir, "consenso.csv")  # empates resolvidos em reunião
        if os.path.exists(decided):
            consenso.update({(r["full_name"], r["tag"]): r["consenso"] for r in _read_csv(decided)
                             if r["dimensao"] == "corretiva" and r["consenso"]})
        print(evaluate_heuristic(consenso, heuristic_predictions(commits_dir, args.versao)))


if __name__ == "__main__":
    main()
