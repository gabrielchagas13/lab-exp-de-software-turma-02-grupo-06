"""Ida e volta: JSON -> Parquet -> JSON.

Este é o teste que sustenta a decisão de versionar só os Parquet. Se a volta
não for fiel, quem clonar o repositório não consegue retomar a coleta e teria
que refazer horas de chamadas à API.
"""
import json
import os

import pytest

from analise.exportar_parquet import exportar
from analise.importar_parquet import importar


def escrever(caminho, conteudo):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conteudo, f)


@pytest.fixture
def original(tmp_path):
    """Dois repositórios, cobrindo os casos chatos: campo nulo, lista vazia,
    commit repetido entre comparações e repositório sem runs."""
    d = tmp_path / "data"
    escrever(str(d / "runs" / "o__r.json"), {
        "repo": "o/r", "branch": "main", "splits": 3, "capped_days": ["2026-02-01"],
        "runs": [
            {"id": 1, "workflow_id": 9, "name": "CI", "conclusion": "success",
             "created_at": "2026-01-01T00:00:00Z", "run_started_at": "2026-01-01T00:00:00Z",
             "updated_at": "2026-01-01T01:00:00Z"},
            {"id": 2, "workflow_id": 9, "name": "CI", "conclusion": None,
             "created_at": "2026-01-02T00:00:00Z", "run_started_at": "2026-01-02T00:00:00Z",
             "updated_at": "2026-01-02T01:00:00Z"}]})
    escrever(str(d / "runs" / "o__vazio.json"), {
        "repo": "o/vazio", "branch": "master", "splits": 0, "capped_days": [], "runs": []})

    escrever(str(d / "releases" / "o__r.json"), {
        "repo": "o/r",
        "releases": [
            {"id": 7, "tag_name": "v1.0.0", "name": None, "body": "## Fixes\nx",
             "draft": False, "prerelease": False, "target_commitish": "main",
             "created_at": "2026-01-01T00:00:00Z", "published_at": "2026-01-01T00:00:00Z",
             "in_window": True},
            {"id": 8, "tag_name": "v1.1.0", "name": "Segunda", "body": None,
             "draft": False, "prerelease": False, "target_commitish": "main",
             "created_at": "2026-02-01T00:00:00Z", "published_at": None,
             "in_window": True}],
        "tags": [{"name": "v1.0.0", "sha": "a" * 40}, {"name": "v1.1.0", "sha": "b" * 40}]})
    escrever(str(d / "releases" / "o__vazio.json"), {
        "repo": "o/vazio", "releases": [], "tags": []})

    escrever(str(d / "commits" / "o__r.json"), {
        "repo": "o/r", "fonte": "git",
        "releases": [
            {"tag": "v1.0.0", "published_at": "2026-01-01T00:00:00Z", "base_tag": "v0.9.0",
             "commits": [{"sha": "c" * 40, "author_date": "2025-12-30T00:00:00Z",
                          "committer_date": "2025-12-30T01:00:00Z", "message": "feat: x"}]},
            {"tag": "v1.1.0", "published_at": "2026-02-01T00:00:00Z", "base_tag": "v1.0.0",
             "commits": [{"sha": "c" * 40, "author_date": "2025-12-30T00:00:00Z",
                          "committer_date": "2025-12-30T01:00:00Z", "message": "feat: x"},
                         {"sha": "d" * 40, "author_date": "2026-01-15T00:00:00Z",
                          "committer_date": "2026-01-15T00:00:00Z", "message": "fix: y"}]},
            # caso de borda do enunciado: release sem nenhum commit novo
            {"tag": "v1.2.0", "published_at": "2026-03-01T00:00:00Z", "base_tag": "v1.1.0",
             "commits": []}],
        "skipped": [{"tag": "v0.9.0", "reason": "sem release anterior"}]})
    escrever(str(d / "commits" / "o__vazio.json"), {
        "repo": "o/vazio", "fonte": "api", "releases": [],
        "skipped": [{"tag": "v1", "reason": "tag não encontrada (404)"}]})
    return str(d)


def ler_todos(pasta):
    return {f: json.load(open(os.path.join(pasta, f), encoding="utf-8"))
            for f in sorted(os.listdir(pasta)) if f.endswith(".json")}


@pytest.fixture
def ida_e_volta(original, tmp_path):
    """Exporta, apaga os JSON e reimporta num diretório limpo."""
    exportar(original)
    destino = tmp_path / "volta"
    os.makedirs(destino)
    import shutil
    shutil.copytree(os.path.join(original, "parquet"), os.path.join(destino, "parquet"))
    importar(str(destino))
    return original, str(destino)


@pytest.mark.parametrize("pasta", ["runs", "releases", "commits"])
def test_mesmos_arquivos_e_mesmo_conteudo(ida_e_volta, pasta):
    orig, volta = ida_e_volta
    a, b = ler_todos(os.path.join(orig, pasta)), ler_todos(os.path.join(volta, pasta))
    assert set(a) == set(b), f"conjunto de arquivos difere em {pasta}"
    for nome in a:
        assert a[nome] == b[nome], f"{pasta}/{nome} difere"


def test_campo_nulo_volta_como_null_e_nao_nan(ida_e_volta):
    """NaN do pandas no JSON quebraria qualquer leitor depois."""
    _, volta = ida_e_volta
    rel = ler_todos(os.path.join(volta, "releases"))["o__r.json"]
    assert rel["releases"][0]["name"] is None
    assert rel["releases"][1]["body"] is None
    runs = ler_todos(os.path.join(volta, "runs"))["o__r.json"]
    assert runs["runs"][1]["conclusion"] is None


def test_repositorio_sem_runs_e_reconstruido(ida_e_volta):
    """Repositório sem nenhuma run não aparece em runs.parquet; ainda assim o
    JSON precisa existir, senão o pipeline tenta recoletar."""
    _, volta = ida_e_volta
    assert ler_todos(os.path.join(volta, "runs"))["o__vazio.json"]["runs"] == []


def test_commit_repetido_volta_nas_duas_releases(ida_e_volta):
    """A normalizacao guarda o commit uma vez; a volta recoloca nos dois lugares."""
    _, volta = ida_e_volta
    rels = ler_todos(os.path.join(volta, "commits"))["o__r.json"]["releases"]
    shas = {r["tag"]: [c["sha"] for c in r["commits"]] for r in rels}
    assert shas["v1.0.0"] == ["c" * 40]
    assert shas["v1.1.0"] == ["c" * 40, "d" * 40]


def test_campos_de_controle_voltam(ida_e_volta):
    _, volta = ida_e_volta
    runs = ler_todos(os.path.join(volta, "runs"))["o__r.json"]
    assert runs["splits"] == 3 and runs["capped_days"] == ["2026-02-01"]
    com = ler_todos(os.path.join(volta, "commits"))["o__r.json"]
    assert com["fonte"] == "git"
    assert com["skipped"] == [{"tag": "v0.9.0", "reason": "sem release anterior"}]


def test_published_at_usa_created_at_como_reserva(ida_e_volta):
    """A v1.1.0 tem published_at nulo; a regra do pipeline cai no created_at."""
    _, volta = ida_e_volta
    rels = ler_todos(os.path.join(volta, "commits"))["o__r.json"]["releases"]
    v11 = next(r for r in rels if r["tag"] == "v1.1.0")
    assert v11["published_at"] == "2026-02-01T00:00:00Z"


def test_nao_sobrescreve_sem_force(original):
    """Quem já tem a coleta no disco não pode perdê-la por rodar o importador."""
    exportar(original)
    caminho = os.path.join(original, "runs", "o__r.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"repo": "o/r", "marcador": True}, f)
    importar(original)
    assert json.load(open(caminho, encoding="utf-8")).get("marcador") is True


def test_force_sobrescreve(original):
    exportar(original)
    caminho = os.path.join(original, "runs", "o__r.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"repo": "o/r", "marcador": True}, f)
    importar(original, force=True)
    assert "marcador" not in json.load(open(caminho, encoding="utf-8"))


def test_sem_parquet_aborta_com_mensagem_util(tmp_path):
    with pytest.raises(SystemExit, match="exportar_parquet"):
        importar(str(tmp_path))


def test_release_sem_commits_novos_sobrevive(ida_e_volta):
    """Caso de borda do enunciado: release que nao traz commit novo.

    Ela nao gera linha em release_commits, entao some se a reconstrucao for
    feita a partir dos commits em vez da tabela de comparacoes."""
    _, volta = ida_e_volta
    rels = ler_todos(os.path.join(volta, "commits"))["o__r.json"]["releases"]
    v12 = next(r for r in rels if r["tag"] == "v1.2.0")
    assert v12["commits"] == [] and v12["base_tag"] == "v1.1.0"


def test_repo_so_com_releases_puladas_sobrevive(ida_e_volta):
    _, volta = ida_e_volta
    d = ler_todos(os.path.join(volta, "commits"))["o__vazio.json"]
    assert d["releases"] == [] and d["fonte"] == "api"
    assert d["skipped"][0]["reason"] == "tag não encontrada (404)"
