"""Testes da geração das tabelas da Metodologia (issue #70)."""
import csv
import json

import pytest

from scripts.tabelas_metodologia import (gerar, latex_escape, markdown, tabela_definicoes,
                                         tabela_funil)


def gravar_csv(caminho, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


@pytest.fixture
def cfg(tmp_path):
    data = tmp_path / "data"
    (data / "selecao").mkdir(parents=True)
    (data / "validacao").mkdir()
    gravar_csv(data / "selecao" / "funil.csv", [
        {"etapa": "candidatos (busca)", "restantes": "50", "descartados": "0", "motivo": ""},
        {"etapa": "poucas_releases", "restantes": "40", "descartados": "10", "motivo": "x"},
        {"etapa": "amostra_final", "restantes": "3", "descartados": "37", "motivo": "y"}])
    gravar_csv(data / "selecao" / "buscas.csv", [
        {"query": "stars:1..2", "total_count": "1500", "fetched": "1000"},
        {"query": "stars:>=3", "total_count": "20", "fetched": "20"}])
    (data / "metricas.json").write_text(json.dumps([
        {"repo": "o/a", "cfr_ci": 0.1, "lead_time_release_h": None},
        {"repo": "o/b", "cfr_ci": 0.2, "lead_time_release_h": 5.0}]))
    (data / "validacao" / "amostra.json").write_text(json.dumps(
        {"seed": 42, "n_repos": 2, "n_releases_total": 9, "repos": ["o/a", "o/b"]}))
    return {"data_dir": str(data), "window_start": "2025-10-01", "window_end": "2026-09-30",
            "selection": {"min_releases": 7, "sample_size": 3}}


def test_funil_preenche_criterio_com_o_config(cfg):
    _, linhas = tabela_funil(cfg["data_dir"], cfg["selection"])
    assert [l[0] for l in linhas] == ["candidatos (busca)", "poucas_releases", "amostra_final"]
    assert ">= 7 releases" in linhas[1][1]
    assert "completar 3" in linhas[2][1]
    assert linhas[2][3] == "37 (não avaliados)"


def test_definicoes_conta_cobertura_de_cada_coluna(cfg):
    _, linhas = tabela_definicoes(cfg["data_dir"])
    por_coluna = {l[5]: l[6] for l in linhas}
    assert por_coluna["`cfr_ci`"] == "2/2"
    assert por_coluna["`lead_time_release_h`"] == "1/2"          # None não conta
    assert por_coluna["`cfr_release_v1_semver`"] == "0/2"        # coluna ainda não coletada


def test_markdown_escapa_barra_vertical():
    md = markdown(["a", "b"], [["x|y", 1]])
    assert md.splitlines() == ["| a | b |", "|---|---|", "| x\\|y | 1 |"]


@pytest.mark.parametrize("entrada,saida", [
    ("cfr_ci", r"cfr\_ci"),
    ("`author_date`", r"author\_date"),
    ("50% & #1", r"50\% \& \#1"),
    (">= 5", r"$\geq$ 5"),
    ("Z > 0", r"Z $>$ 0"),
])
def test_latex_escape(entrada, saida):
    assert latex_escape(entrada) == saida


def test_gerar_grava_md_tex_e_injeta_no_relatorio(cfg, tmp_path):
    relatorio = tmp_path / "relatorio.md"
    relatorio.write_text("Antes\n<!-- tabela:funil -->\nvelho\n<!-- /tabela:funil -->\nDepois\n",
                         encoding="utf-8")
    saida = tmp_path / "tabelas"
    gerar(cfg, str(saida), str(relatorio))

    for nome in ("funil", "definicoes", "amostra_ouro"):
        assert (saida / f"{nome}.md").exists() and (saida / f"{nome}.tex").exists()
    assert r"\begin{tabular}" in (saida / "funil.tex").read_text(encoding="utf-8")

    texto = relatorio.read_text(encoding="utf-8")
    assert "velho" not in texto and "| poucas_releases |" in texto
    assert "1020 de 1520" in texto and "365 dias" in texto
    assert texto.startswith("Antes\n") and texto.endswith("Depois\n")

    # Rodar de novo não duplica a tabela.
    gerar(cfg, str(saida), str(relatorio))
    assert relatorio.read_text(encoding="utf-8").count("| poucas_releases |") == 1
