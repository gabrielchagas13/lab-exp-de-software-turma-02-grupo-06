"""Release corretiva (heurística) e change failure rate, variante (b): proxy de entrega (RQ 03b)."""
import re
from datetime import datetime, timedelta, timezone

_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_FIX_RE = re.compile(r"\b(fix(es|ed)?|hotfix|revert(s|ed)?|bugfix)\b", re.IGNORECASE)
FAILURE_WINDOW = timedelta(days=7)

# v1: só o número de patch muda. v2: v1 ou commits de correção. v3: v1 e commits de correção.
VERSIONS = ("v1", "v2", "v3")


def parse_semver(tag):
    """(major, minor, patch) de uma tag como `v2.3.1` ou `pkg-2.3.1`; None se não segue semver."""
    match = _SEMVER_RE.search(tag or "")
    return tuple(int(g) for g in match.groups()) if match else None


def patch_only_bump(tag, base_tag):
    """True se `tag` só incrementa o patch em relação a `base_tag` (`2.3.0 → 2.3.1`)."""
    new, old = parse_semver(tag), parse_semver(base_tag)
    return bool(new and old and new[:2] == old[:2] and new[2] > old[2])


def has_fix_commits(commits):
    """True se algum commit novo menciona fix/hotfix/revert na mensagem."""
    return any(_FIX_RE.search(c.get("message", "")) for c in commits)


def is_corrective(release, version="v2"):
    """Heurística de release corretiva. `release` vem de `commits/` (tag, base_tag, commits)."""
    patch = patch_only_bump(release["tag"], release["base_tag"])
    fixes = has_fix_commits(release["commits"])
    if version == "v1":
        return patch
    if version == "v2":
        return patch or fixes
    if version == "v3":
        return patch and fixes
    raise ValueError(f"versão desconhecida: {version}")


def _parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def change_failure_rate_release(releases, window_end, version="v2"):
    """CFR (b): releases seguidas, em até 7 dias, por uma release corretiva ÷ releases avaliadas.

    `releases` em ordem cronológica, com `published_at`, `tag`, `base_tag` e `commits`.
    Releases dos últimos 7 dias da janela (até `window_end`, inclusive) ficam fora do
    denominador (censura). Retorna None se nenhuma release pôde ser avaliada.
    """
    end = datetime.combine(window_end, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
    cutoff = end - FAILURE_WINDOW
    dates = [_parse(r["published_at"]) for r in releases]
    corrective = [is_corrective(r, version) for r in releases]
    evaluated = failed = 0
    for i, when in enumerate(dates):
        if when > cutoff:
            continue
        evaluated += 1
        if any(corrective[j] and dates[j] - when <= FAILURE_WINDOW
               for j in range(i + 1, len(releases))):
            failed += 1
    return failed / evaluated if evaluated else None
