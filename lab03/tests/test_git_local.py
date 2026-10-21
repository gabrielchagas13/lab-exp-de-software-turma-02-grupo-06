"""Testes dos commits via clone local.

Monta um repositório git de verdade no tmp_path (rápido, sem rede) com um
histórico conhecido, e confere que `commits_entre` devolve exatamente os
commits que o `compare` da API devolveria para o mesmo par de tags.
"""
import subprocess

import pytest

from pipeline.git_local import (GitError, clonar, commits_entre, disponivel,
                                tag_existe)

pytestmark = pytest.mark.skipif(not disponivel(), reason="git não disponível")


def git(repo, *args):
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def commit(repo, mensagem, data="2026-01-01T00:00:00+00:00"):
    (repo / "arquivo.txt").write_text(mensagem, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "-m", mensagem, "--date", data)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    """Histórico linear: c0 (v1) -> c1, c2 (v2) -> c3 (v3)."""
    d = tmp_path / "repo"
    d.mkdir()
    git(d, "init", "-q", "-b", "main")
    commit(d, "c0", "2026-01-01T00:00:00+00:00")
    git(d, "tag", "v1")
    commit(d, "c1", "2026-01-02T00:00:00+00:00")
    commit(d, "c2", "2026-01-03T00:00:00+00:00")
    git(d, "tag", "v2")
    commit(d, "c3", "2026-01-04T00:00:00+00:00")
    git(d, "tag", "v3")
    return d


def test_commits_entre_traz_so_o_intervalo(repo):
    """base..head = commits de head que não estão em base — a semântica do compare."""
    msgs = [c["message"] for c in commits_entre(repo, "v1", "v2")]
    assert msgs == ["c2", "c1"]  # do mais novo para o mais antigo


def test_nao_inclui_o_commit_da_base(repo):
    assert "c0" not in [c["message"] for c in commits_entre(repo, "v1", "v3")]


def test_intervalo_vazio_quando_nao_ha_commits_novos(repo):
    assert commits_entre(repo, "v2", "v2") == []


def test_formato_igual_ao_da_api(repo):
    """O resto do pipeline não pode saber se o commit veio do git ou da API."""
    c = commits_entre(repo, "v1", "v2")[0]
    assert set(c) == {"sha", "author_date", "committer_date", "message"}
    assert len(c["sha"]) == 40
    assert c["author_date"].startswith("2026-01-03")  # ISO, como o commit.author.date


def test_data_do_autor_preservada(repo):
    """RQ 02 usa commit.author.date; o lead time depende dessa data estar certa."""
    datas = sorted(c["author_date"][:10] for c in commits_entre(repo, "v1", "v3"))
    assert datas == ["2026-01-02", "2026-01-03", "2026-01-04"]


def test_mensagem_com_separador_nao_quebra_o_parser(repo):
    """O separador usado no --format não pode ser confundido com texto do commit."""
    commit(repo, "assunto com | pipe e \x1f estranho", "2026-02-01T00:00:00+00:00")
    git(repo, "tag", "v4")
    c = commits_entre(repo, "v3", "v4")
    assert len(c) == 1 and c[0]["message"].startswith("assunto com | pipe")


def test_tag_existe(repo):
    assert tag_existe(repo, "v1")
    assert not tag_existe(repo, "v-inexistente")


def test_referencia_inexistente_levanta_git_error(repo):
    with pytest.raises(GitError):
        commits_entre(repo, "v1", "nao-existe")


def test_clonar_reaproveita_clone_existente(repo, tmp_path):
    """Retomada: o segundo clone não pode rebaixar nem refazer o primeiro."""
    clones = tmp_path / "clones"
    destino = clonar("o/r", str(clones), url=str(repo))
    marcador = tmp_path / "clones" / "o__r.git" / "MARCADOR"
    marcador.write_text("x", encoding="utf-8")
    assert clonar("o/r", str(clones), url=str(repo)) == destino
    assert marcador.exists(), "o clone foi refeito em vez de reaproveitado"


def test_clone_traz_as_tags(repo, tmp_path):
    destino = clonar("o/r", str(tmp_path / "clones"), url=str(repo))
    assert tag_existe(destino, "v2")
    assert [c["message"] for c in commits_entre(destino, "v1", "v2")] == ["c2", "c1"]


def test_clonar_url_invalida_levanta(tmp_path):
    with pytest.raises(GitError):
        clonar("o/r", str(tmp_path / "clones"), url=str(tmp_path / "nao-existe"))
