"""Testes do dataset final e do dicionario de dados (entregavel da S02)."""
import json

import pandas as pd
import pytest

from analise.dataset import COLUNAS, dicionario, dicionario_markdown, executar, montar


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "metricas.json").write_text(json.dumps([
        {"repo": "o/b", "releases_por_semana": 2.0, "lead_time_release_h": 10.0,
         "cfr_ci": 0.1, "recovery_median_h": 2.0},
        {"repo": "o/a", "releases_por_semana": 0.1, "lead_time_release_h": 900.0,
         "cfr_ci": 0.6, "recovery_median_h": None},
    ]), encoding="utf-8")
    (tmp_path / "selecao").mkdir()
    pd.DataFrame([
        {"full_name": "o/a", "html_url": "u", "default_branch": "main", "stars": 1,
         "forks": 2, "language": "Go", "contributors": 3, "created_at": "2020-01-01",
         "age_years": 6.0},
        {"full_name": "o/b", "html_url": "u", "default_branch": "main", "stars": 9,
         "forks": 8, "language": "Rust", "contributors": 7, "created_at": "2021-01-01",
         "age_years": 5.0},
    ]).to_csv(tmp_path / "selecao" / "repos.csv", index=False)
    return str(tmp_path)


def test_junta_metadados_metricas_e_dora(data_dir):
    df, _ = montar(data_dir)
    assert len(df) == 2
    for col in ("language", "releases_por_semana", "dora_geral"):
        assert col in df.columns, col


def test_ordenado_por_nome_para_diff_estavel(data_dir):
    """Ordem fixa: o grupo replicador compara o CSV dele com o nosso."""
    df, _ = montar(data_dir)
    assert list(df["full_name"]) == ["o/a", "o/b"]


def test_so_entram_colunas_documentadas(data_dir):
    df, _ = montar(data_dir)
    documentadas = {c for c, *_ in COLUNAS}
    assert set(df.columns) <= documentadas


def test_avisa_coluna_documentada_mas_ausente(data_dir):
    """Se o pipeline nao gerou uma metrica, o usuario precisa saber."""
    _, faltando = montar(data_dir)
    assert "cfr_entrega_v1_semver" in faltando


def test_dicionario_cobre_todas_as_colunas_do_csv(data_dir):
    df, _ = montar(data_dir)
    dic = dicionario()
    assert set(df.columns) <= set(dic["coluna"])


def test_dicionario_tem_unidade_e_descricao_em_tudo():
    """Sem unidade o replicador nao sabe se o lead time esta em horas ou dias."""
    dic = dicionario()
    assert not dic["unidade"].isna().any() and (dic["unidade"].str.len() > 0).all()
    assert (dic["descricao"].str.len() > 20).all()


def test_markdown_lista_as_colunas_e_a_janela():
    md = dicionario_markdown(("2025-10-01", "2026-09-30"), 300)
    assert "2025-10-01" in md and "300" in md
    for c, *_ in COLUNAS:
        assert f"`{c}`" in md, c


def test_executar_grava_csv_e_dicionario(data_dir):
    import os
    df, _, caminho = executar(data_dir, os.path.join(data_dir, "docs"))
    assert os.path.exists(caminho)
    assert os.path.exists(os.path.join(data_dir, "dicionario_dados.csv"))
    assert len(pd.read_csv(caminho)) == len(df)
