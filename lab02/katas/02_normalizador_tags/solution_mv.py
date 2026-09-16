"""
Kata 02 - Ranking de tags normalizadas. Ver kata.md para o enunciado completo.

Implemente a funcao abaixo. Nao altere a assinatura.
"""
import re

def normalize_tags(tags: list[str]) -> list[tuple[str, int]]:
    frequencias = {}
    for tag in tags:
        tag = tag.strip().lower()
        tag = re.sub(r"[\s-]+", "-", tag)

        frequencias[tag] = frequencias.get(tag, 0) + 1

    ranking = sorted(frequencias.items(), key=lambda item: (-item[1], item[0]))

    return ranking[:3]    

