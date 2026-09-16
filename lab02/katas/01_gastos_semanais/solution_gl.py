"""
Kata 01 - Semana de maior gasto. Ver kata.md para o enunciado completo.

Trial: guilherme (GL) | tratamento: IA (Claude) | issue #39
"""


def weekly_spending(purchases: list[dict]) -> tuple[int, float]:
    totals: dict[int, float] = {}
    for purchase in purchases:
        week = purchase["day"] // 7
        totals[week] = totals.get(week, 0.0) + purchase["value"]

    best_week = min(totals, key=lambda week: (-totals[week], week))
    return best_week, totals[best_week]
