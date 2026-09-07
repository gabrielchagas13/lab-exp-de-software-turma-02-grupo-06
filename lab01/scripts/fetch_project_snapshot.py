"""
Snapshot do GitHub Projects (v2) do grupo: exporta, via GraphQL, os itens do
board e o valor atual do campo de status de cada um.

Reaproveita o padrao de sessao/retry de fetch_repos.py (Parte 1).

Uso:
    python fetch_project_snapshot.py --owner gabrielchagas13 --number 1
    python fetch_project_snapshot.py --owner gabrielchagas13 --number 1 --owner-type organization

Requer:
- GITHUB_TOKEN no .env com escopo 'read:project' (o escopo 'public_repo'
  usado para as consultas de repositorio NAO cobre Projects v2).
- o numero do projeto (visivel na URL do board, ex.: .../projects/3 -> --number 3).
"""

import argparse
import csv
import os
import sys
import time

import requests
from dotenv import load_dotenv

API_URL = "https://api.github.com/graphql"
PAGE_SIZE = 50
STATUS_FIELD_NAME = "Status"

QUERY = """
query($login: String!, $number: Int!, $cursor: String) {
  %(root)s(login: $login) {
    projectV2(number: $number) {
      title
      url
      items(first: %(page_size)d, after: $cursor) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          status: fieldValueByName(name: "%(status_field)s") {
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
          content {
            ... on Issue {
              type: __typename
              number
              title
              url
              state
              repository { nameWithOwner }
              assignees(first: 5) { nodes { login } }
            }
            ... on PullRequest {
              type: __typename
              number
              title
              url
              state
              repository { nameWithOwner }
              assignees(first: 5) { nodes { login } }
            }
            ... on DraftIssue {
              type: __typename
              title
            }
          }
        }
      }
    }
  }
}
"""


def build_query(owner_type: str) -> str:
    root = "organization" if owner_type == "organization" else "user"
    return QUERY % {"root": root, "page_size": PAGE_SIZE, "status_field": STATUS_FIELD_NAME}


def fetch_items(token: str, owner: str, number: int, owner_type: str) -> tuple[str, list[dict]]:
    session = requests.Session()
    session.headers.update({"Authorization": f"bearer {token}"})
    query = build_query(owner_type)

    items: list[dict] = []
    cursor = None
    project_title = None
    while True:
        variables = {"login": owner, "number": number, "cursor": cursor}

        payload = None
        for attempt in range(4):
            try:
                response = session.post(API_URL, json={"query": query, "variables": variables})
                response.raise_for_status()
                payload = response.json()
                break
            except (requests.exceptions.RequestException, ValueError):
                time.sleep(min(2 ** attempt, 10))
        if payload is None:
            response.raise_for_status()
            payload = response.json()

        if "errors" in payload:
            raise RuntimeError(payload["errors"])

        root_key = "organization" if owner_type == "organization" else "user"
        project = payload["data"][root_key]["projectV2"]
        if project is None:
            raise RuntimeError(
                f"Nenhum Project (v2) numero {number} encontrado para '{owner}' "
                f"({owner_type}). Confira o numero na URL do board."
            )
        project_title = project["title"]

        page = project["items"]
        items.extend(page["nodes"])

        if page["pageInfo"]["hasNextPage"]:
            cursor = page["pageInfo"]["endCursor"]
            time.sleep(1)
        else:
            break

    return project_title, items


def to_rows(items: list[dict]) -> list[dict]:
    rows = []
    for item in items:
        content = item.get("content") or {}
        status = item.get("status")
        assignees = content.get("assignees", {}).get("nodes", []) if content.get("assignees") else []
        rows.append({
            "item_id": item["id"],
            "type": content.get("type", "DraftIssue"),
            "status": status["name"] if status else None,
            "number": content.get("number"),
            "title": content.get("title"),
            "url": content.get("url"),
            "state": content.get("state"),
            "repository": (content.get("repository") or {}).get("nameWithOwner"),
            "assignees": ";".join(a["login"] for a in assignees),
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
    parser.add_argument("--owner", required=True, help="login do dono do board (usuario ou organizacao)")
    parser.add_argument("--owner-type", choices=["user", "organization"], default="user")
    parser.add_argument("--number", type=int, required=True, help="numero do Project (v2), da URL do board")
    parser.add_argument("--output", default="data/snapshot_lab01s02.csv")
    args = parser.parse_args()

    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Erro: defina GITHUB_TOKEN no arquivo .env (veja .env.example)", file=sys.stderr)
        sys.exit(1)

    print(f"Buscando itens do Project #{args.number} de {args.owner}...")
    title, items = fetch_items(token, args.owner, args.number, args.owner_type)
    rows = to_rows(items)
    if not rows:
        print("Aviso: o board nao tem itens ainda.", file=sys.stderr)
        sys.exit(0)
    save_csv(rows, args.output)
    print(f"OK: board '{title}' — {len(rows)} itens salvos em {args.output}")


if __name__ == "__main__":
    main()
