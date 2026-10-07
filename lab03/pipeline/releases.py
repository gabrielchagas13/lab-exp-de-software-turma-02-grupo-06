"""Coleta de releases e tags de um repositório (REST, paginação via header Link)."""
from datetime import datetime, timedelta, timezone

from pipeline.store import load_or_build

KEEP_FIELDS = ("id", "tag_name", "name", "body", "draft", "prerelease",
               "target_commitish", "created_at", "published_at")


def _release_date(release):
    """Data de publicação; releases sem `published_at` caem para `created_at`."""
    value = release.get("published_at") or release["created_at"]
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _in_window(release, start, end):
    lo = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    hi = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)
    return lo <= _release_date(release) < hi


def collect_releases(client, repo, start, end):
    """Releases publicadas (draft=false) do repositório, em ordem cronológica.

    Retorna todas as releases não-rascunho (incluindo pré-releases, marcadas em
    `prerelease`) com a flag `in_window`. As anteriores à janela são mantidas
    porque servem de base (`compare`) para a primeira release da janela.
    """
    releases = []
    for page in client.get_pages(f"/repos/{repo}/releases", {"per_page": 100}):
        for item in page:
            if item.get("draft"):
                continue
            rel = {k: item.get(k) for k in KEEP_FIELDS}
            rel["in_window"] = _in_window(item, start, end)
            releases.append(rel)
    releases.sort(key=_release_date)
    return releases


def collect_tags(client, repo):
    """Tags do repositório como lista de `{name, sha}`."""
    tags = []
    for page in client.get_pages(f"/repos/{repo}/tags", {"per_page": 100}):
        for item in page:
            tags.append({"name": item["name"], "sha": item["commit"]["sha"]})
    return tags


def collect_repo_releases(client, repo, start, end, out_dir):
    """Coleta e grava `out_dir/<owner>__<repo>.json`; pula se já existir (retomada)."""
    return load_or_build(out_dir, repo, lambda: {
        "repo": repo, "releases": collect_releases(client, repo, start, end),
        "tags": collect_tags(client, repo)})
