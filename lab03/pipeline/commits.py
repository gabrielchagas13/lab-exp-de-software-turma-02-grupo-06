"""Coleta dos commits entre releases consecutivas (endpoint compare)."""
from urllib.parse import quote

from pipeline import git_local
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


def _commits_do_clone(repo_dir, base, head):
    """Adapta o git local à mesma interface do `compare` da API.

    Tag ausente no clone é o equivalente local do 404 da API (tag apagada ou
    reescrita), e segue o mesmo tratamento: a release é registrada em `skipped`."""
    for tag in (base, head):
        if not git_local.tag_existe(repo_dir, tag):
            raise NotFoundError(tag)
    return git_local.commits_entre(repo_dir, base, head)


def collect_release_commits(client, repo, releases, repo_dir=None):
    """Commits novos de cada release da janela, relativos à release anterior.

    `releases` vem de `pipeline.releases.collect_releases` (ordem cronológica,
    com `in_window`). A base de cada release é a anterior que ainda existe: se
    o compare dá 404 (tag apagada), a release é registrada em `skipped` e
    ignorada, e a próxima usa como base a última release válida. A primeira
    release do histórico não tem base e também vai para `skipped`.

    Só entram releases da definição principal (`prerelease=false`): pré-releases
    não são deploys e, se fossem base do compare, deslocariam os commits entre
    releases. Elas ficam para a variante da RQ 07.
    """
    out, skipped = [], []
    base = None
    for rel in releases:
        if rel.get("prerelease"):
            continue
        tag = rel["tag_name"]
        if base is None:
            if rel["in_window"]:
                skipped.append({"tag": tag, "reason": "sem release anterior"})
            base = tag
            continue
        try:
            if not rel["in_window"]:
                commits = None
            elif repo_dir:
                commits = _commits_do_clone(repo_dir, base, tag)
            else:
                commits = compare_commits(client, repo, base, tag)
        except NotFoundError:
            skipped.append({"tag": tag, "reason": "tag não encontrada (404)"})
            continue
        if commits is not None:
            out.append({"tag": tag, "published_at": rel["published_at"] or rel["created_at"],
                        "base_tag": base, "commits": commits})
        base = tag
    return out, skipped


def collect_repo_commits(client, repo, releases, out_dir, clones_dir=None):
    """Coleta e grava `out_dir/<owner>__<repo>.json`; pula se já existir (retomada).

    Com `clones_dir`, os commits vêm de um clone local (rápido e sem teto de
    10.000 commits); sem ele, do endpoint `compare` da API. A origem fica
    registrada no JSON, porque as duas podem divergir em comparações muito
    grandes e o artigo precisa dizer qual foi usada."""
    def build():
        repo_dir = None
        if clones_dir:
            repo_dir = git_local.clonar(repo, clones_dir)
        items, skipped = collect_release_commits(client, repo, releases, repo_dir)
        return {"repo": repo, "fonte": "git" if repo_dir else "api",
                "releases": items, "skipped": skipped}
    return load_or_build(out_dir, repo, build)
