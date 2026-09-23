#!/usr/bin/env python3
"""
Agrega metricas estaticas (RQ3, issue #31) por trial (issue #49).

Le data/trials.csv, roda radon (LOC + complexidade ciclomatica) e jscpd
(duplicacao) sobre o solution_path de cada trial, e grava uma linha por
trial em data/metrics.csv -- entrada do dashboard (scripts/dashboard.py).

Reaproveita as funcoes de coleta de scripts/collect_metrics.py (issue #31)
em vez de duplicar a logica do radon/jscpd.

Uso:
    python scripts/aggregate_static_metrics.py
"""

from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect_metrics import get_jscpd_duplication, get_radon_cc, get_radon_raw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAB02_DIR = os.path.dirname(SCRIPT_DIR)
TRIALS_CSV = os.path.join(LAB02_DIR, "data", "trials.csv")
METRICS_CSV = os.path.join(LAB02_DIR, "data", "metrics.csv")


def read_trials(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    if not os.path.isfile(TRIALS_CSV):
        raise SystemExit(f"{TRIALS_CSV} nao encontrado -- rode os trials (scripts/timer.py) primeiro.")

    trials = read_trials(TRIALS_CSV)
    rows = []
    for trial in trials:
        trial_id = trial["trial_id"]
        solution_path = os.path.join(LAB02_DIR, trial["solution_path"])
        if not os.path.isfile(solution_path):
            print(f"[aggregate] aviso: {solution_path} nao encontrado -- pulando {trial_id}")
            continue

        print(f"[aggregate] {trial_id}")
        loc = get_radon_raw(solution_path)
        cc = get_radon_cc(solution_path)
        dup = get_jscpd_duplication(solution_path)

        rows.append({
            "trial_id": trial_id,
            "participant": trial["participant"],
            "kata": trial["kata"],
            "treatment": trial["treatment"],
            "loc": loc,
            "cyclomatic_complexity_mean": round(cc, 4),
            "duplication_pct": round(dup, 4),
        })

    os.makedirs(os.path.dirname(METRICS_CSV), exist_ok=True)
    with open(METRICS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "trial_id", "participant", "kata", "treatment",
            "loc", "cyclomatic_complexity_mean", "duplication_pct",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[aggregate] {len(rows)} trials -> {METRICS_CSV}")


if __name__ == "__main__":
    main()
