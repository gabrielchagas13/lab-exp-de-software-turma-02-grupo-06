"""Ponto de entrada: `python -m pipeline --config config.json`."""
import argparse
import json
import os
import sys
from datetime import date

from metricas.cfr import change_failure_rate_ci
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
    return {
        "repo": runs["repo"],
        "runs": len(runs["runs"]),
        "releases": len(in_window),
        "releases_ignoradas": len(commits["skipped"]),
        "cfr_ci": change_failure_rate_ci(runs["runs"]),
        "recovery_median_h": median_recovery_hours(episodes),
        "recovery_censored_ratio": censored_ratio(episodes),
        **repo_lead_time(commits["releases"]),
        "releases_por_semana": len(in_window) / (((end - start).days + 1) / 7),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Defina a variável de ambiente GITHUB_TOKEN.")

    cfg = load_config(args.config)
    start = date.fromisoformat(cfg["window_start"])
    end = date.fromisoformat(cfg["window_end"])
    client = GitHubClient(token, os.path.join(cfg["data_dir"], "cache"))

    if "selection" in cfg:
        repos = select_repositories(client, cfg["selection"], start, end, cfg["data_dir"])
    else:
        repos = cfg["repos"]

    rows = []
    for repo in repos:
        try:
            row = process_repo(client, repo, start, end, cfg["data_dir"])
        except NotFoundError:
            print(f"[skip] {repo['full_name']}: não encontrado", file=sys.stderr)
            continue
        rows.append(row)
        print(f"[ok] {row['repo']}: {row['runs']} runs, {row['releases']} releases")

    out = os.path.join(cfg["data_dir"], "metricas.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"Métricas gravadas em {out}")


if __name__ == "__main__":
    main()
