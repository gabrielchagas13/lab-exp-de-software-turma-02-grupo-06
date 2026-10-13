import csv
import json

import pytest

from pipeline import gold


def write_repos(tmp_path, n=10):
    p = tmp_path / "repos.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["full_name", "html_url"])
        for i in range(n):
            w.writerow([f"o/r{i}", f"https://github.com/o/r{i}"])
    commits = tmp_path / "commits"
    commits.mkdir()
    for i in range(n):
        rels = [{"tag": f"v1.0.{k}", "base_tag": f"v1.0.{k-1}", "published_at": "2026-01-01T00:00:00Z",
                 "commits": [{"message": "fix: x" if k % 2 else "feat: y"}]} for k in range(1, 8)]
        (commits / f"o__r{i}.json").write_text(json.dumps({"repo": f"o/r{i}", "releases": rels}))
    return p, commits


def test_sorteio_reprodutivel():
    names = [f"o/r{i}" for i in range(100)]
    assert gold.sample_repos(names) == gold.sample_repos(list(reversed(names)))
    assert len(gold.sample_repos(names)) == 60
    assert gold.sample_repos(names, seed=1) != gold.sample_repos(names, seed=2)


def test_build_sheets_gera_planilha_por_avaliador(tmp_path):
    repos, commits = write_repos(tmp_path)
    out = tmp_path / "gold"
    repo_rows, release_rows = gold.build_sheets(str(repos), str(commits), str(out), ["a", "b", "c"], n=4)
    assert len(repo_rows) == 4 and len(release_rows) == 4 * 5
    assert release_rows[0]["url"].startswith("https://github.com/o/r")
    for r in "abc":
        assert (out / f"rotulos_repos_{r}.csv").exists()
        assert (out / f"rotulos_releases_{r}.csv").exists()
    assert release_rows[0]["corretiva"] == ""  # planilha sem a saída da heurística


def test_fleiss_concordancia_total_e_indefinido():
    assert gold.fleiss([["sim", "sim", "sim"], ["nao", "nao", "nao"]]) == pytest.approx(1.0)
    assert gold.fleiss([["sim", "sim", "sim"]]) is None
    assert gold.fleiss([]) is None


def test_landis_koch():
    assert gold.landis_koch(-0.1) == "pobre"
    assert gold.landis_koch(0.2) == "leve"
    assert gold.landis_koch(0.5) == "moderada"
    assert gold.landis_koch(0.9) == "quase perfeita"
    assert gold.landis_koch(None) == "indefinido"


def test_consenso_maioria_e_empate():
    assert gold.consensus(["sim", "sim", "nao"]) == "sim"
    assert gold.consensus(["sim", "sim", "sim"]) == "sim"
    assert gold.consensus(["sim", "nao", "incerto"]) is None


def test_agreement_e_avaliacao(tmp_path):
    repos, commits = write_repos(tmp_path)
    out = tmp_path / "gold"
    _, release_rows = gold.build_sheets(str(repos), str(commits), str(out), ["a", "b", "c"], n=2)
    labels = {"a": "sim", "b": "sim", "c": "nao"}
    for r, lab in labels.items():
        for prefix, fields in (("repos", gold.REPO_FIELDS), ("releases", gold.RELEASE_FIELDS)):
            path = out / f"rotulos_{prefix}_{r}.csv"
            rows = list(csv.DictReader(open(path)))
            for i, row in enumerate(rows):
                if prefix == "repos":
                    row.update({"tipo_projeto": "cli", "releases_reais": "sim"})
                else:
                    row["corretiva"] = lab if i % 2 else "nao"
            gold._write_csv(str(path), fields, rows)
    result = gold.agreement(str(out), ["a", "b", "c"])
    assert result["corretiva"]["n"] == len(release_rows)
    assert result["tipo_projeto"]["kappa"] is None  # todos iguais: indefinido
    cons = result["corretiva"]["consenso"]
    metrics = gold.evaluate_heuristic(cons, {k: True for k in cons})
    assert metrics["n"] == len(cons) and metrics["recall"] == 1.0
    assert metrics["precisao"] == pytest.approx(sum(v == "sim" for v in cons.values()) / len(cons))


def test_heuristic_predictions(tmp_path):
    _, commits = write_repos(tmp_path, n=1)
    preds = gold.heuristic_predictions(str(commits), "v1")
    assert preds[("o/r0", "v1.0.3")] is True
