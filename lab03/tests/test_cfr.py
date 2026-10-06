import pytest

from metricas.cfr import change_failure_rate_ci, classify_conclusion


def run(conclusion):
    return {"conclusion": conclusion}


@pytest.mark.parametrize("conclusion,expected", [
    ("success", "success"),
    ("failure", "failure"),
    ("timed_out", "failure"),
    ("startup_failure", "failure"),
    ("cancelled", None),
    ("skipped", None),
    ("neutral", None),
    ("action_required", None),
    ("stale", None),
    (None, None),
    ("", None),
])
def test_classify_conclusion(conclusion, expected):
    assert classify_conclusion(conclusion) == expected


def test_cfr_basico():
    runs = [run("success")] * 3 + [run("failure")]
    assert change_failure_rate_ci(runs) == 0.25


def test_cfr_ignora_cancelled_skipped_e_em_andamento():
    runs = [run("success"), run("failure"), run("cancelled"), run("skipped"), run(None)]
    assert change_failure_rate_ci(runs) == 0.5


def test_cfr_conta_timed_out_e_startup_failure_como_falha():
    runs = [run("success"), run("timed_out"), run("startup_failure"), run("success")]
    assert change_failure_rate_ci(runs) == 0.5


def test_cfr_sem_execucoes_validas_retorna_none():
    assert change_failure_rate_ci([]) is None
    assert change_failure_rate_ci([run("cancelled"), run(None)]) is None


def test_cfr_so_falhas_e_so_sucessos():
    assert change_failure_rate_ci([run("failure")]) == 1.0
    assert change_failure_rate_ci([run("success")]) == 0.0
