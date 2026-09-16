"""
Kata 02 - Ranking de tags normalizadas. Ver kata.md para o enunciado completo.

Implemente a funcao abaixo. Nao altere a assinatura.
"""

import re
from collections import Counter


def normalize_tags(tags: list[str]) -> list[tuple[str, int]]:
    normalized = []
    for tag in tags:
        cleaned = tag.strip().lower()
        cleaned = re.sub(r"[\s\-]+", "-", cleaned)
        normalized.append(cleaned)

    counts = Counter(normalized)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:3]
