"""
Coleta RQ01 (idade do repositorio) e RQ02 (total de pull requests aceitas/mergeadas)
para os repositorios com mais estrelas do GitHub, via API GraphQL.

Uso:
    python fetch_repos_rq1_rq2.py --count 10                 # teste rapido (validacao)
    python fetch_repos_rq1_rq2.py --count 100                # entrega da Sprint 1
    python fetch_repos_rq1_rq2.py --count 1000 --output data/repos_1000.csv  # Sprint 2

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

QUERY = """
query($searchQuery: String!, $cursor: String) {
  search(query: $searchQuery, type: REPOSITORY, first: 100, after: $cursor) {
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
        createdAt
        primaryLanguage { name }
        pullRequests(states: MERGED) {
          totalCount
        }
      }
    }
  }
}
"""


def fetch_repos(token: str, count: int) -> list[dict]:
    session = requests.Session()
    session.headers.update({"Authorization": f"bearer {token}"})

    # "sort:stars-desc" dentro da propria query de busca ordena os resultados
    # por numero de estrelas, igual ao usado na busca web do GitHub.
    min_stars = 1

    repos: list[dict] = []
    seen = set()
    cursor = None
    while len(repos) < count:
        search_query = f"stars:>{min_stars} sort:stars-desc"
        variables = {"searchQuery": search_query, "cursor": cursor}

        # o gateway do GitHub responde com erro/corpo vazio esporadicamente sob
        # carga (502/503/504 ou 200 com corpo invalido); tenta novamente com
        # backoff antes de desistir.
        payload = None
        for attempt in range(8):
            try:
                response = session.post(API_URL, json={"query": QUERY, "variables": variables})
                response.raise_for_status()
                payload = response.json()
                break
            except (requests.exceptions.RequestException, ValueError):
                time.sleep(min(2 ** attempt, 30))
        if payload is None:
            response.raise_for_status()
            payload = response.json()

        if "errors" in payload:
            raise RuntimeError(payload["errors"])

        search = payload["data"]["search"]
        for node in search["nodes"]:
            if node["nameWithOwner"] not in seen:
                seen.add(node["nameWithOwner"])
                repos.append(node)

        if len(repos) >= count:
            break

        if search["pageInfo"]["hasNextPage"]:
            cursor = search["pageInfo"]["endCursor"]
        else:
            # a Search API do GitHub as vezes reporta hasNextPage=False antes
            # do limite real de 1000 resultados (indice de busca instavel em
            # consultas muito paginadas). Reinicia a paginacao a partir da
            # faixa de estrelas do ultimo repositorio coletado para continuar.
            if not repos:
                break
            min_stars = repos[-1]["stargazerCount"] - 1
            cursor = None

        # evita estourar o limite de taxa da API em consultas grandes (ex.: 1000 repos)
        time.sleep(1)

    return repos[:count]


def to_rows(repos: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc)
    rows = []
    for repo in repos:
        created_at = datetime.fromisoformat(repo["createdAt"].replace("Z", "+00:00"))
        age_years = round((now - created_at).days / 365.25, 2)
        language = repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None

        rows.append({
            "repo": repo["nameWithOwner"],
            "url": repo["url"],
            "stars": repo["stargazerCount"],
            "language": language,
            "created_at": repo["createdAt"],
            "age_years": age_years,               # RQ01
            "merged_pull_requests": repo["pullRequests"]["totalCount"],  # RQ02
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
    parser.add_argument("--output", default="data/repos.csv", help="caminho do CSV de saida")
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
