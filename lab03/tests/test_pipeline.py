import json

import pytest

from pipeline import __main__ as cli


def test_sem_token_aborta(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        cli.main(["--config", str(tmp_path / "c.json")])


def test_load_config(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"a": 1}))
    assert cli.load_config(str(p)) == {"a": 1}


def test_process_repo_integra_runs_releases_e_commits(tmp_path):
    from datetime import date

    def run(i, conclusion, h):
        t = f"2026-01-01T{h:02d}:00:00Z"
        return {"id": i, "workflow_id": 1, "name": "CI", "conclusion": conclusion,
                "created_at": t, "run_started_at": t, "updated_at": t}

    def rel(tag, day, **extra):
        return {"tag_name": tag, "published_at": f"2026-01-{day:02d}T00:00:00Z",
                "created_at": f"2026-01-{day:02d}T00:00:00Z", "draft": False,
                "prerelease": False, "id": day, "name": tag, "body": "",
                "target_commitish": "main", **extra}

    class Client:
        def get(self, path, params=None):
            if "/actions/runs" in path:
                runs = [run(1, "success", 1), run(2, "failure", 2), run(3, "success", 4)]
                return {"total_count": 3, "workflow_runs": runs}, {}
            commit = {"sha": "s", "commit": {"author": {"date": "2026-01-09T00:00:00Z"},
                                             "committer": {"date": "2026-01-09T00:00:00Z"},
                                             "message": "x"}}
            return {"total_commits": 1, "commits": [commit]}, {}

        def get_pages(self, path, params=None):
            if "/actions/runs" in path:
                return [self.get(path, params)[0]]
            if path.endswith("/releases"):
                return [[rel("v1", 1), rel("v2", 10)]]
            return [[]]

    row = cli.process_repo(Client(), {"full_name": "o/r", "default_branch": "main"},
                           date(2026, 1, 1), date(2026, 1, 31), str(tmp_path))
    assert row["repo"] == "o/r" and row["runs"] == 3 and row["releases"] == 2
    assert row["cfr_ci"] == pytest.approx(1 / 3)
    assert row["recovery_median_h"] == 2.0
    assert row["lead_time_release_h"] == 24.0 and row["lead_time_commit_h"] == 24.0
    assert (tmp_path / "commits" / "o__r.json").exists()
