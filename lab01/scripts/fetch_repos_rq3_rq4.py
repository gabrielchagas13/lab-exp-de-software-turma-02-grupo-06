"""
Coleta RQ03 (total de releases) e RQ04 (tempo até a última atualização)
para os repositorios com mais estrelas do GitHub, via API GraphQL.

RQ04 usa o campo `pushedAt` (data do ultimo push de codigo) como proxy de
"ultima atualizacao", por ser mais preciso do que `updatedAt` (que tambem
muda com interacoes como issues/estrelas, sem refletir mudanca de codigo).

Uso:
    python fetch_repos_rq3_rq4.py --count 10                 # teste rapido (validacao)
    python fetch_repos_rq3_rq4.py --count 100                # entrega da Sprint 1
    python fetch_repos_rq3_rq4.py --count 1000 --output data/repos_1000.csv  # Sprint 2

Requer a variavel de ambiente GITHUB_TOKEN (ver .env.example).
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

API_URL = "https://api.github.com/graphql"

PAGE_SIZE = 30  # releases.totalCount é caro para a API calcular; first:100 causa 502/504 no gateway

QUERY = """
query($searchQuery: String!, $cursor: String) {
  search(query: $searchQuery, type: REPOSITORY, first: %d, after: $cursor) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        url
        stargazerCount
        primaryLanguage { name }
        pushedAt
        releases {
          totalCount
        }
      }
    }
  }
}
""" % PAGE_SIZE


def fetch_repos(token: str, count: int) -> list[dict]:
    session = requests.Session()
    session.headers.update({"Authorization": f"bearer {token}"})

    # "sort:stars-desc" dentro da propria query de busca ordena os resultados
    # por numero de estrelas, igual ao usado na busca web do GitHub.
    search_query = "stars:>1 sort:stars-desc"

    repos = []
    cursor = None
    while len(repos) < count:
        variables = {"searchQuery": search_query, "cursor": cursor}
        response = session.post(API_URL, json={"query": QUERY, "variables": variables})
        response.raise_for_status()
        payload = response.json()

        if "errors" in payload:
            raise RuntimeError(payload["errors"])

        search = payload["data"]["search"]
        repos.extend(search["nodes"])

        if not search["pageInfo"]["hasNextPage"]:
            break
        cursor = search["pageInfo"]["endCursor"]

        # evita estourar o limite de taxa da API em consultas grandes (ex.: 1000 repos)
        time.sleep(1)

    return repos[:count]


def to_rows(repos: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc)
    rows = []
    for repo in repos:
        language = repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None
        pushed_at = repo["pushedAt"]
        days_since_update = None
        if pushed_at:
            pushed_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_since_update = (now - pushed_dt).days

        rows.append({
            "repo": repo["nameWithOwner"],
            "url": repo["url"],
            "stars": repo["stargazerCount"],
            "language": language,
            "total_releases": repo["releases"]["totalCount"],  # RQ03
            "pushed_at": pushed_at,
            "days_since_update": days_since_update,            # RQ04
        })
    return rows


def save_csv(rows: list[dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100, help="quantidade de repositorios a coletar")
    parser.add_argument("--output", default="data/repos_rq3_rq4.csv", help="caminho do CSV de saida")
    args = parser.parse_args()

    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Erro: defina GITHUB_TOKEN no arquivo .env (veja .env.example)", file=sys.stderr)
        sys.exit(1)

    print(f"Buscando {args.count} repositorios...")
    repos = fetch_repos(token, args.count)
    rows = to_rows(repos)
    save_csv(rows, args.output)
    print(f"OK: {len(rows)} repositorios salvos em {args.output}")


if __name__ == "__main__":
    main()
