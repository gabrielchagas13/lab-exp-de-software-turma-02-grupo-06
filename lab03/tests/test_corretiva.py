from datetime import date

import pytest

from metricas.corretiva import (change_failure_rate_release, has_fix_commits, is_corrective,
                                parse_semver, patch_only_bump)


def rel(tag, base, day, msgs=()):
    return {"tag": tag, "base_tag": base, "published_at": f"2026-05-{day:02d}T00:00:00Z",
            "commits": [{"message": m} for m in msgs]}


def test_parse_semver():
    assert parse_semver("v2.3.1") == (2, 3, 1)
    assert parse_semver("pkg-1.0.10") == (1, 0, 10)
    assert parse_semver("nightly") is None
    assert parse_semver(None) is None


def test_patch_only_bump():
    assert patch_only_bump("v2.3.1", "v2.3.0")
    assert not patch_only_bump("v2.4.0", "v2.3.5")
    assert not patch_only_bump("v3.0.1", "v2.0.0")
    assert not patch_only_bump("nightly", "v1.0.0")


def test_has_fix_commits():
    assert has_fix_commits([{"message": "fix: crash ao abrir arquivo"}])
    assert has_fix_commits([{"message": "Revert \"feat\""}])
    assert has_fix_commits([{"message": "hotfix login"}])
    assert not has_fix_commits([{"message": "prefix handling"}, {"message": "feat: x"}])


def test_versoes_da_heuristica():
    so_patch = rel("v1.0.1", "v1.0.0", 2, ["chore: deps"])
    so_fix = rel("v1.1.0", "v1.0.0", 2, ["fix: bug"])
    ambos = rel("v1.0.1", "v1.0.0", 2, ["fix: bug"])
    assert is_corrective(so_patch, "v1") and not is_corrective(so_fix, "v1")
    assert is_corrective(so_patch, "v2") and is_corrective(so_fix, "v2")
    assert not is_corrective(so_patch, "v3") and not is_corrective(so_fix, "v3")
    assert is_corrective(ambos, "v3")
    with pytest.raises(ValueError):
        is_corrective(ambos, "v9")


def test_cfr_entrega_exemplo_da_secao_5():
    # v2.3.0 (10/05) -> v2.3.1 (12/05, fix): v2.3.0 falhou. v2.4.0 (20/05) -> v2.5.0 (28/05): ok.
    releases = [rel("v2.3.0", "v2.2.0", 10), rel("v2.3.1", "v2.3.0", 12, ["fix: crash"]),
                rel("v2.4.0", "v2.3.1", 20), rel("v2.5.0", "v2.4.0", 28)]
    assert change_failure_rate_release(releases, date(2026, 12, 31)) == pytest.approx(1 / 4)


def test_cfr_entrega_corretiva_depois_de_7_dias_nao_conta():
    releases = [rel("v1.0.0", "v0.9.0", 1), rel("v1.0.1", "v1.0.0", 9)]
    assert change_failure_rate_release(releases, date(2026, 12, 31)) == 0


def test_cfr_entrega_censura_ultimos_7_dias():
    releases = [rel("v1.0.0", "v0.9.0", 1), rel("v1.1.0", "v1.0.0", 28)]
    # a de 28/05 fica fora do denominador quando a janela termina em 31/05
    assert change_failure_rate_release(releases, date(2026, 5, 31)) == 0
    assert change_failure_rate_release([rel("v1.1.0", "v1.0.0", 28)], date(2026, 5, 31)) is None


def test_cfr_entrega_sem_releases():
    assert change_failure_rate_release([], date(2026, 5, 31)) is None
