from pipeline.commits import collect_release_commits, collect_repo_commits, compare_commits
from pipeline.http import NotFoundError


def commit(i, date="2026-01-01T00:00:00Z", msg="msg"):
    return {"sha": f"sha{i}", "author": {"login": "a"},
            "commit": {"author": {"date": date}, "committer": {"date": date},
                       "message": msg + "\n\ncorpo longo"}}


class FakeClient:
    """Simula `compare` paginado: cada par base...head tem N commits."""
    def __init__(self, sizes, missing=()):
        self.sizes, self.missing = sizes, set(missing)
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, dict(params)))
        spec = path.rsplit("/compare/", 1)[1]
        base, head = spec.split("...")
        if base in self.missing or head in self.missing:
            raise NotFoundError(path)
        total = self.sizes.get((base, head), 0)
        per, page = params["per_page"], params["page"]
        start = (page - 1) * per
        items = [commit(i) for i in range(start, min(start + per, total))]
        return {"total_commits": total, "commits": items}, {}


def test_compare_pagina_acima_de_250_commits():
    client = FakeClient({("a", "b"): 253})
    commits = compare_commits(client, "o/r", "a", "b")
    assert len(commits) == 253
    assert [c[1]["page"] for c in client.calls] == [1, 2, 3]
    assert all(c[1]["per_page"] == 100 for c in client.calls)


def test_compare_reduz_campos_e_pega_primeira_linha_da_mensagem():
    client = FakeClient({("a", "b"): 1})
    [c] = compare_commits(client, "o/r", "a", "b")
    assert c == {"sha": "sha0", "author_date": "2026-01-01T00:00:00Z",
                 "committer_date": "2026-01-01T00:00:00Z", "message": "msg"}


def test_compare_sem_commits():
    client = FakeClient({})
    assert compare_commits(client, "o/r", "a", "b") == []
    assert len(client.calls) == 1


def test_compare_escapa_nome_de_tag():
    client = FakeClient({})
    compare_commits(client, "o/r", "rel/1.0 beta", "rel/1.1")
    assert client.calls[0][0] == "/repos/o/r/compare/rel/1.0%20beta...rel/1.1"


def releases(*tags, in_window=True):
    return [{"tag_name": t, "published_at": f"2026-0{i + 1}-01T00:00:00Z", "created_at": "x",
             "in_window": in_window if isinstance(in_window, bool) else in_window[i]}
            for i, t in enumerate(tags)]


def test_commits_entre_releases_consecutivas():
    client = FakeClient({("v1", "v2"): 2, ("v2", "v3"): 3})
    out, skipped = collect_release_commits(client, "o/r", releases("v1", "v2", "v3"))
    assert [(r["tag"], r["base_tag"], len(r["commits"])) for r in out] == [
        ("v2", "v1", 2), ("v3", "v2", 3)]
    assert skipped == [{"tag": "v1", "reason": "sem release anterior"}]


def test_tag_apagada_404_e_registrada_e_proxima_usa_ultima_valida_como_base():
    client = FakeClient({("v1", "v3"): 4}, missing={"v2"})
    out, skipped = collect_release_commits(client, "o/r", releases("v1", "v2", "v3"))
    assert [(r["tag"], r["base_tag"]) for r in out] == [("v3", "v1")]
    assert {"tag": "v2", "reason": "tag não encontrada (404)"} in skipped


def test_release_anterior_a_janela_serve_de_base_sem_ser_coletada():
    client = FakeClient({("v1", "v2"): 1})
    rels = releases("v1", "v2", in_window=[False, True])
    out, skipped = collect_release_commits(client, "o/r", rels)
    assert [r["tag"] for r in out] == ["v2"]
    assert skipped == []  # v1 está fora da janela: não é "ignorada"
    assert len(client.calls) == 1


def test_unica_release_nao_tem_commits():
    client = FakeClient({})
    out, skipped = collect_release_commits(client, "o/r", releases("v1"))
    assert out == []
    assert skipped == [{"tag": "v1", "reason": "sem release anterior"}]
    assert client.calls == []


def test_collect_repo_commits_grava_e_retoma(tmp_path):
    client = FakeClient({("v1", "v2"): 1})
    out_dir = str(tmp_path / "commits")
    first = collect_repo_commits(client, "owner/repo", releases("v1", "v2"), out_dir)
    n = len(client.calls)
    assert collect_repo_commits(client, "owner/repo", releases("v1", "v2"), out_dir) == first
    assert len(client.calls) == n
    assert (tmp_path / "commits" / "owner__repo.json").exists()


def test_pre_release_nao_entra_nem_serve_de_base():
    client = FakeClient({("v1", "v3"): 2})
    rels = releases("v1", "v2-rc", "v3")
    rels[1]["prerelease"] = True
    out, skipped = collect_release_commits(client, "o/r", rels)
    assert [(r["tag"], r["base_tag"]) for r in out] == [("v3", "v1")]
    assert skipped == [{"tag": "v1", "reason": "sem release anterior"}]
