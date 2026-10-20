"""Testes da validação das planilhas de rótulos (issue #64)."""
import csv
import json

import pytest

from validacao.amostra import COLUNAS_RELEASES, COLUNAS_REPOS
from validacao.validar_rotulos import main, validar


def gravar(caminho, colunas, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas)
        w.writeheader()
        w.writerows(linhas)


def repo(nome, tipo="biblioteca", entregas="sim"):
    return {"full_name": nome, "url": "", "linguagem": "", "estrelas": "",
            "tipo_projeto": tipo, "releases_sao_entregas": entregas}


def release(nome, tag, corretiva="nao"):
    return {"full_name": nome, "tag": tag, "url": "", "release_nome": "", "notas": "",
            "n_commits": "0", "commits": "", "corretiva": corretiva}


@pytest.fixture
def dir_val(tmp_path):
    """Amostra de 2 repositórios com 2 releases cada, planilhas de `gl` completas."""
    (tmp_path / "amostra.json").write_text(json.dumps(
        {"seed": 42, "n_repos": 2, "n_releases_total": 4, "repos": ["o/a", "o/b"]}))
    gravar(tmp_path / "rotulos_repos_gl.csv", COLUNAS_REPOS, [repo("o/a"), repo("o/b", "cli")])
    gravar(tmp_path / "rotulos_releases_gl.csv", COLUNAS_RELEASES,
           [release("o/a", "v1"), release("o/a", "v2", "sim"),
            release("o/b", "v1"), release("o/b", "v2")])
    return tmp_path


def test_planilhas_completas_sao_validas(dir_val):
    assert validar(str(dir_val), "gl") == ([], [])


def test_rotulo_em_branco_e_pendencia_nao_erro(dir_val):
    gravar(dir_val / "rotulos_repos_gl.csv", COLUNAS_REPOS, [repo("o/a", tipo=""), repo("o/b")])
    erros, pendencias = validar(str(dir_val), "gl")
    assert erros == [] and len(pendencias) == 1 and "tipo_projeto" in pendencias[0]


@pytest.mark.parametrize("valor", ["Sim", "sim ", "s", "talvez"])
def test_valor_fora_das_opcoes_e_erro(dir_val, valor):
    gravar(dir_val / "rotulos_releases_gl.csv", COLUNAS_RELEASES,
           [release("o/a", "v1", valor), release("o/a", "v2"),
            release("o/b", "v1"), release("o/b", "v2")])
    erros, _ = validar(str(dir_val), "gl")
    assert len(erros) == 1 and "corretiva" in erros[0]


def test_coluna_alterada_e_erro(dir_val):
    colunas = [c for c in COLUNAS_REPOS if c != "estrelas"]
    gravar(dir_val / "rotulos_repos_gl.csv", colunas,
           [{k: v for k, v in repo("o/a").items() if k in colunas}])
    erros, _ = validar(str(dir_val), "gl")
    assert any("colunas" in e for e in erros)


def test_item_repetido_fora_da_amostra_e_contagem(dir_val):
    gravar(dir_val / "rotulos_repos_gl.csv", COLUNAS_REPOS,
           [repo("o/a"), repo("o/a"), repo("x/intruso")])
    erros, _ = validar(str(dir_val), "gl")
    assert any("repetido" in e for e in erros)
    assert any("x/intruso" in e for e in erros)
    assert any("3 itens" in e for e in erros)


def test_arquivo_ausente_e_erro(dir_val):
    (dir_val / "rotulos_releases_gl.csv").unlink()
    erros, _ = validar(str(dir_val), "gl")
    assert any("não encontrado" in e for e in erros)


def test_cli_completo_falha_com_pendencia(dir_val, tmp_path_factory):
    gravar(dir_val / "rotulos_repos_gl.csv", COLUNAS_REPOS, [repo("o/a", entregas=""), repo("o/b")])
    config = tmp_path_factory.mktemp("cfg") / "config.json"
    config.write_text(json.dumps({"data_dir": str(dir_val.parent)}))
    (dir_val.parent / "validacao").mkdir(exist_ok=True)
    for f in dir_val.iterdir():
        (dir_val.parent / "validacao" / f.name).write_bytes(f.read_bytes())

    main(["--config", str(config), "--avaliador", "gl"])          # pendência sem --completo: ok
    with pytest.raises(SystemExit):
        main(["--config", str(config), "--avaliador", "gl", "--completo"])
