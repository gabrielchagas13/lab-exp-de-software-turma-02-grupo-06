# Kata 02 — Ranking de tags normalizadas

Um sistema de posts salva tags digitadas livremente pelos usuários, com inconsistências: caixa alta/baixa misturada, espaços extras nas pontas, e separadores repetidos (espaços ou hífens) no meio da tag.

Implemente `normalize_tags(tags)` que:
1. Normaliza cada tag: remove espaços nas pontas, converte para minúsculas, e substitui qualquer sequência de espaços/hífens no meio por um único hífen (`-`).
2. Conta a frequência de cada tag normalizada.
3. Retorna as **top 3** tags mais frequentes, como uma lista de tuplas `(tag, contagem)`, ordenada por contagem decrescente; em caso de empate, ordene alfabeticamente pela tag.

**Assinatura:**
```python
def normalize_tags(tags: list[str]) -> list[tuple[str, int]]:
    ...
```

**Exemplo:** `"  Machine Learning "`, `"machine-learning"` e `"Machine   learning"` devem todas normalizar para `"machine-learning"` e contar como a mesma tag.
