"""Consolida metadados e métricas em `dataset.csv` e gera o dicionário de dados."""
import csv
import json
import os

from pipeline.metadata import FIELDS as METADATA_FIELDS

# (coluna, tipo, unidade, fórmula ou origem)
METRIC_DICTIONARY = (
    ("runs", "inteiro", "runs", "Workflow runs `push` do default branch na janela (coleta mensal)"),
    ("releases", "inteiro", "releases", "Releases publicadas na janela (sem draft e sem pré-release)"),
    ("releases_ignoradas", "inteiro", "releases",
     "Releases da janela sem commits comparáveis (primeira da história ou tag apagada)"),
    ("releases_por_semana", "decimal", "releases/semana",
     "RQ 01: `releases / ((window_end − window_start + 1 dia) / 7)`"),
    ("lead_time_release_h", "decimal", "horas",
     "RQ 02a: mediana, entre as releases, de (publicação − commit mais antigo da release); vazio sem commits"),
    ("lead_time_commit_h", "decimal", "horas",
     "RQ 02b: mediana de (publicação − `author_date`) sobre todos os commits de todas as releases"),
    ("releases_com_commits", "inteiro", "releases", "Releases usadas em `lead_time_release_h`"),
    ("commits", "inteiro", "commits", "Commits usados em `lead_time_commit_h`"),
    ("cfr_ci", "decimal", "proporção (0 a 1)",
     "RQ 03a: falhas ÷ (falhas + sucessos); falha = failure/timed_out/startup_failure; cancelled e skipped ignorados"),
    ("cfr_entrega", "decimal", "proporção (0 a 1)",
     "RQ 03b: releases seguidas em ≤ 7 dias por release corretiva ÷ releases avaliadas (últimos 7 dias da janela ficam fora)"),
    ("recovery_median_h", "decimal", "horas",
     "RQ 04: mediana de (`updated_at` do sucesso − `run_started_at` da 1ª falha) por episódio; vazio sem episódio concluído"),
    ("recovery_censored_ratio", "decimal", "proporção (0 a 1)",
     "RQ 04: episódios de falha sem sucesso posterior na janela ÷ total de episódios"),
)
METADATA_DICTIONARY = (
    ("full_name", "texto", "", "`full_name` da API (`dono/repositório`)"),
    ("html_url", "texto", "", "`html_url`"),
    ("default_branch", "texto", "", "`default_branch`"),
    ("stars", "inteiro", "estrelas", "`stargazers_count` no momento da busca"),
    ("forks", "inteiro", "forks", "`forks_count`"),
    ("language", "texto", "", "`language` (vazio se o GitHub não detecta)"),
    ("contributors", "inteiro", "pessoas",
     "Última página de `GET /contributors?per_page=1&anon=true`; vazio se a API recusa listar"),
    ("created_at", "data ISO 8601", "", "`created_at`"),
    ("age_years", "decimal", "anos", "(window_end − created_at) / 365,25 dias"),
)
DICTIONARY = METADATA_DICTIONARY + METRIC_DICTIONARY
COLUMNS = tuple(col for col, *_ in DICTIONARY)


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_dataset(data_dir):
    """Junta `selecao/repos.csv` e `metricas.json` (chave `full_name` = `repo`).

    Grava `dataset.csv` e `dicionario_dados.csv` em `data_dir` e retorna as linhas.
    Repositórios sem métricas (pulados na coleta) ficam de fora.
    """
    meta_path = os.path.join(data_dir, "selecao", "repos.csv")  # ausente quando config usa `repos`
    metadata = {r["full_name"]: r for r in _read_csv(meta_path)} if os.path.exists(meta_path) else {}
    with open(os.path.join(data_dir, "metricas.json"), encoding="utf-8") as f:
        metrics = json.load(f)
    rows = []
    for m in metrics:
        row = {col: "" for col in COLUMNS}
        row.update({k: v for k, v in metadata.get(m["repo"], {"full_name": m["repo"]}).items()
                    if k in METADATA_FIELDS})
        row.update({k: "" if m.get(k) is None else m[k] for k in COLUMNS if k in m})
        rows.append(row)
    _write_csv(os.path.join(data_dir, "dataset.csv"), COLUMNS, rows)
    _write_csv(os.path.join(data_dir, "dicionario_dados.csv"),
               ("coluna", "tipo", "unidade", "origem"),
               [dict(zip(("coluna", "tipo", "unidade", "origem"), d)) for d in DICTIONARY])
    return rows
