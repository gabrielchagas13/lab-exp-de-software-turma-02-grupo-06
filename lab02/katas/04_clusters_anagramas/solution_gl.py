"""
Kata 04 - Agrupamento de anagramas. Ver kata.md.

Trial: guilherme (GL) | tratamento: IA (Claude) | issue #42
"""


def anagram_clusters(words: list[str]) -> list[list[str]]:
    groups: dict[str, list[str]] = {}
    for word in words:
        key = "".join(sorted(word))
        groups.setdefault(key, []).append(word)

    clusters = [sorted(group) for group in groups.values()]
    clusters.sort(key=lambda group: (-len(group), group[0]))
    return clusters
