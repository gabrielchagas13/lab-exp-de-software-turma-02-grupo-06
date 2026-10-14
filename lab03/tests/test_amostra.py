"""Testes do sorteio da amostra-ouro e das planilhas de rotulagem."""
import csv
import json

import pytest

from validacao.amostra import gerar_planilhas, releases_da_janela, sortear


@pytest.fixture
def data_dir(tmp_path):
    """Amostra final de 4 repositórios, cada um com releases na janela e fora."""
    (tmp_path / "selecao").mkdir()
    with open(tmp_path / "selecao" / "repos.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["full_name"])
        w.writeheader()
        w.writerows([{"full_name": f"o/r{i}"} for i in range(4)])

    (tmp_path / "releases").mkdir()
    for i in range(4):
        rels = [{"tag_name": f"v{j}", "in_window": True, "prerelease": False,
                 "published_at": f"2026-01-{j + 1:02d}T00:00:00Z"} for j in range(8)]
        rels.append({"tag_name": "antiga", "in_window": False, "prerelease": False,
                     "published_at": "2020-01-01T00:00:00Z"})
        rels.append({"tag_name": "rc1", "in_window": True, "prerelease": True,
                     "published_at": "2026-02-01T00:00:00Z"})
        (tmp_path / "releases" / f"o__r{i}.json").write_text(
            json.dumps({"repo": f"o/r{i}", "releases": rels}), encoding="utf-8")
    return str(tmp_path)


def test_ignora_fora_da_janela_e_pre_releases(data_dir):
    tags = {r["tag_name"] for r in releases_da_janela(data_dir, "o/r0")}
    assert "antiga" not in tags and "rc1" not in tags and len(tags) == 8


def test_sorteia_n_repos_e_n_releases_por_repo(data_dir):
    repos, releases = sortear(data_dir, n_repos=3, n_releases=5)
    assert len(repos) == 3
    assert len(releases) == 15
    for nome in {r["full_name"] for r in repos}:
        assert sum(1 for r in releases if r["full_name"] == nome) == 5


def test_mesma_semente_mesmo_sorteio(data_dir):
    a, ra = sortear(data_dir, n_repos=3, seed=42)
    b, rb = sortear(data_dir, n_repos=3, seed=42)
    assert [x["full_name"] for x in a] == [x["full_name"] for x in b]
    assert [(x["full_name"], x["tag"]) for x in ra] == [(x["full_name"], x["tag"]) for x in rb]


def test_sementes_diferentes_sorteiam_diferente(data_dir):
    _, ra = sortear(data_dir, n_repos=3, seed=1)
    _, rb = sortear(data_dir, n_repos=3, seed=2)
    assert [(x["full_name"], x["tag"]) for x in ra] != [(x["full_name"], x["tag"]) for x in rb]


def test_repo_com_menos_releases_que_o_pedido_nao_quebra(data_dir):
    _, releases = sortear(data_dir, n_repos=4, n_releases=50)
    assert len(releases) == 32  # 4 repos x 8 releases disponíveis na janela


def test_planilhas_tem_links_diretos_e_rotulos_vazios(data_dir):
    gerar_planilhas(data_dir, avaliadores=("mv",), n_repos=2, n_releases=3)
    import os
    with open(os.path.join(data_dir, "validacao", "rotulos_releases_mv.csv"),
              encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert all(l["url"] == f"https://github.com/{l['full_name']}/releases/tag/{l['tag']}"
               for l in linhas)
    assert all(l["corretiva"] == "" for l in linhas)


def test_os_tres_avaliadores_recebem_a_mesma_amostra(data_dir):
    import os
    gerar_planilhas(data_dir, n_repos=3, n_releases=4)
    conteudos = {open(os.path.join(data_dir, "validacao", f"rotulos_releases_{i}.csv"),
                      encoding="utf-8").read() for i in ("mv", "gc", "gl")}
    assert len(conteudos) == 1, "avaliadores não podem rotular amostras diferentes"


def test_nao_sobrescreve_planilha_ja_preenchida(data_dir):
    """Regerar depois de alguém rotular apagaria horas de trabalho manual."""
    import os
    gerar_planilhas(data_dir, avaliadores=("mv",), n_repos=2, n_releases=3)
    caminho = os.path.join(data_dir, "validacao", "rotulos_repos_mv.csv")
    with open(caminho, encoding="utf-8") as f:
        preenchido = f.read().replace(",,", ",cli,sim", 1)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(preenchido)

    res = gerar_planilhas(data_dir, avaliadores=("mv",), n_repos=2, n_releases=3)
    assert "rotulos_repos_mv.csv" in res["preservados"]
    with open(caminho, encoding="utf-8") as f:
        assert "cli" in f.read()


def test_grava_registro_do_sorteio(data_dir):
    """Sem o registro da semente, o sorteio não é reproduzível por outro grupo."""
    import os
    gerar_planilhas(data_dir, n_repos=3, n_releases=4, seed=7)
    with open(os.path.join(data_dir, "validacao", "amostra.json"), encoding="utf-8") as f:
        reg = json.load(f)
    assert reg["seed"] == 7 and reg["n_repos"] == 3 and len(reg["repos"]) == 3


def test_repo_sem_arquivo_de_releases_devolve_vazio(data_dir):
    """Repositório cujo JSON de releases não foi coletado não pode quebrar o sorteio."""
    assert releases_da_janela(data_dir, "o/inexistente") == []


def test_planilha_traz_evidencia_bruta_dos_commits(data_dir):
    """O avaliador precisa ler as mensagens de commit sem abrir o navegador."""
    import os
    dir_commits = os.path.join(data_dir, "commits")
    os.makedirs(dir_commits, exist_ok=True)
    with open(os.path.join(dir_commits, "o__r0.json"), "w", encoding="utf-8") as f:
        json.dump({"repo": "o/r0", "releases": [
            {"tag": "v0", "commits": [{"message": "fix: corrige crash"},
                                      {"message": "docs: atualiza readme"}]}]}, f)
    _, releases = sortear(data_dir, n_repos=4, n_releases=8)
    linha = next(r for r in releases if r["full_name"] == "o/r0" and r["tag"] == "v0")
    assert linha["n_commits"] == 2
    assert "fix: corrige crash" in linha["commits"]


def test_notas_sao_achatadas_e_sem_entidades_html():
    from validacao.amostra import _uma_linha
    assert _uma_linha("a&nbsp;b\n\nc", 50) == "a b c"
    assert _uma_linha("x" * 10, 4) == "xxxx..."


def test_planilha_nao_embute_sinais_da_heuristica():
    """A planilha traz evidência bruta, nunca 'mudou so o patch' ou 'tem fix'.

    Embutir os sinais da heurística induziria o avaliador a concordar com ela,
    inflando a precisão/recall medidas depois contra esse mesmo gabarito."""
    from validacao.amostra import COLUNAS_RELEASES
    proibidas = {"patch", "semver", "tem_fix", "heuristica", "predicao", "sugestao"}
    assert not proibidas & set(COLUNAS_RELEASES)
