import json
from datetime import date

from pipeline.releases import collect_releases, collect_repo_releases, collect_tags

START, END = date(2025, 10, 1), date(2026, 9, 30)


def rel(tag, published, **kw):
    return {"id": hash(tag) % 1000, "tag_name": tag, "name": tag, "body": "", "draft": False,
            "prerelease": False, "target_commitish": "main", "created_at": published,
            "published_at": published, "author": {"login": "x"}, **kw}


class FakeClient:
    def __init__(self, releases=(), tags=()):
        self.releases, self.tags = list(releases), list(tags)
        self.calls = []

    def get_pages(self, path, params=None):
        self.calls.append(path)
        data = self.releases if path.endswith("/releases") else self.tags
        return [data[:2], data[2:]]  # duas páginas


def test_descarta_drafts_e_mantem_prereleases():
    client = FakeClient([
        rel("v1", "2026-01-01T00:00:00Z"),
        rel("v2-rc", "2026-02-01T00:00:00Z", prerelease=True),
        rel("v3", "2026-03-01T00:00:00Z", draft=True),
    ])
    out = collect_releases(client, "o/r", START, END)
    assert [r["tag_name"] for r in out] == ["v1", "v2-rc"]
    assert out[1]["prerelease"] is True
    assert "author" not in out[0]  # só os campos necessários


def test_ordena_cronologicamente_e_junta_paginas():
    client = FakeClient([
        rel("v3", "2026-03-01T00:00:00Z"),
        rel("v1", "2026-01-01T00:00:00Z"),
        rel("v2", "2026-02-01T00:00:00Z"),
    ])
    out = collect_releases(client, "o/r", START, END)
    assert [r["tag_name"] for r in out] == ["v1", "v2", "v3"]


def test_marca_janela_e_mantem_release_anterior_como_base():
    client = FakeClient([
        rel("v0", "2025-09-30T23:59:59Z"),   # antes da janela
        rel("v1", "2025-10-01T00:00:00Z"),   # primeiro instante da janela
        rel("v2", "2026-09-30T23:59:59Z"),   # último dia da janela
        rel("v3", "2026-10-01T00:00:00Z"),   # depois
    ])
    out = collect_releases(client, "o/r", START, END)
    assert [(r["tag_name"], r["in_window"]) for r in out] == [
        ("v0", False), ("v1", True), ("v2", True), ("v3", False)]


def test_release_sem_published_at_usa_created_at():
    client = FakeClient([rel("v1", None, created_at="2026-01-01T00:00:00Z")])
    out = collect_releases(client, "o/r", START, END)
    assert out[0]["in_window"] is True


def test_collect_tags():
    client = FakeClient(tags=[{"name": "v1", "commit": {"sha": "a"}, "zipball_url": "z"},
                              {"name": "v2", "commit": {"sha": "b"}},
                              {"name": "v3", "commit": {"sha": "c"}}])
    assert collect_tags(client, "o/r") == [
        {"name": "v1", "sha": "a"}, {"name": "v2", "sha": "b"}, {"name": "v3", "sha": "c"}]


def test_collect_repo_releases_grava_e_retoma(tmp_path):
    client = FakeClient([rel("v1", "2026-01-01T00:00:00Z")], [{"name": "v1", "commit": {"sha": "a"}}])
    out_dir = str(tmp_path / "releases")
    first = collect_repo_releases(client, "owner/repo", START, END, out_dir)
    assert (tmp_path / "releases" / "owner__repo.json").exists()
    n_calls = len(client.calls)
    again = collect_repo_releases(client, "owner/repo", START, END, out_dir)
    assert again == first
    assert len(client.calls) == n_calls  # retomada: nenhuma chamada nova
    saved = json.loads((tmp_path / "releases" / "owner__repo.json").read_text())
    assert saved["tags"] == [{"name": "v1", "sha": "a"}]
