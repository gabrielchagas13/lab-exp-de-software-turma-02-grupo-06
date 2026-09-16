"""
Kata 04 - Agrupamento de anagramas. Ver kata.md.

Implemente a funcao abaixo. Nao altere a assinatura.
"""


def anagram_clusters(words: list[str]) -> list[list[str]]:
    grupos = {}

    for palavra in words:
        chave = ''.join(sorted(palavra))

        if chave not in grupos:
            grupos[chave] = []

        grupos[chave].append(palavra)

    resultado = [sorted(grupo) for grupo in grupos.values()]       

    resultado.sort(key=lambda grupo: (-len(grupo), grupo[0]))

    return resultado