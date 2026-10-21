"""Testes da exportação para Parquet.

O ponto central é **não perder informação**: o Parquet entra no repositório
como a cópia consultável do dado bruto, então qualquer campo que suma aqui
some para quem for replicar o estudo.
"""
import json
import os

import pandas as pd
import pytest

from analise.exportar_parquet import (exportar, tabelas_commits, tabelas_releases,
                                      tabelas_runs)


@pytest.fixture
def data_dir(tmp_path):
    for sub in ("runs", "releases", "commits"):
        (tmp_path / sub).mkdir()

    (tmp_path / "runs" / "o__r.json").write_text(json.dumps({
        "repo": "o/r", "branch": "main", "splits": 2, "capped_days": ["2026-01-05"],
        "runs": [{"id": 1, "workflow_id": 9, "name": "CI", "conclusion": "success",
                  "created_at": "2026-01-01T00:00:00Z",
                  "run_started_at": "2026-01-01T00:00:00Z",
                  "updated_at": "2026-01-01T01:00:00Z"}]}), encoding="utf-8")

    (tmp_path / "releases" / "o__r.json").write_text(json.dumps({
        "repo": "o/r",
        "tags": [{"name": "v1.0.0", "sha": "a" * 40}],
        "releases": [{"id": 7, "tag_name": "v1.0.0", "name": "Primeira",
                      "body": "## Bug Fixes\n- corrige tudo", "draft": False,
                      "prerelease": False, "target_commitish": "main",
                      "created_at": "2026-01-01T00:00:00Z",
                      "published_at": "2026-01-01T00:00:00Z", "in_window": True}]},
    ), encoding="utf-8")

    (tmp_path / "commits" / "o__r.json").write_text(json.dumps({
        "repo": "o/r", "fonte": "git",
        "skipped": [{"tag": "v0.9.0", "reason": "sem release anterior"}],
        "releases": [
            {"tag": "v1.0.0", "base_tag": "v0.9.0", "published_at": "2026-01-01T00:00:00Z",
             "commits": [{"sha": "c" * 40, "author_date": "2025-12-30T00:00:00Z",
                          "committer_date": "2025-12-30T01:00:00Z", "message": "feat: x"}]},
            # o mesmo commit aparece de novo noutra comparacao (compare cruzado)
            {"tag": "v1.1.0", "base_tag": "v1.0.0", "published_at": "2026-02-01T00:00:00Z",
             "commits": [{"sha": "c" * 40, "author_date": "2025-12-30T00:00:00Z",
                          "committer_date": "2025-12-30T01:00:00Z", "message": "feat: x"},
                         {"sha": "d" * 40, "author_date": "2026-01-15T00:00:00Z",
                          "committer_date": "2026-01-15T00:00:00Z", "message": "fix: y"}]}]},
    ), encoding="utf-8")
    return str(tmp_path)


# ---- preservacao de campos ----

def test_runs_preserva_todos_os_campos(data_dir):
    t = tabelas_runs(data_dir)
    assert set(t["runs"].columns) == {
        "repo", "id", "workflow_id", "name", "conclusion",
        "created_at", "run_started_at", "updated_at"}


def test_campos_de_controle_da_coleta_sao_preservados(data_dir):
    """splits e capped_days dizem se algum dia ficou truncado pelo teto da API.

    Sem eles não há como saber se a coleta de runs está completa."""
    c = tabelas_runs(data_dir)["runs_coleta"].iloc[0]
    assert c["splits"] == 2 and list(c["capped_days"]) == ["2026-01-05"]
    assert c["branch"] == "main"


def test_release_notes_sao_preservadas(data_dir):
    """O enunciado manda o avaliador da amostra-ouro ler as release notes;
    perder o `body` inviabiliza regerar a planilha de rotulagem."""
    r = tabelas_releases(data_dir)["releases"].iloc[0]
    assert "corrige tudo" in r["body"]
    assert r["target_commitish"] == "main" and r["in_window"]


def test_tags_sao_preservadas(data_dir):
    """Tags são a unidade de deploy da variante C3 da RQ 07."""
    t = tabelas_releases(data_dir)["tags"]
    assert list(t["name"]) == ["v1.0.0"] and len(t.iloc[0]["sha"]) == 40


def test_sha_completo_de_40_caracteres(data_dir):
    """Sem truncar: o sha é a chave de auditoria contra o GitHub."""
    c = tabelas_commits(data_dir)["commits"]
    assert (c["sha"].str.len() == 40).all()


def test_procedencia_e_releases_puladas_preservadas(data_dir):
    t = tabelas_commits(data_dir)
    assert t["commits_coleta"].iloc[0]["fonte"] == "git"
    pulada = t["releases_puladas"].iloc[0]
    assert pulada["tag"] == "v0.9.0" and "anterior" in pulada["reason"]


# ---- normalizacao ----

def test_commit_repetido_guardado_uma_vez_so(data_dir):
    """O mesmo commit entra em duas comparações; o conteúdo não se duplica."""
    t = tabelas_commits(data_dir)
    assert len(t["commits"]) == 2            # c e d
    assert len(t["release_commits"]) == 3    # c aparece em v1.0.0 e v1.1.0, d em v1.1.0


def test_vinculo_permite_reconstruir_a_lista_por_release(data_dir):
    """Nada se perde na normalização: dá para voltar ao formato original."""
    t = tabelas_commits(data_dir)
    junto = t["release_commits"].merge(t["commits"], on=["repo", "sha"])
    por_tag = junto.groupby("tag")["sha"].count().to_dict()
    assert por_tag == {"v1.0.0": 1, "v1.1.0": 2}
    assert set(junto.columns) >= {"tag", "base_tag", "author_date", "message"}


# ---- execucao completa ----

def test_exportar_grava_todas_as_tabelas(data_dir):
    resumo = exportar(data_dir)
    nomes = {r["tabela"] for r in resumo}
    assert nomes == {"runs", "runs_coleta", "releases", "tags",
                     "commits", "release_commits", "commits_coleta", "releases_puladas"}
    for r in resumo:
        caminho = os.path.join(data_dir, "parquet", f"{r['tabela']}.parquet")
        assert os.path.exists(caminho), r["tabela"]


def test_parquet_le_de_volta_igual(data_dir):
    exportar(data_dir)
    lido = pd.read_parquet(os.path.join(data_dir, "parquet", "releases.parquet"))
    assert len(lido) == 1 and "corrige tudo" in lido.iloc[0]["body"]


def test_leitura_por_coluna_funciona(data_dir):
    """A vantagem do colunar: carregar só o que interessa, sem ler o resto."""
    exportar(data_dir)
    so_datas = pd.read_parquet(os.path.join(data_dir, "parquet", "commits.parquet"),
                               columns=["repo", "author_date"])
    assert list(so_datas.columns) == ["repo", "author_date"]
