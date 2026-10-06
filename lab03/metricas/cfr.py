"""Change failure rate, variante (a): proxy de CI (RQ 03a)."""

SUCCESS = "success"
FAILURE = "failure"
_FAILURE_CONCLUSIONS = {"failure", "timed_out", "startup_failure"}


def classify_conclusion(conclusion):
    """Classifica o campo `conclusion` de um workflow run.

    Retorna "success", "failure" ou None (ignorar: cancelled, skipped,
    neutral, action_required, stale ou vazio/em andamento).
    """
    if conclusion == "success":
        return SUCCESS
    if conclusion in _FAILURE_CONCLUSIONS:
        return FAILURE
    return None


def change_failure_rate_ci(runs):
    """CFR (a) = falhas / (falhas + sucessos), considerando todos os workflows.

    `runs` é uma lista de dicts com a chave `conclusion`. Retorna None quando
    não há nenhuma execução válida (repositório sem denominador).
    """
    failures = successes = 0
    for run in runs:
        kind = classify_conclusion(run.get("conclusion"))
        if kind == FAILURE:
            failures += 1
        elif kind == SUCCESS:
            successes += 1
    total = failures + successes
    if total == 0:
        return None
    return failures / total
