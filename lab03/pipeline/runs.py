"""Coleta de workflow runs do default branch (event=push) na janela."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
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
    # Filtra para KEEP_FIELDS JA NA ENTRADA. O objeto cru de um workflow run
    # tem ~8 KB de JSON; reduzido aos 7 campos usados, ~220 bytes. Guardar o
    # cru ate o fim de collect_runs fazia a memoria explodir em repositorios
    # com centenas de milhares de runs -- 16 GB observados com 3 threads.
    runs = []
    for page in client.get_pages(path, params):
        runs.extend({k: run.get(k) for k in KEEP_FIELDS} for run in page["workflow_runs"])
    return runs


def collect_runs(client, repo, branch, start, end, workers=1):
    """Retorna (runs, stats) do repositório; runs sem duplicatas, campos reduzidos.

    Os intervalos mensais são independentes entre si, então podem ser buscados
    em paralelo. Isso não aumenta o número de requisições por minuto — o
    `GitHubClient` reserva os slots globalmente —, apenas aproveita o tempo em
    que uma thread estaria parada esperando resposta. As páginas de runs são
    grandes e a coleta fica ociosa ~80% do tempo com uma thread só.

    A ordem dos meses é preservada na junção, então a deduplicação por `id` é
    determinística, com ou sem paralelismo.
    """
    ranges = month_ranges(start, end)
    if workers > 1 and len(ranges) > 1:
        # Cada intervalo acumula suas próprias stats; mescladas em ordem depois,
        # porque dicionário compartilhado entre threads perderia incrementos.
        parciais = [{"splits": 0, "capped_days": []} for _ in ranges]
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futuros = [executor.submit(_fetch_range, client, repo, branch, lo, hi, st)
                       for (lo, hi), st in zip(ranges, parciais)]
            resultados = [f.result() for f in futuros]  # ordem de submissão
        stats = {"splits": sum(p["splits"] for p in parciais),
                 "capped_days": [d for p in parciais for d in p["capped_days"]]}
    else:
        stats = {"splits": 0, "capped_days": []}
        resultados = [_fetch_range(client, repo, branch, lo, hi, stats) for lo, hi in ranges]

    by_id = {}
    for runs in resultados:
        for run in runs:
            by_id[run["id"]] = run  # ja vem reduzido de _fetch_range
    return list(by_id.values()), stats


def collect_repo(client, repo, branch, start, end, out_dir, workers=1):
    """Coleta e grava `out_dir/<owner>__<repo>.json`; pula se já existir (retomada)."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, repo.replace("/", "__") + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    runs, stats = collect_runs(client, repo, branch, start, end, workers)
    result = {"repo": repo, "branch": branch, "runs": runs, **stats}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f)
    os.replace(tmp, path)
    return result
