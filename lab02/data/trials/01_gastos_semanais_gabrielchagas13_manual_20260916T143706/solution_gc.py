"""
Kata 01 - Semana de maior gasto. Ver kata.md para o enunciado completo.

Implemente a funcao abaixo. Nao altere a assinatura.
"""


def weekly_spending(purchases: list[dict]) -> tuple[int, float]:
    totals = [0.0] * 4
    for purchase in purchases:
        totals[purchase["day"] // 7] += purchase["value"]

    week = max(range(4), key=lambda index: totals[index])
    return week, totals[week]
