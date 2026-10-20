"""Testes da heurística de release corretiva e do CFR (b) (issue #67)."""
import pytest

from metricas.corretiva import (VARIANTES, cfr_releases, eh_corretiva, eh_patch,
                                fracao_commits_corretivos, nome_corretivo, sinais)


@pytest.mark.parametrize("tag,esperado", [
    ("v1.2.3", True),
    ("1.0.1", True),
    ("release-2.4.10", True),
    ("@scope/pkg@3.1.2", True),
    ("v1.2.3-hotfix", True),
    ("v1.2.0", False),       # minor
    ("v2.0.0", False),       # major
    ("v1.2", False),         # sem número de patch
    ("2026.01.05", False),   # calver: o terceiro número é o dia, não patch
    ("nightly", False),
    ("", False),
    (None, False),
])
def test_eh_patch(tag, esperado):
    assert eh_patch(tag) is esperado


@pytest.mark.parametrize("tag,nome,esperado", [
    ("v1.2.0", "Hotfix release", True),
    ("v1.2.0", "Bugfix for login", True),
    ("v1.2.0", "Revert broken migration", True),
    ("v1.2.0-fix", None, True),
    ("v1.2.0", "Fixes crash on startup", True),
    ("v1.2.0", "New prefix option", False),   # "prefix" contém "fix", mas não é a palavra
    ("v1.2.0", "Feature release", False),
    ("v1.2.0", None, False),
])
def test_nome_corretivo(tag, nome, esperado):
    assert nome_corretivo(tag, nome) is esperado


def test_fracao_ignora_merges():
    msgs = ["fix: a", "feat: b", "Merge pull request #1 from x/y", "Merge branch 'main'"]
    assert fracao_commits_corretivos(msgs) == 0.5


def test_fracao_olha_so_a_primeira_linha():
    assert fracao_commits_corretivos(["feat: b\n\nfixes #12"]) == 0.0


def test_fracao_sem_commits_e_none():
    assert fracao_commits_corretivos([]) is None
    assert fracao_commits_corretivos(["Merge branch 'main'"]) is None


def test_sinal_commits_usa_limiar_de_metade():
    assert sinais("v1.1.0", "", ["fix: a", "feat: b"])["commits"] is True
    assert sinais("v1.1.0", "", ["fix: a", "feat: b", "feat: c"])["commits"] is False
    assert sinais("v1.1.0", "", [])["commits"] is False


@pytest.mark.parametrize("variante,esperado", [
    ("v1_semver", False),
    ("v2_semver_ou_nome", True),
    ("v3_commits", False),
    ("v4_combinada", True),
])
def test_variantes_combinam_sinais(variante, esperado):
    # Só o sinal `nome` está ligado: minor, título com hotfix, commits de feature.
    assert eh_corretiva("v1.3.0", "Hotfix", ["feat: a", "feat: b"], variante) is esperado


def test_cfr_releases_por_variante():
    releases = [{"tag_name": "v1.0.0", "name": "v1.0.0"},
                {"tag_name": "v1.0.1", "name": "v1.0.1"},
                {"tag_name": "v1.1.0", "name": "v1.1.0"},
                {"tag_name": "v1.2.0", "name": "v1.2.0"}]
    commits = {"v1.1.0": ["fix: a", "revert: b", "feat: c"]}
    cfr = cfr_releases(releases, commits)
    assert set(cfr) == {f"cfr_release_{v}" for v in VARIANTES}
    assert cfr["cfr_release_v1_semver"] == 0.25        # v1.0.1
    assert cfr["cfr_release_v3_commits"] == 0.25       # v1.1.0 (2 de 3 commits)
    assert cfr["cfr_release_v4_combinada"] == 0.5      # v1.0.1 e v1.1.0


def test_cfr_releases_sem_releases_e_none():
    assert all(v is None for v in cfr_releases([], {}).values())
