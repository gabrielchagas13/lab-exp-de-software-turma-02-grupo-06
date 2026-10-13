import csv
import json

from pipeline.dataset import COLUMNS, DICTIONARY, build_dataset


def test_dataset_junta_metadados_e_metricas(tmp_path):
    (tmp_path / "selecao").mkdir()
    (tmp_path / "selecao" / "repos.csv").write_text(
        "full_name,html_url,default_branch,stars,forks,language,contributors,created_at,age_years\n"
        "a/b,https://github.com/a/b,main,1500,10,Python,42,2020-01-01T00:00:00Z,6.7\n")
    (tmp_path / "metricas.json").write_text(json.dumps([
        {"repo": "a/b", "runs": 80, "releases": 6, "cfr_ci": 0.1, "cfr_entrega": None,
         "recovery_median_h": 2.5, "lead_time_release_h": None, "extra": 1},
        {"repo": "c/d", "runs": 60, "releases": 5}]))
    rows = build_dataset(str(tmp_path))
    assert [r["full_name"] for r in rows] == ["a/b", "c/d"]
    assert rows[0]["stars"] == "1500"
    assert rows[0]["cfr_entrega"] == "" and rows[0]["recovery_median_h"] == 2.5
    assert rows[1]["stars"] == ""
    with open(tmp_path / "dataset.csv", encoding="utf-8") as f:
        assert next(csv.reader(f)) == list(COLUMNS)
    with open(tmp_path / "dicionario_dados.csv", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == len(DICTIONARY)


def test_dataset_sem_selecao(tmp_path):
    (tmp_path / "metricas.json").write_text(json.dumps([{"repo": "a/b", "runs": 1}]))
    assert build_dataset(str(tmp_path))[0]["full_name"] == "a/b"
