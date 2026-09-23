"""
Kata 01 - Semana de maior gasto. Ver kata.md para o enunciado completo.

Trial: marcus (MV) | tratamento: IA (Claude) | issue #35
"""


def weekly_spending(purchases: list[dict]) -> tuple[int, float]:
    totals = [0.0] * 4
    for purchase in purchases:
        totals[purchase["day"] // 7] += purchase["value"]

    # max() devolve o primeiro maximo encontrado, entao o empate ja resolve
    # pela semana de menor indice sem precisar de tratamento extra.
    best_week = max(range(4), key=lambda week: totals[week])
    return best_week, totals[best_week]
