"""Tempo de recuperação após falha de CI (RQ 04)."""
from dataclasses import dataclass
from datetime import datetime
from statistics import median

from metricas.cfr import FAILURE, SUCCESS, classify_conclusion


@dataclass(frozen=True)
class Episode:
    workflow_id: object
    started_at: datetime
    hours: float | None  # None quando censurado
    censored: bool


def parse_ts(value):
    """Converte timestamp ISO 8601 da API (`...Z`) em datetime com timezone."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _start(run):
    return parse_ts(run.get("run_started_at") or run["created_at"])


def recovery_episodes(runs):
    """Episódios de falha, calculados dentro de cada workflow.

    Um episódio começa na primeira falha após um sucesso e termina na próxima
    execução bem-sucedida do mesmo workflow. Tempo = `updated_at` do sucesso −
    `run_started_at` da primeira falha. Sem sucesso posterior, o episódio é
    censurado (não descartado). Execuções ignoradas (cancelled etc.) não
    interferem. Falhas anteriores ao primeiro sucesso não abrem episódio.
    """
    by_workflow = {}
    for run in runs:
        if classify_conclusion(run.get("conclusion")) is not None:
            by_workflow.setdefault(run["workflow_id"], []).append(run)

    episodes = []
    for workflow_id, wf_runs in by_workflow.items():
        wf_runs.sort(key=_start)
        seen_success = False
        open_failure = None
        for run in wf_runs:
            kind = classify_conclusion(run["conclusion"])
            if kind == SUCCESS:
                if open_failure is not None:
                    start = _start(open_failure)
                    hours = (parse_ts(run["updated_at"]) - start).total_seconds() / 3600
                    episodes.append(Episode(workflow_id, start, hours, False))
                    open_failure = None
                seen_success = True
            elif kind == FAILURE and seen_success and open_failure is None:
                open_failure = run
        if open_failure is not None:
            episodes.append(Episode(workflow_id, _start(open_failure), None, True))
    return episodes


def median_recovery_hours(episodes):
    """Mediana (horas) dos episódios não censurados; None se não houver."""
    values = [e.hours for e in episodes if not e.censored]
    return median(values) if values else None


def censored_ratio(episodes):
    """Proporção de episódios censurados; None se não há episódios."""
    if not episodes:
        return None
    return sum(e.censored for e in episodes) / len(episodes)
