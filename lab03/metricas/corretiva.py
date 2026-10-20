"""Change failure rate, variante (b): proporção de releases corretivas (RQ 03b).

Uma release é *corretiva* quando existe para consertar algo que a anterior
quebrou. Não há campo na API que diga isso, então a classificação é uma
heurística sobre três sinais, cada um com uma fraqueza conhecida:

- `patch`: a versão é semver `X.Y.Z` com `Z > 0` (incremento de patch). Não
  depende da release anterior: `Z > 0` só acontece depois de `X.Y.(Z-1)`.
  Tags em calver (`2026.01.05`, ano >= 1900 no primeiro número) e versões com
  menos de três números não dão sinal. Falha em projetos que publicam
  funcionalidade nova em patch.
- `nome`: a tag ou o título da release contém `fix`, `hotfix`, `bugfix` ou
  `revert` (palavra inteira, sem diferenciar maiúsculas).
- `commits`: pelo menos metade dos commits novos da release (sem contar
  merges) menciona essas palavras na primeira linha da mensagem.

Cada variante combina os sinais de um jeito; todas são avaliadas contra o
consenso da amostra-ouro (`validacao.avaliar_heuristica`) e o resultado de cada
uma fica registrado, inclusive as descartadas. As release notes não entram como
sinal: quase toda release tem uma seção "Bug Fixes", mesmo as de funcionalidade.
"""
import re

PALAVRAS = re.compile(r"\b(hot-?fix(es|ed)?|bug-?fix(es|ed)?|fix(es|ed)?|revert(s|ed)?)\b",
                      re.IGNORECASE)
SEMVER = re.compile(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?!\d)")
LIMIAR_COMMITS = 0.5   # fração mínima de commits corretivos para o sinal `commits`


def eh_patch(tag):
    """True se a tag é semver X.Y.Z com Z > 0; False para calver ou sem versão."""
    m = SEMVER.search(tag or "")
    if not m:
        return False
    major, _, patch = (int(g) for g in m.groups())
    return major < 1900 and patch > 0


def nome_corretivo(tag, nome):
    """True se a tag ou o título da release trazem uma palavra de correção."""
    return bool(PALAVRAS.search(f"{tag or ''} {nome or ''}"))


def _eh_merge(mensagem):
    return mensagem.lstrip().startswith("Merge ")


def fracao_commits_corretivos(mensagens):
    """Fração dos commits (sem merges) com palavra de correção; None se não há commits."""
    validas = [m for m in mensagens if m and not _eh_merge(m)]
    if not validas:
        return None
    return sum(bool(PALAVRAS.search(m.split("\n", 1)[0])) for m in validas) / len(validas)


def sinais(tag, nome, mensagens):
    """Os três sinais da heurística para uma release."""
    fracao = fracao_commits_corretivos(mensagens)
    return {"patch": eh_patch(tag), "nome": nome_corretivo(tag, nome),
            "commits": fracao is not None and fracao >= LIMIAR_COMMITS}


# Variantes avaliadas, na ordem em que foram propostas. Cada uma recebe o dict
# de `sinais` e devolve True (corretiva) ou False.
VARIANTES = {
    "v1_semver": lambda s: s["patch"],
    "v2_semver_ou_nome": lambda s: s["patch"] or s["nome"],
    "v3_commits": lambda s: s["commits"],
    "v4_combinada": lambda s: s["patch"] or s["nome"] or s["commits"],
}


def eh_corretiva(tag, nome, mensagens, variante):
    """Classifica uma release com a variante pedida (chave de `VARIANTES`)."""
    return VARIANTES[variante](sinais(tag, nome, mensagens))


def cfr_releases(releases, commits_por_tag):
    """CFR (b) por variante: releases corretivas / releases avaliadas.

    `releases` são as releases da janela sem pré-release (`tag_name`, `name`);
    `commits_por_tag` é {tag: [mensagens]}. Releases sem commits coletados
    (primeira do histórico, tag apagada) ainda são classificadas pela tag e
    pelo título. Retorna {"cfr_release_<variante>": valor ou None}.
    """
    contagem = dict.fromkeys(VARIANTES, 0)
    for rel in releases:
        s = sinais(rel["tag_name"], rel.get("name"), commits_por_tag.get(rel["tag_name"], []))
        for nome, regra in VARIANTES.items():
            contagem[nome] += bool(regra(s))
    n = len(releases)
    return {f"cfr_release_{v}": (c / n if n else None) for v, c in contagem.items()}
