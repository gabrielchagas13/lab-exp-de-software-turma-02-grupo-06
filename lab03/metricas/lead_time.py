"""Lead time for changes (RQ 02): do commit à release que o entrega."""
from datetime import datetime
from statistics import median


def _hours(release_at, commit_at):
    """Horas entre o commit e a release; commits com data posterior à release viram 0."""
    parse = lambda v: datetime.fromisoformat(v.replace("Z", "+00:00"))
    return max((parse(release_at) - parse(commit_at)).total_seconds() / 3600, 0.0)


def lead_times_commits(release):
    """Variante (b): lead time (horas) de cada commit novo da release (`author_date`)."""
    return [_hours(release["published_at"], c["author_date"]) for c in release["commits"]]


def lead_time_release(release):
    """Variante (a): release − commit mais antigo que ela entrega; None sem commits novos."""
    return max(lead_times_commits(release), default=None)


def repo_lead_time(releases):
    """Mediana de (a) entre as releases e mediana de (b) sobre todos os commits do repositório."""
    per_release = [v for v in map(lead_time_release, releases) if v is not None]
    per_commit = [v for r in releases for v in lead_times_commits(r)]
    return {"lead_time_release_h": median(per_release) if per_release else None,
            "lead_time_commit_h": median(per_commit) if per_commit else None,
            "releases_com_commits": len(per_release), "commits": len(per_commit)}
