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
