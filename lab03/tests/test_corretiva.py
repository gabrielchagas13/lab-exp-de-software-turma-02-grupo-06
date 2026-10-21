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


# ---- CFR (b): release falha se seguida em ate 7 dias por uma corretiva ----
from datetime import date  # noqa: E402

from metricas.corretiva import cfr_entrega  # noqa: E402

FIM = date(2026, 12, 31)


def rel(tag, dia, nome=None):
    return {"tag_name": tag, "name": nome,
            "published_at": f"2026-{dia}T00:00:00Z"}


def test_exemplo_do_enunciado():
    """v2.3.0 (10/05) seguida de v2.3.1 (12/05, patch) => v2.3.0 FALHOU.
    v2.4.0 (01/06) seguida de v2.5.0 (20/06) => v2.4.0 NAO falhou."""
    releases = [rel("v2.3.0", "05-10"), rel("v2.3.1", "05-12"),
                rel("v2.4.0", "06-01"), rel("v2.5.0", "06-20")]
    r = cfr_entrega(releases, {}, "v1_semver", FIM)
    # avaliadas: 4; falhou so a v2.3.0 (a v2.3.1 nao e seguida de corretiva)
    assert r["cfr_entrega_avaliadas"] == 4
    assert r["cfr_entrega"] == 0.25


def test_corretiva_fora_da_janela_de_7_dias_nao_conta():
    releases = [rel("v1.0.0", "05-01"), rel("v1.0.1", "05-10")]  # 9 dias depois
    assert cfr_entrega(releases, {}, "v1_semver", FIM)["cfr_entrega"] == 0.0


def test_corretiva_exatamente_em_7_dias_conta():
    releases = [rel("v1.0.0", "05-01"), rel("v1.0.1", "05-08")]
    assert cfr_entrega(releases, {}, "v1_semver", FIM)["cfr_entrega"] == 0.5


def test_releases_dos_ultimos_7_dias_sao_censuradas():
    """Nao da para saber se havera correcao depois do fim da janela."""
    fim = date(2026, 6, 30)
    releases = [rel("v1.0.0", "01-10"), rel("v2.0.0", "06-28")]
    r = cfr_entrega(releases, {}, "v1_semver", fim)
    assert r["cfr_entrega_censuradas"] == 1
    assert r["cfr_entrega_avaliadas"] == 1


def test_sem_releases_avaliaveis_devolve_none():
    fim = date(2026, 6, 30)
    r = cfr_entrega([rel("v1.0.0", "06-29")], {}, "v1_semver", fim)
    assert r["cfr_entrega"] is None and r["cfr_entrega_avaliadas"] == 0


def test_uma_corretiva_resolve_a_falha_sem_contar_duas_vezes():
    """Duas corretivas em 7 dias contam como UMA falha da release original."""
    releases = [rel("v1.0.0", "05-01"), rel("v1.0.1", "05-02"), rel("v1.0.2", "05-03")]
    r = cfr_entrega(releases, {}, "v1_semver", FIM)
    assert r["cfr_entrega_avaliadas"] == 3
    # v1.0.0 falha (seguida de v1.0.1); v1.0.1 falha (seguida de v1.0.2); v1.0.2 nao
    assert r["cfr_entrega"] == pytest.approx(2 / 3)


def test_ordena_por_data_e_nao_pela_ordem_da_lista():
    fora_de_ordem = [rel("v1.0.1", "05-02"), rel("v1.0.0", "05-01")]
    assert cfr_entrega(fora_de_ordem, {}, "v1_semver", FIM)["cfr_entrega"] == 0.5


def test_difere_da_rework_rate():
    """cfr_releases conta releases que SAO corretivas; cfr_entrega conta as que
    foram SEGUIDAS por uma. Sao metricas diferentes e nao podem coincidir aqui."""
    releases = [rel("v1.0.0", "05-01"), rel("v1.0.1", "05-02")]
    rework = cfr_releases(releases, {})["cfr_release_v1_semver"]
    entrega = cfr_entrega(releases, {}, "v1_semver", FIM)["cfr_entrega"]
    assert rework == 0.5 and entrega == 0.5  # valores iguais por acaso aqui
    releases3 = [rel("v1.0.0", "05-01"), rel("v1.0.1", "05-02"), rel("v1.0.2", "05-03")]
    assert cfr_releases(releases3, {})["cfr_release_v1_semver"] == pytest.approx(2 / 3)
    assert cfr_entrega(releases3, {}, "v1_semver", FIM)["cfr_entrega"] == pytest.approx(2 / 3)
