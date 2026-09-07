# Kata 01 — Semana de maior gasto

Você recebe o histórico de compras de um usuário ao longo de um período de 4 semanas (28 dias, numerados de 0 a 27). Cada compra é um dicionário com `item` (str), `value` (float) e `day` (int, 0-27).

Implemente `weekly_spending(purchases)` que retorna uma tupla `(semana, total)`, onde `semana` é o índice da semana (0 a 3, semana 0 = dias 0-6, semana 1 = dias 7-13, etc.) com o **maior gasto total**, e `total` é o valor somado gasto nessa semana.

Em caso de empate entre semanas, retorne a de **menor índice**.

**Assinatura:**
```python
def weekly_spending(purchases: list[dict]) -> tuple[int, float]:
    ...
```

**Restrições:** não usar bibliotecas externas de data (o cálculo de semana é só `day // 7`).
