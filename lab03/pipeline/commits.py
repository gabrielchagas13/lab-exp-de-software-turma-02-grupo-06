"""Coleta dos commits entre releases consecutivas (endpoint compare)."""
from urllib.parse import quote

from pipeline.http import NotFoundError
from pipeline.store import load_or_build

PER_PAGE = 100


def _slim(commit):
    info = commit["commit"]
    return {"sha": commit["sha"],
            "author_date": info["author"]["date"],
            "committer_date": info["committer"]["date"],
            "message": (info.get("message") or "").split("\n", 1)[0]}


def compare_commits(client, repo, base, head):
    """Todos os commits de `base...head`, paginando com per_page/page.

    Um compare pode ter mais de 250 commits, então a paginação segue até somar
    `total_commits` (ou a página vir vazia). Levanta `NotFoundError` se alguma
    das referências não existe.
    """
    path = f"/repos/{repo}/compare/{quote(base, safe='/')}...{quote(head, safe='/')}"
    commits, page, total = [], 1, None
    while total is None or len(commits) < total:
        body, _ = client.get(path, {"per_page": PER_PAGE, "page": page})
        total = body.get("total_commits", len(body["commits"]))
        if not body["commits"]:
            break
        commits.extend(_slim(c) for c in body["commits"])
        page += 1
    return commits


def collect_release_commits(client, repo, releases):
    """Commits novos de cada release da janela, relativos à release anterior.

    `releases` vem de `pipeline.releases.collect_releases` (ordem cronológica,
    com `in_window`). A base de cada release é a anterior que ainda existe: se
    o compare dá 404 (tag apagada), a release é registrada em `skipped` e
    ignorada, e a próxima usa como base a última release válida. A primeira
    release do histórico não tem base e também vai para `skipped`.
    """
    out, skipped = [], []
    base = None
    for rel in releases:
        tag = rel["tag_name"]
        if base is None:
            if rel["in_window"]:
                skipped.append({"tag": tag, "reason": "sem release anterior"})
            base = tag
            continue
        try:
            commits = compare_commits(client, repo, base, tag) if rel["in_window"] else None
        except NotFoundError:
            skipped.append({"tag": tag, "reason": "tag não encontrada (404)"})
            continue
        if commits is not None:
            out.append({"tag": tag, "published_at": rel["published_at"] or rel["created_at"],
                        "base_tag": base, "commits": commits})
        base = tag
    return out, skipped


def collect_repo_commits(client, repo, releases, out_dir):
    """Coleta e grava `out_dir/<owner>__<repo>.json`; pula se já existir (retomada)."""
    def build():
        items, skipped = collect_release_commits(client, repo, releases)
        return {"repo": repo, "releases": items, "skipped": skipped}
    return load_or_build(out_dir, repo, build)
