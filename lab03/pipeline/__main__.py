"""Ponto de entrada: `python -m pipeline --config config.json`."""
import argparse
import json
import os
import sys
from datetime import date

from metricas.cfr import change_failure_rate_ci
from metricas.corretiva import cfr_releases
from metricas.lead_time import repo_lead_time
from metricas.recuperacao import censored_ratio, median_recovery_hours, recovery_episodes
from pipeline.commits import collect_repo_commits
from pipeline.http import GitHubClient, NotFoundError
from pipeline.releases import collect_repo_releases
from pipeline.runs import collect_repo
from pipeline.selection import select_repositories


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    """Grava JSON de forma atômica (tmp + replace).

    A gravação é feita a cada repositório; sem o arquivo temporário, uma queda
    no meio da escrita deixaria um JSON truncado por cima do resultado bom."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def load_dotenv(path):
    """Carrega KEY=valor de um .env para o ambiente, sem dependência externa.

    Variáveis já definidas no ambiente têm precedência: o .env é conveniência
    para desenvolvimento, não a fonte de verdade (na CI o token vem de secret).
    O arquivo é ignorado pelo git e nunca deve ser commitado."""
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def process_repo(client, repo, start, end, data_dir):
    """Coleta runs, releases e commits entre releases de um repositório e calcula as métricas."""
    name = repo["full_name"]
    runs = collect_repo(client, name, repo["default_branch"], start, end,
                        os.path.join(data_dir, "runs"))
    rels = collect_repo_releases(client, name, start, end, os.path.join(data_dir, "releases"))
    commits = collect_repo_commits(client, name, rels["releases"],
                                   os.path.join(data_dir, "commits"))
    episodes = recovery_episodes(runs["runs"])
    in_window = [r for r in rels["releases"] if r["in_window"] and not r["prerelease"]]
    mensagens = {r["tag"]: [c["message"] for c in r["commits"]] for r in commits["releases"]}
    return {
        "repo": runs["repo"],
        "runs": len(runs["runs"]),
        "releases": len(in_window),
        "releases_ignoradas": len(commits["skipped"]),
        "cfr_ci": change_failure_rate_ci(runs["runs"]),
        **cfr_releases(in_window, mensagens),
        "recovery_median_h": median_recovery_hours(episodes),
        "recovery_censored_ratio": censored_ratio(episodes),
        **repo_lead_time(commits["releases"]),
        "releases_por_semana": len(in_window) / (((end - start).days + 1) / 7),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Defina GITHUB_TOKEN no ambiente ou em lab03/.env (ver README).")

    cfg = load_config(args.config)
    start = date.fromisoformat(cfg["window_start"])
    end = date.fromisoformat(cfg["window_end"])
    # 'http' é opcional; os padrões do cliente já são conservadores. Aumente
    # min_interval se a coleta esbarrar no limite secundário do GitHub.
    http_cfg = cfg.get("http", {})
    client = GitHubClient(token, os.path.join(cfg["data_dir"], "cache"), **http_cfg)

    if "selection" in cfg:
        repos = select_repositories(client, cfg["selection"], start, end, cfg["data_dir"])
    else:
        repos = cfg["repos"]

    out = os.path.join(cfg["data_dir"], "metricas.json")
    rows, falhas = [], []
    total = len(repos)
    for i, repo in enumerate(repos, 1):
        try:
            row = process_repo(client, repo, start, end, cfg["data_dir"])
        except NotFoundError:
            print(f"[skip] {repo['full_name']}: não encontrado", file=sys.stderr)
            continue
        except Exception as exc:
            # Um repositório problemático não pode derrubar uma coleta de horas:
            # registra, segue, e o motivo fica no resumo do fim.
            falhas.append({"repo": repo["full_name"], "erro": f"{type(exc).__name__}: {exc}"})
            print(f"[erro] {repo['full_name']}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        rows.append(row)
        print(f"[ok] {i}/{total} {row['repo']}: {row['runs']} runs, {row['releases']} releases")
        # Grava a cada repositório: se a máquina dormir ou cair, o que já foi
        # calculado está em disco em vez de se perder no fim da execução.
        write_json(out, rows)

    if falhas:
        write_json(os.path.join(cfg["data_dir"], "falhas.json"), falhas)
        print(f"{len(falhas)} repositórios falharam; detalhes em "
              f"{os.path.join(cfg['data_dir'], 'falhas.json')}", file=sys.stderr)

    write_json(out, rows)
    print(f"Métricas gravadas em {out} ({len(rows)} repositórios)")


if __name__ == "__main__":
    main()
