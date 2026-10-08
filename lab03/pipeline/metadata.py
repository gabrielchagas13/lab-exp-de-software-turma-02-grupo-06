"""Metadados dos repositórios: estrelas, linguagem, contribuidores e idade (RQ 06)."""
import re
from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

_LAST_RE = re.compile(r'<([^>]+)>;\s*rel="last"')
FIELDS = ("full_name", "html_url", "default_branch", "stars", "forks", "language",
          "contributors", "created_at", "age_years")


def count_contributors(client, repo):
    """Nº de contribuidores (incluindo anônimos) sem baixar a lista inteira.

    Pede `per_page=1&anon=true` e lê o número da última página no header Link.
    Sem Link, a lista cabe numa página só (0 ou 1 contribuidor). Retorna None
    quando a API se recusa a listar (403: histórico grande demais).
    """
    try:
        body, headers = client.get(f"/repos/{repo}/contributors", {"per_page": 1, "anon": "true"})
    except HTTPError as err:
        if err.code == 403:
            return None
        raise
    match = _LAST_RE.search(headers.get("link", ""))
    if match:
        return int(parse_qs(urlparse(match.group(1)).query)["page"][0])
    return len(body or [])


def age_years(created_at, ref):
    """Idade em anos (365,25 dias) entre `created_at` (ISO) e a data de referência `ref`."""
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
    return round((ref - created).days / 365.25, 2)


def repo_metadata(item, contributors, ref):
    """Linha de metadados a partir de um item da busca (ou de GET /repos/{repo}).

    `ref` é a data de referência para a idade (o fim da janela de observação).
    """
    return {
        "full_name": item["full_name"],
        "html_url": item.get("html_url") or f"https://github.com/{item['full_name']}",
        "default_branch": item["default_branch"],
        "stars": item["stargazers_count"],
        "forks": item.get("forks_count"),
        "language": item.get("language") or "",
        "contributors": contributors,
        "created_at": item["created_at"],
        "age_years": age_years(item["created_at"], ref),
    }


def collect_metadata(client, item, ref):
    """Metadados de um repositório candidato (uma chamada à API, a de contribuidores)."""
    return repo_metadata(item, count_contributors(client, item["full_name"]), ref)
