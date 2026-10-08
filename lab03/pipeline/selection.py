"""Seleção de repositórios: busca fatiada por estrelas, filtros de inclusão e funil."""
import csv
import os
import random
from datetime import date
from urllib.error import HTTPError

from metricas.cfr import classify_conclusion
from pipeline.http import NotFoundError
from pipeline.metadata import FIELDS as METADATA_FIELDS, collect_metadata
from pipeline.releases import collect_releases
from pipeline.runs import collect_repo

PER_PAGE = 100
DEFAULTS = {
    "sample_size": 100,
    "min_releases": 5,
    "min_runs": 50,
    "seed": 42,
    "query": "",
    "star_ranges": ["1000..2000", "2000..5000", "5000..10000", "10000..50000", ">=50000"],
}

# Etapas do funil, na ordem em que os filtros são aplicados: (status, descrição).
INCLUDED = "incluido"
NOT_EVALUATED = "nao_avaliado"
DISCARD_REASONS = (
    ("fork_ou_arquivado", "fork ou arquivado"),
    ("sem_push_na_janela", "sem push durante a janela"),
    ("inacessivel", "erro ao acessar a API (404/451...)"),
    ("sem_actions", "não usa GitHub Actions (0 workflows)"),
    ("poucas_releases", "menos releases que o mínimo na janela"),
    ("poucos_runs", "menos workflow runs válidos que o mínimo na janela"),
)


# ---- busca ---------------------------------------------------------------
def search_candidates(client, star_ranges, query=""):
    """Candidatos de /search/repositories, uma consulta por faixa de estrelas.

    A busca devolve no máximo 1.000 resultados por consulta, por isso a busca é
    fatiada. Retorna (candidatos sem duplicatas ordenados por nome, fatias), em
    que cada fatia registra `total_count` e quantos itens vieram de fato.
    """
    by_name, slices = {}, []
    for stars in star_ranges:
        q = f"stars:{stars} {query}".strip()
        pages = client.get_pages("/search/repositories", {
            "q": q, "sort": "stars", "order": "desc", "per_page": PER_PAGE})
        items = [item for page in pages for item in page["items"]]
        slices.append({"query": q, "total_count": pages[0]["total_count"] if pages else 0,
                       "fetched": len(items)})
        for item in items:
            by_name.setdefault(item["full_name"], item)
    return sorted(by_name.values(), key=lambda r: r["full_name"].lower()), slices


# ---- filtros -------------------------------------------------------------
def count_releases(releases):
    """Releases da definição principal na janela: draft=false e prerelease=false."""
    return sum(1 for r in releases if r["in_window"] and not r["prerelease"])


def count_valid_runs(runs):
    """Runs que entram nos cálculos (success ou falha); cancelled etc. são ignorados."""
    return sum(1 for r in runs if classify_conclusion(r.get("conclusion")) is not None)


def has_actions(client, repo):
    body, _ = client.get(f"/repos/{repo}/actions/workflows", {"per_page": 1})
    return body["total_count"] > 0


def runs_upper_bound(client, repo, branch, start, end):
    """total_count de runs push no default branch na janela (uma chamada).

    É um limite superior dos runs válidos: se já for menor que o mínimo, o
    repositório é descartado sem coletar os runs um a um.
    """
    body, _ = client.get(f"/repos/{repo}/actions/runs", {
        "branch": branch, "event": "push", "per_page": 1,
        "created": f"{start.isoformat()}..{end.isoformat()}"})
    return body["total_count"]


def _pushed_in_window(item, start):
    pushed = item.get("pushed_at")
    return pushed is not None and date.fromisoformat(pushed[:10]) >= start


def evaluate(client, item, start, end, cfg, runs_dir):
    """Aplica os filtros em ordem, do mais barato ao mais caro em chamadas.

    Retorna (status, info): status é `incluido` ou o primeiro motivo de descarte;
    `info` traz as contagens obtidas até o ponto de parada.
    """
    repo, branch = item["full_name"], item["default_branch"]
    info = {"releases": None, "valid_runs": None}
    if item.get("fork") or item.get("archived"):
        return "fork_ou_arquivado", info
    if not _pushed_in_window(item, start):
        return "sem_push_na_janela", info
    try:
        if not has_actions(client, repo):
            return "sem_actions", info
        info["releases"] = count_releases(collect_releases(client, repo, start, end))
        if info["releases"] < cfg["min_releases"]:
            return "poucas_releases", info
        if runs_upper_bound(client, repo, branch, start, end) < cfg["min_runs"]:
            return "poucos_runs", info
        data = collect_repo(client, repo, branch, start, end, runs_dir)
    except (NotFoundError, HTTPError):
        return "inacessivel", info
    info["valid_runs"] = count_valid_runs(data["runs"])
    if info["valid_runs"] < cfg["min_runs"]:
        return "poucos_runs", info
    return INCLUDED, info


# ---- funil ---------------------------------------------------------------
def funnel(records):
    """Tabela do funil: quantos restam após cada etapa e quantos saíram nela."""
    counts = {}
    for rec in records:
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    remaining = len(records)
    rows = [{"etapa": "candidatos (busca)", "restantes": remaining, "descartados": 0, "motivo": ""}]
    for status, reason in DISCARD_REASONS:
        n = counts.get(status, 0)
        remaining -= n
        rows.append({"etapa": status, "restantes": remaining, "descartados": n, "motivo": reason})
    n = counts.get(NOT_EVALUATED, 0)
    rows.append({"etapa": "amostra_final", "restantes": remaining - n, "descartados": n,
                 "motivo": "não avaliados: amostra já completa"})
    return rows


def _write_csv(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(path + ".tmp", path)


# ---- etapa completa ------------------------------------------------------
def select_repositories(client, selection, start, end, data_dir, log=print):
    """Busca, filtra e amostra repositórios; grava funil, candidatos e metadados.

    Os candidatos são embaralhados com a semente da config (reprodutível) e
    avaliados até a amostra atingir `sample_size`; os restantes ficam como
    `nao_avaliado` no funil. Toda chamada passa pelo cache do cliente, então
    rodar de novo retoma de onde parou. Retorna `[{full_name, default_branch}]`.

    Saídas em `data_dir/selecao/`: `funil.csv`, `candidatos.csv`,
    `buscas.csv` e `repos.csv` (metadados da amostra final).
    """
    cfg = {**DEFAULTS, **selection}
    out_dir = os.path.join(data_dir, "selecao")
    runs_dir = os.path.join(data_dir, "runs")

    candidates, slices = search_candidates(client, cfg["star_ranges"], cfg["query"])
    random.Random(cfg["seed"]).shuffle(candidates)
    log(f"[selecao] {len(candidates)} candidatos")

    records, metadata = [], []
    for item in candidates:
        rec = {"full_name": item["full_name"], "stars": item["stargazers_count"],
               "status": NOT_EVALUATED, "releases": None, "valid_runs": None}
        if len(metadata) < cfg["sample_size"]:
            status, info = evaluate(client, item, start, end, cfg, runs_dir)
            rec.update(status=status, **info)
            if status == INCLUDED:
                metadata.append(collect_metadata(client, item, end))
                log(f"[selecao] {len(metadata)}/{cfg['sample_size']} {item['full_name']}")
        records.append(rec)

    _write_csv(os.path.join(out_dir, "buscas.csv"), ["query", "total_count", "fetched"], slices)
    _write_csv(os.path.join(out_dir, "candidatos.csv"),
               ["full_name", "stars", "status", "releases", "valid_runs"], records)
    _write_csv(os.path.join(out_dir, "funil.csv"),
               ["etapa", "restantes", "descartados", "motivo"], funnel(records))
    _write_csv(os.path.join(out_dir, "repos.csv"), METADATA_FIELDS, metadata)
    if len(metadata) < cfg["sample_size"]:
        log(f"[selecao] aviso: só {len(metadata)} repositórios passaram nos filtros")
    return [{"full_name": m["full_name"], "default_branch": m["default_branch"]}
            for m in metadata]
