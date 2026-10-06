"""Coleta de workflow runs do default branch (event=push) na janela."""
import json
import os
from datetime import date, timedelta

API_CAP = 1000  # a API retorna no máximo 1.000 resultados por consulta filtrada
PER_PAGE = 100
KEEP_FIELDS = ("id", "workflow_id", "name", "conclusion", "created_at",
               "run_started_at", "updated_at")


def month_ranges(start, end):
    """Divide [start, end] (date) em intervalos mensais (início, fim) inclusivos."""
    ranges = []
    cur = start
    while cur <= end:
        nxt = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
        ranges.append((cur, min(nxt - timedelta(days=1), end)))
        cur = nxt
    return ranges


def _fetch_range(client, repo, branch, lo, hi, stats):
    params = {"branch": branch, "event": "push", "per_page": PER_PAGE,
              "created": f"{lo.isoformat()}..{hi.isoformat()}"}
    path = f"/repos/{repo}/actions/runs"
    first, _ = client.get(path, {**params, "page": 1})
    if first["total_count"] >= API_CAP and lo < hi:
        # teto da API atingido: divide o intervalo ao meio para não perder runs
        mid = lo + (hi - lo) // 2
        stats["splits"] += 1
        return (_fetch_range(client, repo, branch, lo, mid, stats)
                + _fetch_range(client, repo, branch, mid + timedelta(days=1), hi, stats))
    if first["total_count"] >= API_CAP:
        stats["capped_days"].append(lo.isoformat())  # um único dia já estoura o teto
    runs = []
    for page in client.get_pages(path, params):
        runs.extend(page["workflow_runs"])
    return runs


def collect_runs(client, repo, branch, start, end):
    """Retorna (runs, stats) do repositório; runs sem duplicatas, campos reduzidos."""
    stats = {"splits": 0, "capped_days": []}
    by_id = {}
    for lo, hi in month_ranges(start, end):
        for run in _fetch_range(client, repo, branch, lo, hi, stats):
            by_id[run["id"]] = {k: run.get(k) for k in KEEP_FIELDS}
    return list(by_id.values()), stats


def collect_repo(client, repo, branch, start, end, out_dir):
    """Coleta e grava `out_dir/<owner>__<repo>.json`; pula se já existir (retomada)."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, repo.replace("/", "__") + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    runs, stats = collect_runs(client, repo, branch, start, end)
    result = {"repo": repo, "branch": branch, "runs": runs, **stats}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f)
    os.replace(tmp, path)
    return result
