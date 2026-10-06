import pytest

from metricas.recuperacao import (censored_ratio, median_recovery_hours,
                                  parse_ts, recovery_episodes)


def mk(hhmm, conclusion, updated=None, wf=1, day="2026-03-10"):
    start = f"{day}T{hhmm}:00Z"
    return {"workflow_id": wf, "conclusion": conclusion, "created_at": start,
            "run_started_at": start,
            "updated_at": f"{day}T{updated}:00Z" if updated else start}


@pytest.fixture
def exemplo_enunciado():
    # Exemplo da seção 5 (RQ 04): recuperação em 1h20
    return [
        mk("09:00", "success"),
        mk("10:00", "failure"),
        mk("10:30", "failure"),
        mk("11:15", "success", updated="11:20"),
    ]


def test_exemplo_do_enunciado_da_1h20(exemplo_enunciado):
    eps = recovery_episodes(exemplo_enunciado)
    assert len(eps) == 1
    assert eps[0].hours == pytest.approx(80 / 60)
    assert not eps[0].censored


def test_ordena_cronologicamente(exemplo_enunciado):
    eps = recovery_episodes(list(reversed(exemplo_enunciado)))
    assert eps[0].hours == pytest.approx(80 / 60)


def test_falha_nunca_recuperada_e_censurada():
    eps = recovery_episodes([mk("09:00", "success"), mk("10:00", "failure")])
    assert len(eps) == 1
    assert eps[0].censored and eps[0].hours is None


def test_cancelled_e_ignorado():
    runs = [mk("09:00", "success"), mk("10:00", "failure"),
            mk("10:30", "cancelled"), mk("11:00", "success", updated="11:10")]
    eps = recovery_episodes(runs)
    assert len(eps) == 1 and eps[0].hours == pytest.approx(70 / 60)


def test_cancelled_nao_encerra_nem_abre_episodio():
    runs = [mk("09:00", "success"), mk("10:00", "cancelled"), mk("11:00", "success")]
    assert recovery_episodes(runs) == []


def test_workflows_sao_independentes():
    runs = [
        mk("09:00", "success", wf=1), mk("09:00", "success", wf=2),
        mk("10:00", "failure", wf=1),
        mk("10:30", "success", updated="10:40", wf=2),  # sucesso de OUTRO workflow
        mk("11:00", "success", updated="12:00", wf=1),
    ]
    eps = recovery_episodes(runs)
    assert len(eps) == 1
    assert eps[0].workflow_id == 1 and eps[0].hours == pytest.approx(2.0)


def test_falha_antes_do_primeiro_sucesso_nao_abre_episodio():
    runs = [mk("08:00", "failure"), mk("09:00", "success")]
    assert recovery_episodes(runs) == []


def test_dois_episodios_no_mesmo_workflow():
    runs = [mk("09:00", "success"), mk("10:00", "failure"), mk("11:00", "success", updated="11:00"),
            mk("12:00", "failure"), mk("14:00", "success", updated="14:00")]
    eps = recovery_episodes(runs)
    assert [e.hours for e in eps] == pytest.approx([1.0, 2.0])


def test_usa_created_at_se_run_started_at_ausente():
    r = mk("10:00", "failure")
    r["run_started_at"] = None
    eps = recovery_episodes([mk("09:00", "success"), r, mk("11:00", "success", updated="11:00")])
    assert eps[0].hours == pytest.approx(1.0)


def test_sem_runs():
    assert recovery_episodes([]) == []
    assert median_recovery_hours([]) is None
    assert censored_ratio([]) is None


def test_mediana_ignora_censurados_e_proporcao():
    runs = [mk("09:00", "success"), mk("10:00", "failure"), mk("11:00", "success", updated="11:00"),
            mk("12:00", "failure"), mk("15:00", "success", updated="15:00"),
            mk("16:00", "failure")]  # censurado
    eps = recovery_episodes(runs)
    assert len(eps) == 3
    assert median_recovery_hours(eps) == pytest.approx(2.0)  # mediana de 1h e 3h
    assert censored_ratio(eps) == pytest.approx(1 / 3)


def test_parse_ts_com_z():
    assert parse_ts("2026-03-10T09:00:00Z").utcoffset().total_seconds() == 0
