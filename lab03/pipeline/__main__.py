"""Ponto de entrada: `python -m pipeline --config config.json`."""
import argparse
import json
import os
import sys
from datetime import date

from metricas.cfr import change_failure_rate_ci
from metricas.recuperacao import censored_ratio, median_recovery_hours, recovery_episodes
from pipeline.http import GitHubClient, NotFoundError
from pipeline.runs import collect_repo


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


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
    out_dir = os.path.join(cfg["data_dir"], "runs")

    rows = []
    for repo in cfg["repos"]:
        try:
            data = collect_repo(client, repo["full_name"], repo["default_branch"],
                                start, end, out_dir)
        except NotFoundError:
            print(f"[skip] {repo['full_name']}: não encontrado", file=sys.stderr)
            continue
        episodes = recovery_episodes(data["runs"])
        rows.append({
            "repo": data["repo"],
            "runs": len(data["runs"]),
            "cfr_ci": change_failure_rate_ci(data["runs"]),
            "recovery_median_h": median_recovery_hours(episodes),
            "recovery_censored_ratio": censored_ratio(episodes),
        })
        print(f"[ok] {data['repo']}: {len(data['runs'])} runs")

    out = os.path.join(cfg["data_dir"], "metricas_ci.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"Métricas gravadas em {out}")


if __name__ == "__main__":
    main()
