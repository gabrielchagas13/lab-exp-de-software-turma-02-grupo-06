import pytest

from metricas.lead_time import lead_time_release, lead_times_commits, repo_lead_time


def release(published, *commit_dates):
    return {"published_at": published, "commits": [{"author_date": d} for d in commit_dates]}


# Release publicada em 10/01 12:00; commits 24 h, 48 h e 6 h antes.
EXEMPLO = release("2026-01-10T12:00:00Z",
                  "2026-01-09T12:00:00Z", "2026-01-08T12:00:00Z", "2026-01-10T06:00:00Z")


def test_lead_time_por_commit_b():
    assert lead_times_commits(EXEMPLO) == [24.0, 48.0, 6.0]


def test_lead_time_por_release_a_usa_commit_mais_antigo():
    assert lead_time_release(EXEMPLO) == 48.0


def test_release_sem_commits_novos():
    vazia = release("2026-01-10T12:00:00Z")
    assert lead_times_commits(vazia) == []
    assert lead_time_release(vazia) is None


def test_commit_posterior_a_release_nao_gera_lead_time_negativo():
    r = release("2026-01-10T12:00:00Z", "2026-01-11T12:00:00Z", "2026-01-10T00:00:00Z")
    assert lead_times_commits(r) == [0.0, 12.0]
    assert lead_time_release(r) == 12.0


def test_resumo_do_repositorio_agrupa_commits_e_ignora_releases_vazias():
    segunda = release("2026-02-01T00:00:00Z", "2026-01-31T00:00:00Z")      # (b)=[24]; (a)=24
    vazia = release("2026-03-01T00:00:00Z")
    out = repo_lead_time([EXEMPLO, segunda, vazia])
    assert out["lead_time_release_h"] == pytest.approx(36.0)      # mediana(48, 24)
    assert out["lead_time_commit_h"] == pytest.approx(24.0)       # mediana(24, 48, 6, 24)
    assert out["releases_com_commits"] == 2
    assert out["commits"] == 4


def test_repositorio_com_uma_unica_release_ou_nenhuma_nao_tem_lead_time():
    assert repo_lead_time([]) == {"lead_time_release_h": None, "lead_time_commit_h": None,
                                  "releases_com_commits": 0, "commits": 0}
    assert repo_lead_time([release("2026-01-10T12:00:00Z")])["lead_time_release_h"] is None
