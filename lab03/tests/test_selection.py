import csv
import io
from datetime import date
from urllib.error import HTTPError

from pipeline import selection
from pipeline.http import NotFoundError
from pipeline.selection import (count_releases, count_valid_runs, evaluate, funnel,
                                search_candidates, select_repositories)

START, END = date(2025, 10, 1), date(2026, 9, 30)
CFG = {"min_releases": 5, "min_runs": 50}


def cand(name, stars=2000, **kw):
    return {"full_name": name, "html_url": f"https://github.com/{name}", "default_branch": "main",
            "stargazers_count": stars, "forks_count": 1, "language": "Go", "fork": False,
            "archived": False, "pushed_at": "2026-09-01T00:00:00Z",
            "created_at": "2018-01-01T00:00:00Z", **kw}


def release(i, published="2026-01-01T00:00:00Z", **kw):
    return {"id": i, "tag_name": f"v{i}", "name": "", "body": "", "draft": False,
            "prerelease": False, "target_commitish": "main", "created_at": published,
            "published_at": published, **kw}


def run(i, conclusion="success"):
    return {"id": i, "workflow_id": 1, "name": "CI", "conclusion": conclusion,
            "created_at": "2026-01-01T00:00:00Z", "run_started_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:01:00Z"}


class FakeClient:
    """Simula a API por repositório: workflows, releases, runs e contribuidores."""
    def __init__(self, search=None, repos=None):
        self.search = search or {}   # query -> lista de itens
        self.repos = repos or {}     # full_name -> {"workflows", "releases", "runs", "error"}
        self.calls = []

    def _repo(self, path):
        name = "/".join(path.split("/")[2:4])
        spec = self.repos[name]
        if spec.get("error"):
            raise spec["error"]
        return spec

    def get(self, path, params=None):
        self.calls.append(path)
        spec = self._repo(path)
        if path.endswith("/actions/workflows"):
            return {"total_count": spec.get("workflows", 1)}, {}
        if path.endswith("/actions/runs"):
            runs = spec.get("runs", [])
            if params["per_page"] == 1:
                return {"total_count": len(runs), "workflow_runs": runs[:1]}, {}
            page = params.get("page", 1)
            return {"total_count": len(runs),
                    "workflow_runs": runs[(page - 1) * 100: page * 100]}, {}
        if path.endswith("/contributors"):
            return [{"login": "a"}], {"link": '<https://x/contributors?page=9>; rel="last"'}
        raise AssertionError(path)

    def get_pages(self, path, params=None):
        self.calls.append(path)
        if path == "/search/repositories":
            items = self.search[params["q"]]
            return [{"total_count": len(items), "items": items[:2]},
                    {"total_count": len(items), "items": items[2:]}]
        spec = self._repo(path)
        if path.endswith("/releases"):
            return [spec.get("releases", [])]
        if path.endswith("/actions/runs"):
            return [{"workflow_runs": spec.get("runs", [])}]
        raise AssertionError(path)


def good_repo(n_releases=5, n_runs=50):
    return {"releases": [release(i) for i in range(n_releases)],
            "runs": [run(i) for i in range(n_runs)]}


# ---- busca ---------------------------------------------------------------
def test_busca_fatiada_remove_duplicatas_e_registra_fatias():
    client = FakeClient(search={
        "stars:1..2 archived:false": [cand("b/b"), cand("A/a"), cand("c/c")],
        "stars:>2 archived:false": [cand("c/c"), cand("d/d")],
    })
    items, slices = search_candidates(client, ["1..2", ">2"], "archived:false")
    assert [i["full_name"] for i in items] == ["A/a", "b/b", "c/c", "d/d"]
    assert slices == [{"query": "stars:1..2 archived:false", "total_count": 3, "fetched": 3},
                      {"query": "stars:>2 archived:false", "total_count": 2, "fetched": 2}]


# ---- contagens -----------------------------------------------------------
def test_conta_so_releases_da_janela_sem_prerelease():
    rels = [{"in_window": True, "prerelease": False}, {"in_window": True, "prerelease": True},
            {"in_window": False, "prerelease": False}, {"in_window": True, "prerelease": False}]
    assert count_releases(rels) == 2


def test_runs_cancelados_e_em_andamento_nao_contam():
    runs = [run(1), run(2, "failure"), run(3, "timed_out"), run(4, "cancelled"),
            run(5, "skipped"), run(6, None)]
    assert count_valid_runs(runs) == 3


# ---- filtros -------------------------------------------------------------
def ev(client, item, tmp_path):
    return evaluate(client, item, START, END, CFG, str(tmp_path / "runs"))


def test_incluido_no_limite_minimo(tmp_path):
    client = FakeClient(repos={"o/r": good_repo()})
    status, info = ev(client, cand("o/r"), tmp_path)
    assert status == "incluido"
    assert info == {"releases": 5, "valid_runs": 50}
    assert (tmp_path / "runs" / "o__r.json").exists()  # runs reaproveitados pelo pipeline


def test_fork_e_arquivado_descartados_sem_chamar_api(tmp_path):
    client = FakeClient()
    assert ev(client, cand("o/r", fork=True), tmp_path)[0] == "fork_ou_arquivado"
    assert ev(client, cand("o/r", archived=True), tmp_path)[0] == "fork_ou_arquivado"
    assert client.calls == []


def test_sem_push_na_janela(tmp_path):
    client = FakeClient()
    assert ev(client, cand("o/r", pushed_at="2025-09-30T23:00:00Z"), tmp_path)[0] == \
        "sem_push_na_janela"
    assert ev(client, cand("o/r", pushed_at=None), tmp_path)[0] == "sem_push_na_janela"
    assert client.calls == []


def test_sem_actions_nao_coleta_releases(tmp_path):
    client = FakeClient(repos={"o/r": {**good_repo(), "workflows": 0}})
    assert ev(client, cand("o/r"), tmp_path)[0] == "sem_actions"
    assert client.calls == ["/repos/o/r/actions/workflows"]


def test_poucas_releases_ignora_prerelease_draft_e_fora_da_janela(tmp_path):
    rels = [release(i) for i in range(4)] + [
        release(10, prerelease=True), release(11, draft=True),
        release(12, published="2025-01-01T00:00:00Z")]
    client = FakeClient(repos={"o/r": {**good_repo(), "releases": rels}})
    status, info = ev(client, cand("o/r"), tmp_path)
    assert (status, info["releases"]) == ("poucas_releases", 4)


def test_poucos_runs_pela_contagem_previa_nao_coleta_runs(tmp_path):
    client = FakeClient(repos={"o/r": good_repo(n_runs=49)})
    assert ev(client, cand("o/r"), tmp_path)[0] == "poucos_runs"
    assert not (tmp_path / "runs").exists()


def test_poucos_runs_validos_apos_coleta(tmp_path):
    runs = [run(i) for i in range(45)] + [run(100 + i, "cancelled") for i in range(10)]
    client = FakeClient(repos={"o/r": {**good_repo(), "runs": runs}})
    status, info = ev(client, cand("o/r"), tmp_path)
    assert (status, info["valid_runs"]) == ("poucos_runs", 45)


def test_inacessivel(tmp_path):
    for err in (NotFoundError("x"), HTTPError("x", 451, "blocked", {}, io.BytesIO(b""))):
        client = FakeClient(repos={"o/r": {"error": err}})
        assert ev(client, cand("o/r"), tmp_path)[0] == "inacessivel"


# ---- funil ---------------------------------------------------------------
def test_funil_contabiliza_cada_etapa():
    statuses = (["fork_ou_arquivado"] * 2 + ["sem_actions"] * 3 + ["poucas_releases"] * 4
                + ["poucos_runs"] + ["incluido"] * 2 + ["nao_avaliado"] * 5)
    rows = {r["etapa"]: r for r in funnel([{"status": s} for s in statuses])}
    assert rows["candidatos (busca)"]["restantes"] == 17
    assert (rows["fork_ou_arquivado"]["restantes"], rows["fork_ou_arquivado"]["descartados"]) == (15, 2)
    assert rows["sem_push_na_janela"]["descartados"] == 0
    assert rows["sem_actions"]["restantes"] == 12
    assert rows["poucas_releases"]["restantes"] == 8
    assert rows["poucos_runs"]["restantes"] == 7
    assert (rows["amostra_final"]["restantes"], rows["amostra_final"]["descartados"]) == (2, 5)


# ---- etapa completa ------------------------------------------------------
def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_world():
    names = [f"o/r{i}" for i in range(8)]
    repos = {n: good_repo() for n in names}
    repos["o/r1"]["workflows"] = 0
    repos["o/r2"]["releases"] = []
    search = {"stars:1000..2000": [cand(n) for n in names[:5]],
              "stars:>=2000": [cand(n, stars=5000) for n in names[4:]]}
    return search, repos


def test_select_repositories_completa_amostra_e_grava_saidas(tmp_path):
    search, repos = make_world()
    client = FakeClient(search, repos)
    sel = {"sample_size": 3, "star_ranges": ["1000..2000", ">=2000"]}
    out = select_repositories(client, sel, START, END, str(tmp_path), log=lambda *_: None)

    assert len(out) == 3
    assert all(r["default_branch"] == "main" for r in out)
    assert not {"o/r1", "o/r2"} & {r["full_name"] for r in out}

    sel_dir = tmp_path / "selecao"
    funil = {r["etapa"]: r for r in read_csv(sel_dir / "funil.csv")}
    assert funil["candidatos (busca)"]["restantes"] == "8"
    assert funil["amostra_final"]["restantes"] == "3"
    cands = read_csv(sel_dir / "candidatos.csv")
    assert len(cands) == 8
    meta = read_csv(sel_dir / "repos.csv")
    assert [m["full_name"] for m in meta] == [r["full_name"] for r in out]
    assert meta[0]["contributors"] == "9" and meta[0]["language"] == "Go"
    assert len(read_csv(sel_dir / "buscas.csv")) == 2


def test_select_repositories_reprodutivel_pela_semente(tmp_path):
    search, repos = make_world()
    sel = {"sample_size": 3, "star_ranges": ["1000..2000", ">=2000"], "seed": 7}
    a = select_repositories(FakeClient(search, repos), sel, START, END, str(tmp_path / "a"),
                            log=lambda *_: None)
    b = select_repositories(FakeClient(search, repos), sel, START, END, str(tmp_path / "b"),
                            log=lambda *_: None)
    assert a == b


def test_select_repositories_avisa_amostra_incompleta(tmp_path):
    search, repos = make_world()
    logs = []
    sel = {"sample_size": 50, "star_ranges": ["1000..2000", ">=2000"]}
    out = select_repositories(FakeClient(search, repos), sel, START, END, str(tmp_path),
                              log=logs.append)
    assert len(out) == 6
    assert any("aviso" in m for m in logs)


def test_defaults_seguem_a_especificacao():
    assert selection.DEFAULTS["min_releases"] == 5
    assert selection.DEFAULTS["min_runs"] == 50
